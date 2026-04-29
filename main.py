import os
import pandas as pd
from helpers.lead_enrichment import enrich

INPUT_FILE = "data/lead_input.csv"
OUTPUT_FILE = "data/lead_output.csv"

# 1: Read leads file
leads = pd.read_csv(INPUT_FILE)

# 2: Normalize column names
leads.columns = (
    leads.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# 3: Make sure processing_status exists in the input file
if "processing_status" not in leads.columns:
    leads["processing_status"] = "new"

leads["processing_status"] = leads["processing_status"].fillna("new")

# 4: Filter only unprocessed/new leads
new_leads = leads[leads["processing_status"] == "new"]

if new_leads.empty:
    print("No new leads to process.")

else:
    output_rows = []

    # 5: Enrich only new leads
    for index, row in new_leads.iterrows():
        print(f"Processing lead {index}: {row['name']} at {row['company']}")

        try:
            score, insights, outreach_email, priority, rep_approach = enrich(row)

            # Update ONLY processing status in input file
            leads.at[index, "processing_status"] = "processed"

            # Save enriched results separately in output file
            output_rows.append({
                "name": row.get("name", ""),
                "email": row.get("email", ""),
                "company": row.get("company", ""),
                "property_address": row.get("property_address", ""),
                "city": row.get("city", ""),
                "state": row.get("state", ""),
                "country": row.get("country", ""),
                "lead_score": score,
                "priority": priority,
                "sales_insights": insights,
                "rep_approach": rep_approach,
                "outreach_email": outreach_email
            })

            print(f"Done: {row['name']} | Score: {score} | Priority: {priority}\n")

        except Exception as e:
            # If enrichment fails, mark the row as error so it does not silently repeat forever
            leads.at[index, "processing_status"] = "error"
            print(f"Error processing {row.get('name', 'unknown lead')}: {e}\n")

# 6: Save updated input file (only processing_status)
leads.to_csv(INPUT_FILE, index=False)

# 7: Prepare new output rows
output_df = pd.DataFrame(output_rows)

if not output_df.empty:

    # Load existing output if it exists
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        combined_df = pd.concat([existing_df, output_df], ignore_index=True)
    else:
        combined_df = output_df

    # Sort by priority + score
    priority_order = {"HIGH": 3, "MED": 2, "LOW": 1}
    combined_df["priority_rank"] = combined_df["priority"].map(priority_order)

    combined_df = combined_df.sort_values(
        by=["priority_rank", "lead_score"],
        ascending=[False, False]
    )

    combined_df = combined_df.drop(columns=["priority_rank"])

    # Overwrite sorted output
    combined_df.to_csv(OUTPUT_FILE, index=False)

print(f"Finished. Updated processing status in {INPUT_FILE}. Saved sorted leads in {OUTPUT_FILE}.")