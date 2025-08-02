# Strava Elevation Map

A Python application that fetches your latest Strava activity and generates an elevation profile map, annotated static map images, and more.

## Prerequisites & Notes
- **Google Static Maps API** only supports 2D top-down images (no tilt or rotation).
- **Mapbox Static Images API** supports tilt (pitch) and bearing for pseudo-3D effect.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file with your API credentials:**
   ```env
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key  # Optional, for Google Maps images
   MAPBOX_ACCESS_TOKEN=your_mapbox_access_token  # Optional, for Mapbox images
   ```
   - Get Strava API credentials from https://www.strava.com/settings/api
   - Get a Google Maps API key from https://console.cloud.google.com/
   - Get a Mapbox access token from https://account.mapbox.com/

3. **Run the script:**
   ```bash
   python strava_auth_test.py
   ```
   - On first run, follow the instructions to authenticate with Strava (copy/paste the code from the browser).
   - The script will fetch your latest activity, generate map images, annotate them, and save them to disk.

4. **Check the output images:**
   - `route_start_mapbox.png`: Mapbox static image with scale and elevation gain
   - `elevation_profile.png`: Side-view elevation profile (if enabled)

## Features

- OAuth authentication with token persistence
- Fetches latest Strava activity
- Extracts route and elevation data
- Gets ground elevation data from Open-Elevation API
- Generates Google and Mapbox static map images (with 3D tilt for Mapbox)
- Annotates Mapbox image with scale and elevation gain
- Generates a side-view elevation profile using matplotlib
- (Optional) Overlay the full route on the map image (coming soon)
