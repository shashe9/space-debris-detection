import pandas as pd
from skyfield.api import load, EarthSatellite, wgs84
import csv
import os
from datetime import datetime

# === Step 1: Load the starlink metadata from the data directory ===
metadata_path = "../data/starlink_metadata.csv"

# Read the CSV using pandas
df = pd.read_csv(metadata_path)

# For testing purposes, we limit the dataset to the first 100 entries
df = df.head(1000)

# === Step 2: Load Skyfield time system ===
ts = load.timescale()

# === Step 3: Set up output CSV path ===
output_path = "../data/all_satellite_orbits.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# === Step 4: Open CSV writer and start writing output ===
with open(output_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Satellite Name", "Time (UTC)", "Latitude", "Longitude", "Altitude (m)"])

    # === Step 5: Loop through each satellite ===
    for index, row in df.iterrows():
        try:
            # Pull the required orbital parameters
            name = row["OBJECT_NAME"]
            satnum = int(row["NORAD_CAT_ID"])
            classification = row.get("CLASSIFICATION_TYPE", "U")
            int_desig = row["OBJECT_ID"].replace("-", "")
            epoch = pd.to_datetime(row["EPOCH"])
            epoch_year = epoch.year % 100
            epoch_day = (
                epoch.dayofyear +
                epoch.hour / 24 +
                epoch.minute / 1440 +
                epoch.second / 86400
            )
            mm_dot = float(row["MEAN_MOTION_DOT"])
            bstar = float(row["BSTAR"])
            set_number = int(row.get("ELEMENT_SET_NO", 999))
            rev_at_epoch = int(row.get("REV_AT_EPOCH", 0))

            # Construct TLE line 1
            line1 = f"1 {satnum:05d}{classification} {int_desig:<8} {epoch_year:02d}{epoch_day:012.8f} " \
                    f"{mm_dot: .8f} 00000-0 {bstar:.5e} 0 {set_number:04d}"

            # Construct TLE line 2 using orbital elements
            inc = float(row["INCLINATION"])
            raan = float(row["RA_OF_ASC_NODE"])
            ecc = int(float(row["ECCENTRICITY"]) * 1e7)
            argp = float(row["ARG_OF_PERICENTER"])
            mean_anom = float(row["MEAN_ANOMALY"])
            mean_motion = float(row["MEAN_MOTION"])

            line2 = f"2 {satnum:05d} {inc:8.4f} {raan:8.4f} {ecc:07d} {argp:8.4f} {mean_anom:8.4f} {mean_motion:11.8f}{rev_at_epoch:5d}"

            # Create Skyfield satellite object from TLE lines
            sat = EarthSatellite(line1, line2, name, ts)

            # Simulate for 24 hours from epoch, every 10 minutes
            start_time = sat.epoch
            times = [start_time + i / (60 * 24) for i in range(0, 24 * 60, 10)]

            # Extract and write lat/lon/alt data
            for t in times:
                subpoint = wgs84.subpoint(sat.at(t))
                lat = subpoint.latitude.degrees
                lon = subpoint.longitude.degrees
                alt = subpoint.elevation.m  # in meters
                writer.writerow([name, t.utc_iso(), lat, lon, alt])

        except Exception as e:
            print(f"⚠️ Skipping {row['OBJECT_NAME']} due to error: {e}")
            continue

print(f"\nSimulation complete. Output saved to: {output_path}")
