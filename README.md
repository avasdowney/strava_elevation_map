# Strava Elevation Map

A Python application that fetches your latest Strava activity and generates an elevation profile map.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Strava API credentials:
```plaintext
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

3. Run the script:
```bash
python strava_auth_test.py
```

On first run, you'll be prompted to authorize the application with your Strava account.

## Features

- OAuth authentication with token persistence
- Fetches latest Strava activity
- Extracts route and elevation data
- Gets ground elevation data from Open-Elevation API
- Coming soon: Elevation map visualization
