from helpers.company_fit import score_company_fit
from helpers.market_quality import score_market_quality
from helpers.city_demand import score_city_demand


def calculate_priority(score):
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MED"
    else:
        return "LOW"


def format_insights(insights):
    return "\n".join([f"- {insight}" for insight in insights])


def generate_outreach_email(name, company, city, population):
    first_name = str(name).split()[0]

    if population and population >= 1_000_000:
        market_line = "a high-volume leasing market"
    elif population and population >= 300_000:
        market_line = "a growing rental market"
    else:
        market_line = "an active rental market"

    return f"""Hi {first_name},

Reaching out because {company} is operating in {city}, which is {market_line}—teams there usually end up buried in inbound leads, tour scheduling, and follow-ups.

We help property management teams take that entire front-end off their plate—responding to every inquiry instantly, scheduling tours automatically, and handling the bulk of resident communication—so onsite teams can focus on closing and operations instead of chasing leads.

If you’re seeing that kind of volume right now, it might be worth comparing notes.

Best,  
Cara"""


def enrich(row):
    name = row["name"]
    company = row["company"]
    city = row["city"]
    state = row["state"]

    total_score = 0
    all_insights = []

    # 1. Company Fit
    company_score, company_insights, company_data = score_company_fit(company)
    total_score += company_score
    all_insights.extend(company_insights)

    # 2. Market Quality
    market_score, market_insights, market_data = score_market_quality(city, state)
    total_score += market_score
    all_insights.extend(market_insights)

    # 3. City Demand
    city_score, city_insights, city_data = score_city_demand(row)
    total_score += city_score
    all_insights.extend(city_insights)

    total_score = min(total_score, 100)

    priority = calculate_priority(total_score)
    sales_insights = format_insights(all_insights)

    population = market_data.get("population") if market_data else None

    outreach_email = generate_outreach_email(
        name=name,
        company=company,
        city=city,
        population=population
    )

    return total_score, sales_insights, outreach_email, priority