import pandas as pd
import plotly.express as px
import os

# === Load the collision risk data =======
csv_path = "../data/collision_risks_with_velocity.csv"

if not os.path.exists(csv_path):
    print(f"❌ File not found: {csv_path}")
    print("👉 Please run 'detect_collisions_with_velocity.py' first to generate the data.")
    exit()

# Read the CSV into DataFrame
df = pd.read_csv(csv_path)

# Convert timestamp to datetime for sorting & plotting
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Sort by time
df = df.sort_values("Timestamp")

# Create an interaction label
df["Pair"] = df["Satellite 1"] + " vs " + df["Satellite 2"]

# === Generate Heatmap ===
fig = px.density_heatmap(
    df,
    x="Timestamp",
    y="Pair",
    z="Relative Velocity (m/s)",
    color_continuous_scale="YlOrRd",
    title="Satellite Collision Risk Heatmap (Relative Velocity)",
    labels={"Relative Velocity (m/s)": "Rel. Velocity (m/s)"},
    nbinsx=30,
)

fig.update_layout(
    xaxis_title="Time (UTC)",
    yaxis_title="Satellite Pairs",
    title_x=0.5,
    height=800
)

# Save as HTML for dashboard use later
output_html = "../plots/collision_heatmap.html"
os.makedirs(os.path.dirname(output_html), exist_ok=True)
fig.write_html(output_html)

print(f"✅ Collision heatmap generated and saved to: {output_html}")
