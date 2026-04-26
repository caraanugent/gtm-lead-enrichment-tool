# GTM Lead Enrichment Tool

## Overview

This tool automates the inbound lead enrichment process for a sales team.

Given a list of leads (name, company, location), it:

* Enriches each lead using public APIs
* Scores leads based on company fit, market quality, and city demand
* Generates sales insights
* Drafts personalized outreach emails
* Prioritizes leads (HIGH / MED / LOW)

---

## Scoring Framework

**Total: 100 points**

* Company Fit (40)

  * Industry
  * Credibility
  * Growth signals

* Market Quality (35)

  * Population
  * Median income
  * Vacancy rate

* City Demand (25)

  * Walk score
  * Urban density

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Keys

Run the following in your terminal:

```bash
export NEWS_API_KEY=your_key_here
export WALKSCORE_API_KEY=your_key_here
```

---

## Running the Tool

```bash
python main.py
```

This will:

* Process only new leads (`processing_status = "new"`)
* Enrich and score them
* Update the CSV with results

---

## Automation (Daily at 7 AM)

To schedule the script:

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

This installs a cron job that runs the pipeline every morning at 7 AM.

---

## Input Format

The input CSV should include:

* name
* email
* company
* property_address
* city
* state
* country
* processing_status

---

## Output

The input file is updated only with:

- processing_status

Enriched results are saved separately in:

data/lead_output.csv

That file includes:

- name
- email
- company
- property_address
- city
- state
- country
- lead_score
- priority
- sales_insights
- outreach_email

---

## Notes

* Property-level unit data was excluded due to lack of reliable free APIs.
* The tool avoids using low-confidence estimates to maintain scoring integrity.
* Designed as an MVP for scalability and real-world sales workflows.

---

## ⚠️ Environment Variables & Cron

Cron jobs do not automatically inherit environment variables from your terminal.

If API keys are not recognized during scheduled runs, ensure that:

- They are added to your shell configuration (e.g., ~/.zshrc), or
- They are included directly in the cron job

Example:

export NEWS_API_KEY=your_key_here
export WALKSCORE_API_KEY=your_key_here