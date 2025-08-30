import pandas as pd
import math
import os
import csv
from datetime import datetime

# === Load data ===
df = pd.read_csv("../data/all_satellite_orbits.csv")

# === Clean columns ===
df["Latitude"] = df["Latitude"].astype(float)
df["Longitude"] = df["Longitude"].astype(float)
df["Altitude (m)"] = df["Altitude (m)"].astype(float)

# === Convert timestamp to datetime ===
df["Time (UTC)"] = pd.to_datetime(df["Time (UTC)"])

# === Sort by satellite name and time ===
df.sort_values(by=["Satellite Name", "Time (UTC)"], inplace=True)

# === Compute velocity vectors using finite differences ===
velocity_dict = {}  # Store { (name, timestamp) : (vx, vy, vz) }

earth_radius = 6371000  # in meters

for sat_name, group in df.groupby("Satellite Name"):
    group = group.sort_values("Time (UTC)").reset_index(drop=True)

    for i in range(1, len(group)):
        prev = group.iloc[i - 1]
        curr = group.iloc[i]

        dt = (curr["Time (UTC)"] - prev["Time (UTC)"]).total_seconds()
        if dt == 0:
            continue

        # Convert lat/lon/alt to ECEF XYZ (in meters)
        def to_xyz(lat, lon, alt):
            lat_rad = math.radians(lat)
            lon_rad = math.radians(lon)
            r = earth_radius + alt
            x = r * math.cos(lat_rad) * math.cos(lon_rad)
            y = r * math.cos(lat_rad) * math.sin(lon_rad)
            z = r * math.sin(lat_rad)
            return x, y, z

        x1, y1, z1 = to_xyz(prev["Latitude"], prev["Longitude"], prev["Altitude (m)"])
        x2, y2, z2 = to_xyz(curr["Latitude"], curr["Longitude"], curr["Altitude (m)"])

        # Velocity = delta position / delta time
        vx = (x2 - x1) / dt
        vy = (y2 - y1) / dt
        vz = (z2 - z1) / dt

        velocity_dict[(sat_name, curr["Time (UTC)"])] = (vx, vy, vz)

# === Prepare output CSV ===
output_csv = "../data/collision_risks_with_velocity.csv"
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Satellite 1", "Satellite 2", "Distance (m)", "Relative Velocity (m/s)"])

    collision_found = False

    # === Group by timestamp ===
    for timestamp, group in df.groupby("Time (UTC)"):
        satellites = group.values.tolist()

        for i in range(len(satellites)):
            s1 = satellites[i]
            name1, lat1, lon1, alt1 = s1[0], s1[2], s1[3], s1[4]

            for j in range(i + 1, len(satellites)):
                s2 = satellites[j]
                name2, lat2, lon2, alt2 = s2[0], s2[2], s2[3], s2[4]

                # Haversine surface distance
                R = earth_radius
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                d_phi = math.radians(lat2 - lat1)
                d_lambda = math.radians(lon2 - lon1)

                a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                surface_dist = R * c

                # Total distance
                alt_diff = abs(alt1 - alt2)
                dist = math.sqrt(surface_dist**2 + alt_diff**2)

                if dist < 5000: #5000 metres which is 5 km------
                    # Get velocities
                    v1 = velocity_dict.get((name1, pd.to_datetime(timestamp)), (0, 0, 0))
                    v2 = velocity_dict.get((name2, pd.to_datetime(timestamp)), (0, 0, 0))

                    # Relative velocity magnitude
                    rel_v = math.sqrt((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2 + (v1[2] - v2[2])**2)

                    collision_found = True
                    print(f"⚠️  Collision risk at {timestamp}")
                    print(f"    Between: {name1} and {name2}")
                    print(f"    Distance: {dist:.2f} meters")
                    print(f"    Relative velocity: {rel_v:.2f} m/s\n")

                    writer.writerow([timestamp, name1, name2, f"{dist:.2f}", f"{rel_v:.2f}"])

    if not collision_found:
        print("✅ No collision risks detected in the simulation period.")
