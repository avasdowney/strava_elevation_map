import os
import json
from dotenv import load_dotenv
from stravalib.client import Client
import requests
import math

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TOKEN_FILE = "strava_token.json"

def _save_token_info(token_info):
    """Callback to save updated token info."""
    print("stravalib requested a token save.")
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_info, f, indent=4)
    print(f"Token information saved to {TOKEN_FILE}")

def get_strava_client():
    """
    Returns a fully authenticated stravalib client.
    Handles token loading, refreshing, and saving.
    """
    token_info = None

    # Check if we have a saved token
    if os.path.exists(TOKEN_FILE):
        print(f"Found token file '{TOKEN_FILE}', loading from it.")
        with open(TOKEN_FILE, "r") as f:
            token_info = json.load(f)

    # If we don't have a token from the file, start the auth flow.
    if not token_info:
        client = Client()
        print("No token file found. Starting one-time authorization flow.")
        if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
            raise ValueError(
                "Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in your .env file."
            )

        auth_url = client.authorization_url(
            client_id=STRAVA_CLIENT_ID,
            redirect_uri="http://localhost",
            scope=["read", "activity:read_all"],
        )

        print("\n--- Please Authorize This Application ---")
        print("1. Go to this URL in your browser:")
        print(f"\n   {auth_url}\n")
        print("2. Authorize the application (you may need to check a box to grant activity access).")
        print("3. You will be redirected to a 'localhost' page. Copy the 'code' from the URL in your browser's address bar.")
        auth_code = input("\n4. Paste the 'code' here and press Enter: ")

        token_info = client.exchange_code_for_token(
            client_id=STRAVA_CLIENT_ID,
            client_secret=STRAVA_CLIENT_SECRET,
            code=auth_code.strip(),
        )

        _save_token_info(token_info)
        print("\nAuthorization successful! Token saved for future use.")

    # Now, create the client using the token info we have (from file or auth)
    client = Client(access_token=token_info['access_token'])
    client.refresh_token = token_info['refresh_token']
    client.token_expires_at = token_info['expires_at']
    client.token_updater = _save_token_info
    return client

def get_latest_activity(client):
    """Fetch the latest activity for the authenticated user."""
    activities = list(client.get_activities(limit=1))
    if not activities:
        print("No activities found.")
        return None
    return activities[0]

def extract_route_and_elevation(activity, client):
    """Extract route (GPS coordinates) and total elevation gain from the activity."""
    # Get the stream data for latlng (route)
    streams = client.get_activity_streams(activity.id, types=['latlng'], resolution='high')
    latlng_stream = streams.get('latlng')
    route = latlng_stream.data if latlng_stream else []
    elevation_gain = activity.total_elevation_gain
    return route, elevation_gain

def get_ground_elevations(route):
    """Fetch ground elevation for each GPS coordinate using the Open-Elevation API."""
    if not route:
        return []
    url = "https://api.open-elevation.com/api/v1/lookup"
    elevations = []
    batch_size = 100
    for i in range(0, len(route), batch_size):
        batch = route[i:i+batch_size]
        locations = [{"latitude": lat, "longitude": lon} for lat, lon in batch]
        response = requests.post(url, json={"locations": locations})
        if response.status_code == 200:
            data = response.json()
            elevations.extend([result["elevation"] for result in data["results"]])
        else:
            print(f"Failed to fetch elevations for batch {i//batch_size+1}")
            elevations.extend([None] * len(batch))
    return elevations

def get_positive_elevation_gain(elevations):
    """
    Calculate the total positive elevation gain from a list of elevations.
    Args:
        elevations (list of float): List of elevation values (meters).
    Returns:
        float: Total positive elevation gain (meters).
    """
    gain = 0.0
    for prev, curr in zip(elevations, elevations[1:]):
        if curr is not None and prev is not None and curr > prev:
            gain += curr - prev
    return gain

def get_route_start_coords(route):
    """Get the starting coordinates of the route."""
    if not route:
        return None
    return route[0]

def save_google_static_map(coords, filename="route_start_map.png", zoom=15, size="600x400", maptype="roadmap"):
    """
    Fetch and save a Google Static Maps image for the given coordinates.
    Args:
        coords (tuple): (latitude, longitude)
        filename (str): Output image filename
        zoom (int): Map zoom level
        size (str): Image size (e.g., '600x400')
        maptype (str): Map type ('roadmap', 'satellite', etc.)
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("GOOGLE_MAPS_API_KEY not set in .env file. Please add your Google Maps API key.")
        return
    lat, lon = coords
    url = (
        f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}"
        f"&zoom={zoom}&size={size}&maptype={maptype}&markers=color:red%7C{lat},{lon}&key={api_key}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Google Static Map image saved as {filename}")
    else:
        print(f"Failed to fetch map image: {response.status_code} {response.text}")

def estimate_mapbox_zoom(lat, map_width_px, ground_width_m):
    """
    Estimate the Mapbox zoom level to fit a given ground width (meters) in the map image.
    Args:
        lat (float): Latitude in degrees
        map_width_px (int): Map image width in pixels
        ground_width_m (float): Desired ground width in meters
    Returns:
        float: Estimated zoom level
    """
    # 156543.03392 = meters per pixel at zoom 0 at equator
    meters_per_pixel = ground_width_m / map_width_px
    zoom = math.log2((156543.03392 * math.cos(math.radians(lat))) / meters_per_pixel)
    return max(0, min(22, zoom))  # Clamp to Mapbox zoom range

def save_mapbox_static_image(coords, filename="route_start_mapbox.png", zoom=15, bearing=0, pitch=60, width=600, height=400, style="mapbox/satellite-streets-v12"):
    """
    Fetch and save a Mapbox Static Image for the given coordinates with 3D terrain and tilt.
    Args:
        coords (tuple): (latitude, longitude)
        filename (str): Output image filename
        zoom (int): Map zoom level
        bearing (int): Map rotation in degrees (0 = north up)
        pitch (int): Tilt angle in degrees (0 = top-down, up to 60)
        width (int): Image width in pixels
        height (int): Image height in pixels
        style (str): Mapbox style (e.g., 'mapbox/satellite-streets-v12')
    """
    access_token = os.getenv("MAPBOX_ACCESS_TOKEN")
    if not access_token:
        print("MAPBOX_ACCESS_TOKEN not set in .env file. Please add your Mapbox access token.")
        return
    lat, lon = coords
    url = (
        f"https://api.mapbox.com/styles/v1/{style}/static/"
        f"pin-l+ff0000({lon},{lat})/"
        f"{lon},{lat},{zoom},{bearing},{pitch}/"
        f"{width}x{height}?access_token={access_token}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Mapbox static image saved as {filename}")
    else:
        print(f"Failed to fetch Mapbox image: {response.status_code} {response.text}")

if __name__ == "__main__":
    client = get_strava_client()
    athlete = client.get_athlete()
    print(f"Authenticated as: {athlete.firstname} {athlete.lastname}")
    activity = get_latest_activity(client)
    if activity:
        print(f"Latest activity: {activity.name} on {activity.start_date}")
        route, elevation_gain = extract_route_and_elevation(activity, client)
        print(f"Route has {len(route)} points. Total elevation gain: {elevation_gain} meters.")
        if route:
            elevations = get_ground_elevations(route)
            positive_gain = get_positive_elevation_gain(elevations)
            print(f"Computed positive elevation gain from ground elevations: {positive_gain:.2f} meters")
            start_coords = get_route_start_coords(route)
            print(f"Route start coordinates: {start_coords}")
            if start_coords:
                # save_google_static_map(start_coords, maptype="satellite")
                lat, lon = start_coords
                map_width_px = 600
                zoom = estimate_mapbox_zoom(lat, map_width_px, max(positive_gain, 100))  # Avoid too small
                save_mapbox_static_image(start_coords, zoom=zoom)
