import pandas as pd
import os

# Load the collision risks CSV====
input_csv = "../data/collision_risks.csv"
df = pd.read_csv(input_csv)

# Ensure Timestamp is in datetime format
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Sort by time to detect persistence
df.sort_values("Timestamp", inplace=True)

# Prepare for scoring
risk_rows = []
pair_history = {}

for _, row in df.iterrows():
    timestamp = row["Timestamp"]
    sat1 = row["Satellite 1"]
    sat2 = row["Satellite 2"]
    distance = float(row["Distance (m)"])

    # Create consistent pair key
    pair_key = tuple(sorted((sat1, sat2)))

    # Track consecutive appearances
    last_timestamp, streak = pair_history.get(pair_key, (None, 0))
    
    # Check if current timestamp is within 15 mins of previous (adjustable)
    if last_timestamp and (timestamp - last_timestamp).total_seconds() <= 900:
        streak += 1
    else:
        streak = 1  # reset streak

    pair_history[pair_key] = (timestamp, streak)

    # Calculate risk score (you can tweak this formula)
    risk_score = (1 / (distance + 1)) * (1 + streak)

    # Add to output
    risk_rows.append([
        timestamp, sat1, sat2, distance, streak, round(risk_score, 5)
    ])

# Create DataFrame for saving
output_df = pd.DataFrame(risk_rows, columns=[
    "Timestamp", "Satellite 1", "Satellite 2", "Distance (m)", "Streak", "Risk Score"
])

# Save to persistent_risks.csv
output_file = "../data/persistent_risks.csv"
os.makedirs(os.path.dirname(output_file), exist_ok=True)
output_df.to_csv(output_file, index=False)

print(f"✅ Risk scoring complete. Output saved to {output_file}")


# === Append Position Data from all_satellite_orbits.csv ===

# Load orbit data
orbit_df = pd.read_csv("../data/all_satellite_orbits.csv", parse_dates=["Time (UTC)"])

# Standardize column names
orbit_df.rename(columns={
    "Satellite Name": "Name",
    "Time (UTC)": "Timestamp",
    "Altitude (m)": "Altitude"
}, inplace=True)

# Merge Satellite 1 position
merged = output_df.merge(
    orbit_df[["Name", "Timestamp", "Latitude", "Longitude", "Altitude"]],
    left_on=["Satellite 1", "Timestamp"],
    right_on=["Name", "Timestamp"],
    how="left"
).rename(columns={
    "Latitude": "Lat1",
    "Longitude": "Lon1",
    "Altitude": "Alt1"
}).drop(columns=["Name"])

# Merge Satellite 2 position
merged = merged.merge(
    orbit_df[["Name", "Timestamp", "Latitude", "Longitude", "Altitude"]],
    left_on=["Satellite 2", "Timestamp"],
    right_on=["Name", "Timestamp"],
    how="left"
).rename(columns={
    "Latitude": "Lat2",
    "Longitude": "Lon2",
    "Altitude": "Alt2"
}).drop(columns=["Name"])

# Calculate average position (for plotting)
merged["Latitude"] = (merged["Lat1"] + merged["Lat2"]) / 2
merged["Longitude"] = (merged["Lon1"] + merged["Lon2"]) / 2
merged["Avg Altitude"] = (merged["Alt1"] + merged["Alt2"]) / 2

# Save to enhanced file
merged.to_csv("../data/persistent_risks.csv", index=False)
print("✅ Position-enhanced risk file saved to persistent_risks_with_positions.csv")
