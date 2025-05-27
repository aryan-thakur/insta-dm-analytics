import pandas as pd
import re

# Load the CSV
df = pd.read_csv("cleaned_file.csv")

# Define ISO 8601 timestamp pattern (no 'T', just space)
iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

# Find rows where timestamp_iso_dt is invalid or NaN
invalid_mask = ~df["timestamp_iso_dt"].astype(str).str.match(iso_pattern)

# Print the invalid rows
print("Invalid timestamp rows:")
print(df[invalid_mask])

# Drop those rows
df_cleaned = df[~invalid_mask].copy()

# Save to new CSV
df_cleaned.to_csv("dm_data_cleaned.csv", index=False)

print(f"\n✅ Cleaned data saved to 'dm_data_cleaned.csv'.")
print(f"Removed {invalid_mask.sum()} rows with invalid timestamps.")
