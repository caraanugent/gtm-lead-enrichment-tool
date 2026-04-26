import requests

# state codes for API
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
    "WY": "56"}

def find_place_fips(city, state):
    """
    Finds the Census place code for a city within a state.
    """

    state_fips = STATE_FIPS.get(state.upper())

    if not state_fips:
        return None

    url = "https://api.census.gov/data/2024/acs/acs5"

    params = {
        "get": "NAME",
        "for": "place:*",
        "in": f"state:{state_fips}"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            rows = response.json()
            headers = rows[0]
            data_rows = rows[1:]

            for row in data_rows:
                row_data = dict(zip(headers, row))
                place_name = row_data["NAME"].lower()

                if city.lower() in place_name:
                    return row_data["place"]

        return None

    except Exception as e:
        print(f"Census place lookup error for {city}, {state}: {e}")
        return None


def get_market_data(city, state):
    """
    Gets population, median income, and housing vacancy data from Census ACS.

    Variables:
    B01003_001E = total population
    B19013_001E = median household income
    B25001_001E = total housing units
    B25004_001E = vacant housing units
    """

    state_fips = STATE_FIPS.get(state.upper())

    if not state_fips:
        return {}

    place_fips = find_place_fips(city, state)

    if not place_fips:
        return {}

    url = "https://api.census.gov/data/2024/acs/acs5"

    params = {
        "get": "NAME,B01003_001E,B19013_001E,B25001_001E,B25004_001E",
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
            median_income = int(data["B19013_001E"])
            total_housing_units = int(data["B25001_001E"])
            vacant_housing_units = int(data["B25004_001E"])

            vacancy_rate = None
            if total_housing_units > 0:
                vacancy_rate = vacant_housing_units / total_housing_units

            return {
                "place_name": data["NAME"],
                "population": population,
                "median_income": median_income,
                "vacancy_rate": vacancy_rate
            }

        return {}

    except Exception as e:
        print(f"Census market data error for {city}, {state}: {e}")
        return {}


def score_market_quality(city, state):
    """
    Scores market quality out of 35 points:
    - Population: 12 pts
    - Median income: 10 pts
    - Vacancy rate: 13 pts
    Returns: score, insights, data
    """

    score = 0
    insights = []

    data = get_market_data(city, state)

    if not data:
        insights.append(f"Could not find Census market data for {city}, {state}.")
        return score, insights, {}

    population = data.get("population")
    median_income = data.get("median_income")
    vacancy_rate = data.get("vacancy_rate")

    # 1. Population score: max 12
    if population >= 500000:
        score += 12
        insights.append(f"{city} has a large population of about {population:,}.")
    elif population >= 150000:
        score += 7
        insights.append(f"{city} has a solid population base of about {population:,}.")
    elif population >= 50000:
        score += 3
        insights.append(f"{city} has a smaller population of about {population:,}.")
    else:
        insights.append(f"{city} has a relatively small population of about {population:,}.")

    # 2. Median income score: max 10
    if median_income >= 100000:
        score += 10
        insights.append(f"Median household income is strong at about ${median_income:,}.")
    elif median_income >= 70000:
        score += 7
        insights.append(f"Median household income is healthy at about ${median_income:,}.")
    elif median_income >= 50000:
        score += 4
        insights.append(f"Median household income is moderate at about ${median_income:,}.")
    else:
        insights.append(f"Median household income is lower at about ${median_income:,}.")

    # 3. Vacancy rate score: max 13
    if vacancy_rate is not None:
        vacancy_percent = vacancy_rate * 100

        if vacancy_rate <= 0.05:
            score += 13
            insights.append(f"Vacancy rate is low at about {vacancy_percent:.1f}%, suggesting strong demand.")
        elif vacancy_rate <= 0.08:
            score += 8
            insights.append(f"Vacancy rate is moderate at about {vacancy_percent:.1f}%.")
        elif vacancy_rate <= 0.12:
            score += 4
            insights.append(f"Vacancy rate is somewhat elevated at about {vacancy_percent:.1f}%.")
        else:
            insights.append(f"Vacancy rate is high at about {vacancy_percent:.1f}%, suggesting weaker demand.")
    else:
        insights.append("Vacancy rate could not be calculated.")


    return score, insights, data