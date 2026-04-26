import os
import requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_wikipedia_data(company):
    """
    Gets company summary from Wikipedia
    """
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + company.replace(" ", "_")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            return {
                "exists": True,
                "summary": data.get("extract", "")
            }

        return {"exists": False, "summary": ""}

    except Exception as e:
        print(f"Wikipedia error for {company}: {e}")
        return {"exists": False, "summary": ""}


def detect_industry(company, summary):
    """
    Infers industry from Wikipedia summary + company name
    """

    real_estate_keywords = [
        "real estate", "property", "realty", "apartments",
        "housing", "multifamily", "residential", "communities", 
        "property group", "management", "development"
    ]

    text = (summary or "").lower()
    name = (company or "").lower()


    if any(keyword in text for keyword in real_estate_keywords) or \
       any(keyword in name for keyword in real_estate_keywords):
        return "real_estate"

    return "other"


def is_expanding(company):
    """
    Uses NewsAPI to check for growth signals
    """
    if not NEWS_API_KEY:
        return False, "NewsAPI key not available."

    url = "https://newsapi.org/v2/everything"

    search_query = (
        f'"{company}" AND '
        f'(expansion OR expanding OR opened OR acquired OR acquisition OR funding OR partnership OR growth)'
    )

    params = {
        "q": search_query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            articles = response.json().get("articles", [])

            if articles:
                headline = articles[0].get("title", "")
                return True, headline

        return False, "No recent expansion-related news found."

    except Exception as e:
        print(f"NewsAPI error for {company}: {e}")
        return False, "Could not check expansion signals."


def score_company_fit(company):
    """
    Scores company fit out of 40 points:
    - Industry: 18 pts
    - Credibility (Wikipedia): 4 pts
    - Growth signals: 8 pts
    (Size omitted due to lack of reliable free APIs)
    """

    score = 0
    insights = []
    data = {}

    wiki_data = get_wikipedia_data(company)

    summary = wiki_data["summary"]
    exists = wiki_data["exists"]

    # 1. Industry (max 18)
    industry = detect_industry(company, summary)

    if industry == "real_estate":
        score += 18
        insights.append(f"{company} appears to operate in real estate (strong fit).")
    else:
        insights.append(f"{company} does not clearly operate in real estate.")

    # 2. Credibility (max 4)
    if exists:
        score += 4
        insights.append(f"{company} has a Wikipedia presence (established company).")
    else:
        insights.append(f"{company} does not have a Wikipedia page.")

    # 3. Growth signals (max 8)
    expanding, headline = is_expanding(company)

    data["expansion_signal"] = expanding
    data["growth_headline"] = headline

    if expanding:
        score += 8
        insights.append(f"Recent growth signal: {headline}")
    else:
        insights.append(headline)

    score = min(score, 40)

    return score, insights, data