import os
import json
from dotenv import load_dotenv
from stravalib.client import Client

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

if __name__ == "__main__":
    client = get_strava_client()
    athlete = client.get_athlete()
    print(f"Authenticated as: {athlete.firstname} {athlete.lastname}")
    activity = get_latest_activity(client)
    if activity:
        print(f"Latest activity: {activity.name} on {activity.start_date}")
        route, elevation_gain = extract_route_and_elevation(activity, client)
        print(f"Route has {len(route)} points. Total elevation gain: {elevation_gain} meters.")
