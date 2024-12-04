import requests
from datetime import datetime
import time
from config import (
    OPENSKY_API_BASE,
    OPENSKY_USERNAME,
    OPENSKY_PASSWORD,
    REGION_BOUNDS
)

class OpenSkyClient:
    def __init__(self):
        """Initialize the OpenSky Network API client."""
        if OPENSKY_USERNAME and OPENSKY_PASSWORD:
            print("Using authenticated OpenSky API access")
            self.auth = (OPENSKY_USERNAME, OPENSKY_PASSWORD)
        else:
            print("WARNING: Using anonymous OpenSky API access (rate limited)")
            self.auth = None
        
        self.base_url = OPENSKY_API_BASE
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 10  # seconds between requests for anonymous users
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed the rate limit."""
        if not self.auth:  # Only for anonymous users
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                print(f"Rate limiting: waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_states(self):
        """
        Fetch current state vectors for the specified region.
        Returns a list of flights with their current states.
        """
        self._wait_for_rate_limit()
        
        endpoint = f"{self.base_url}/states/all"
        params = {
            "lamin": REGION_BOUNDS[0],  # min latitude
            "lamax": REGION_BOUNDS[1],  # max latitude
            "lomin": REGION_BOUNDS[2],  # min longitude
            "lomax": REGION_BOUNDS[3]   # max longitude
        }
        
        try:
            print("Fetching flight data from OpenSky Network...")
            response = self.session.get(
                endpoint,
                params=params,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Please wait before trying again.")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            if not data or "states" not in data:
                print("No flight data available in the specified region")
                return []
            
            # Process and format the response
            flights = []
            for state in data["states"]:
                if state[5] and state[6]:  # Check if longitude and latitude are not None
                    flight = {
                        "icao24": state[0],
                        "callsign": state[1].strip() if state[1] else None,
                        "origin_country": state[2],
                        "longitude": float(state[5]),
                        "latitude": float(state[6]),
                        "altitude": float(state[7]) if state[7] else 0,
                        "velocity": float(state[9]) if state[9] else 0,
                        "heading": float(state[10]) if state[10] else 0,
                        "on_ground": bool(state[8]),
                        "timestamp": int(state[4])
                    }
                    flights.append(flight)
            
            print(f"Retrieved {len(flights)} flights")
            return flights
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from OpenSky Network: {e}")
            if hasattr(e.response, 'status_code'):
                print(f"Status code: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def get_flight_details(self, icao24):
        """
        Fetch detailed information for a specific aircraft.
        """
        self._wait_for_rate_limit()
        
        endpoint = f"{self.base_url}/tracks/all"
        params = {"icao24": icao24}
        
        try:
            response = self.session.get(
                endpoint,
                params=params,
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching flight details: {e}")
            return None