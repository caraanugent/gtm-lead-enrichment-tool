import os
import requests

from helpers.market_quality import find_place_fips

WALKSCORE_API_KEY = os.getenv("WALKSCORE_API_KEY")


STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
    "WY": "56"
}


def geocode_address(address, city, state):
    """
    Converts property address into latitude/longitude using Nominatim.
    """

    full_address = f"{address}, {city}, {state}, USA"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": full_address,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "lead-enrichment-assignment"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])

        return None, None

    except Exception as e:
        print(f"Geocoding error for {full_address}: {e}")
        return None, None


def get_walk_score(address, city, state, lat, lon):
    """
    Gets Walk Score for a property location.
    """

    if not WALKSCORE_API_KEY:
        print("Missing WALKSCORE_API_KEY.")
        return None

    full_address = f"{address}, {city}, {state}"

    url = "https://api.walkscore.com/score"

    params = {
        "format": "json",
        "address": full_address,
        "lat": lat,
        "lon": lon,
        "wsapikey": WALKSCORE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("walkscore")

        return None

    except Exception as e:
        print(f"Walk Score error for {full_address}: {e}")
        return None



def get_urban_density_proxy(city, state):
    """
    Uses population as a proxy for urban density.

    True land-area density was excluded because area is not reliably available
    from the ACS endpoint without extra geospatial processing.
    """

    state_fips = STATE_FIPS.get(state.upper())

    if not state_fips:
        return None

    place_fips = find_place_fips(city, state)

    if not place_fips:
        return None

    url = "https://api.census.gov/data/2024/acs/acs5"

    params = {
        "get": "NAME,B01003_001E",
        "for": f"place:{place_fips}",
        "in": f"state:{state_fips}"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            rows = response.json()
            headers = rows[0]
            values = rows[1]
            data = dict(zip(headers, values))

            population = int(data["B01003_001E"])

            return {
                "population": population,
                "place_name": data["NAME"]
            }

        return None

    except Exception as e:
        print(f"Urban density proxy error for {city}, {state}: {e}")
        return None


def score_city_demand(row):
    """
    Scores city demand out of 25 points:
    - Walk score: 15 pts
    - Urban density: 10 pts
    Returns : score, insights, data
    """

    score = 0
    insights = []

    address = row["property_address"]
    city = row["city"]
    state = row["state"]

    lat, lon = geocode_address(address, city, state)

    if lat is None or lon is None:
        insights.append("Could not geocode property address for Walk Score.")
        walk_score = None
    else:
        walk_score = get_walk_score(address, city, state, lat, lon)

    density_data = get_urban_density_proxy(city, state)

    # 1. Walk Score: max 15
    if walk_score is not None:
        if walk_score >= 90:
            score += 15
            insights.append(f"Walk Score is {walk_score}, considered highly walkable.")
        elif walk_score >= 70:
            score += 13
            insights.append(f"Walk Score is {walk_score}, indicating strong walkability.")
        elif walk_score >= 50:
            score += 8
            insights.append(f"Walk Score is {walk_score}, indicating moderate walkability.")
        else:
            insights.append(f"Walk Score is {walk_score}, indicating low walkability.")
    else:
        insights.append("Walk Score was not available.")

    # 2. Urban density: max 10
    if density_data:
        population = density_data.get("population")

        if population is not None:
            if population >= 1_000_000:
                score += 10
                insights.append(f"{city} has a large population of about {population:,}, which is used as a proxy for strong urban density.")
            elif population >= 300_000:
                score += 7
                insights.append(f"{city} has a solid population of about {population:,}, suggesting a strong urban market.")
            elif population >= 100_000:
                score += 4
                insights.append(f"{city} has about {population:,} residents, suggesting a mid-sized urban market.")
            else:
                insights.append(f"{city} has a smaller population of about {population:,}, suggesting lower urban density.")
        else:
            insights.append("Urban density proxy was not available.")
    else:
        insights.append("Urban density proxy was not available.")

    data = {
        "walk_score": walk_score,
        "density_data": density_data,
        "latitude": lat,
        "longitude": lon
    }

    return score, insights, data