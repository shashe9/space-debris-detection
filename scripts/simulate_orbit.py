#importing modules 
from skyfield.api import load, EarthSatellite, wgs84
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D 
from matplotlib.animation import FuncAnimation


#Load the TLE data
#as of now hardcode the data

#TLE for one satellite (we hardcoded Starlink-1010 TLE data for now)
line1 = "1 44714U 19074B   25195.18782228 -.00000912  00000+0 -42376-4 0  9990"
line2 = "2 44714  53.0544 177.2958 0001195  66.4551 293.6564 15.06388484312979"
name = "STARLINK-1010"

#We now created EarthSatellite object using Skyfield
satellite = EarthSatellite(line1, line2, name)
ts = load.timescale()

#now we will define time window
#we'll take positions every 10 minutes
start_time = ts.now()
minutes_interval = 10
total_minutes = 24 * 60  
times = []

#time list for all timestamps (at every 10 minutes)
for minute in range(0, total_minutes, minutes_interval):
    t = start_time + minute / (60 * 24) 
    times.append(t)



#Now for computing satellite positions (we will create latitudes and longitudes)

latitudes = []
longitudes = []
altitudes = [] 



    


#for each time we will get satellite subpoint
for t in times:
    #we are finding geocentric coordinates here(relative to center of earth)
    geocentric = satellite.at(t)

    #to point the geocentric coordinate with the earth's surface just below 
    subpoint = wgs84.subpoint(geocentric)

    #extracting latitude and longitude from subpoint
    latitude = subpoint.latitude.degrees
    longitude = subpoint.longitude.degrees

    

    # Get (x, y, z) position of satellite in kilometers
    position = geocentric.position.km
    x, y, z = position

    # Earth radius (approximate in km)
    earth_radius_km = 6371.0

    # Distance from Earth's center to satellite
    distance = np.sqrt(x**2 + y**2 + z**2)

    # Altitude above Earth’s surface
    altitude = distance - earth_radius_km


    latitudes.append(latitude)
    longitudes.append(longitude)
    altitudes.append(altitude)


#Data Storage and File Handling through csv file
output_csv = "../data/satellite_orbit_track.csv"


with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    #header row
    writer.writerow(["Time (UTC)", "Latitude", "Longitude", "Altitude (km)"]) 

    
    for i in range(len(times)):
        #to convert the time to a UTC timestamp in ISO 8601 format, like:
        #'2025-07-15T18:30:00Z'
        #Z at the end means “Zulu time,” which is just another name for UTC.

        time_string = times[i].utc_iso() 
        writer.writerow([time_string, latitudes[i], longitudes[i],altitudes[i]])


#Plotting the lat long
plt.figure(figsize=(12, 6))

# Plot the orbit path as a scatter plot
plt.plot(longitudes, latitudes, marker='o', linestyle='-', color='blue', markersize=3)

# Set axis labels and title
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title(f"Ground Track of {name}")

# Set axis limits
plt.xlim(-180, 180)
plt.ylim(-90, 90)

# Add a grid for better readability
plt.grid(True)

# Save the plot to PNG file
plot_path = "../plots/orbit_track.png"
plt.savefig(plot_path)

# Show the plot (you can disable this on headless systems)
plt.show()

print("Orbit simulation completed.")
print(f"CSV saved to: {output_csv}")
print(f"Plot saved to: {plot_path}")


# Plot Altitude vs Time
plt.figure(figsize=(10, 5))
plt.plot([t.utc_datetime() for t in times], altitudes, color='green', linewidth=2)

plt.xlabel("Time (UTC)")
plt.ylabel("Altitude (km)")
plt.title(f"Altitude vs Time for {name}")
plt.grid(True)

# Save plot
altitude_plot_path = "../plots/altitude_vs_time.png"
plt.savefig(altitude_plot_path)
plt.show()

print(f"Altitude plot saved to: {altitude_plot_path}")


# 3D Plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Plotting longitude, latitude, and altitude
ax.plot(longitudes, latitudes, altitudes, color='purple', marker='o', markersize=2, linestyle='-')

ax.set_xlabel('Longitude (°)')
ax.set_ylabel('Latitude (°)')
ax.set_zlabel('Altitude (km)')
ax.set_title(f"3D Orbit Track of {name}")

# Optional: Set axis limits
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)

# Save the figure
plot_3d_path = "../plots/3d_orbit.png"
plt.savefig(plot_3d_path)
plt.show()

print(f"3D orbit plot saved to: {plot_3d_path}")

# Convert longitudes, latitudes, and altitudes to 3D Cartesian coordinates
x_vals = []
y_vals = []
z_vals = []

for i in range(len(latitudes)):
    # Convert degrees to radians
    lat_rad = np.radians(latitudes[i])
    lon_rad = np.radians(longitudes[i])
    r = altitudes[i] + earth_radius_km

    # Spherical to Cartesian conversion
    x = r * np.cos(lat_rad) * np.cos(lon_rad)
    y = r * np.cos(lat_rad) * np.sin(lon_rad)
    z = r * np.sin(lat_rad)

    x_vals.append(x)
    y_vals.append(y)
    z_vals.append(z)

# Setup figure
plt.style.use('dark_background')

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_title(f"3D Orbit Animation of {name}")

# Earth sphere
u, v = np.mgrid[0:2*np.pi:100j, 0:np.pi:50j]
earth_x = earth_radius_km * np.cos(u) * np.sin(v)
earth_y = earth_radius_km * np.sin(u) * np.sin(v)
earth_z = earth_radius_km * np.cos(v)
ax.plot_surface(earth_x, earth_y, earth_z, rstride=4, cstride=4, color='midnightblue', edgecolor='gray', linewidth=0.3, alpha=1.0)


# Axis limits and labels
limit = max(x_vals + y_vals + z_vals, key=abs)
ax.set_xlim([-limit, limit])
ax.set_ylim([-limit, limit])
ax.set_zlim([-limit, limit])
ax.set_xlabel("X (km)")
ax.set_ylabel("Y (km)")
ax.set_zlabel("Z (km)")


# Initial satellite point and trail line
satellite_dot, = ax.plot([], [], [], 'ro', markersize=4, label='Satellite')
trail_line, = ax.plot([], [], [], color='red', linewidth=1, label='Trail')

def update(frame):
    # Update the satellite dot
    satellite_dot.set_data([x_vals[frame]], [y_vals[frame]])
    satellite_dot.set_3d_properties([z_vals[frame]])
    
    # Update the trail (path so far)
    trail_line.set_data(x_vals[:frame+1], y_vals[:frame+1])
    trail_line.set_3d_properties(z_vals[:frame+1])
    
    return satellite_dot, trail_line



# Animate!
ani = FuncAnimation(fig, update, frames=len(x_vals), interval=100, blit=True)


# Show animation
plt.show()

print("3D animation complete.")
