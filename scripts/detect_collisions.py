# import pandas as pd
# import math

# # === Load the full orbit data ===
# df = pd.read_csv("../data/all_satellite_orbits.csv")

# # === Clean and convert columns ===
# df["Latitude"] = df["Latitude"].astype(float)
# df["Longitude"] = df["Longitude"].astype(float)
# df["Altitude (m)"] = df["Altitude (m)"].astype(float)

# collision_found = False  # Flag to track if any collision risk is detected

# # === Group data by timestamp (all satellites at that time) ===
# for timestamp, group in df.groupby("Time (UTC)"):
#     satellites = group.values.tolist()  # Each row: [Name, time, Lat, Lon, Alt]

#     for i in range(len(satellites)):
#         sat1 = satellites[i]
#         name1, lat1, lon1, alt1 = sat1[0], sat1[2], sat1[3], sat1[4]

#         for j in range(i + 1, len(satellites)):
#             sat2 = satellites[j]
#             name2, lat2, lon2, alt2 = sat2[0], sat2[2], sat2[3], sat2[4]

#             # === Approximate 3D distance in meters ===
#             dist_m = math.sqrt(
#                 (lat1 - lat2)**2 +
#                 (lon1 - lon2)**2 +
#                 ((alt1 - alt2)/111000)**2  # Scale altitude diff to degrees approx.
#             ) * 111000  # Convert to meters

#             # === Check for close approach ===
#             if dist_m < 500:  # less than 500 m
#                 collision_found = True
#                 print(f"    Collision risk at {timestamp}")
#                 print(f"    Between: {name1} and {name2}")
#                 print(f"    Distance: {dist_m:.2f} meters\n")

# if not collision_found:
#     print("   No collision risks detected in the simulation period.")


import pandas as pd
import math
import os
import csv

# === Load satellite data ===
df = pd.read_csv("../data/all_satellite_orbits.csv")

# === Clean and convert columns ===
df["Latitude"] = df["Latitude"].astype(float)
df["Longitude"] = df["Longitude"].astype(float)
df["Altitude (m)"] = df["Altitude (m)"].astype(float)

# === Prepare output CSV ===
output_csv = "../data/collision_risks.csv"
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

# Overwrite existing file and write headers
with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Satellite 1", "Satellite 2", "Distance (m)"])

    collision_found = False

    # === Group data by timestamp ===
    for timestamp, group in df.groupby("Time (UTC)"):
        satellites = group.values.tolist()

        for i in range(len(satellites)):
            sat1 = satellites[i]
            name1, lat1, lon1, alt1 = sat1[0], sat1[2], sat1[3], sat1[4]

            for j in range(i + 1, len(satellites)):
                sat2 = satellites[j]
                name2, lat2, lon2, alt2 = sat2[0], sat2[2], sat2[3], sat2[4]

                # === Compute surface (lat/lon) distance using Haversine ===
                R = 6371000  # Earth radius in meters
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                delta_phi = math.radians(lat2 - lat1)
                delta_lambda = math.radians(lon2 - lon1)

                a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                surface_dist = R * c

                # === Add altitude difference ===
                alt_diff = abs(alt1 - alt2)
                total_dist = math.sqrt(surface_dist**2 + alt_diff**2)

                # === Threshold for collision risk (e.g., < 5000 m) =======
                if total_dist < 5000:
                    collision_found = True
                    print(f"   Collision risk at {timestamp}")
                    print(f"    Between: {name1} and {name2}")
                    print(f"    Distance: {total_dist:.2f} meters\n")
                    writer.writerow([timestamp, name1, name2, f"{total_dist:.2f}"])

    if not collision_found:
        print("  No collision risks detected in the simulation period.")
