import requests
from typing import Dict, Any

class LocationMCP:
    def __init__(self):
        self.api_key = "" # Mock key

    def get_current_location(self) -> Dict[str, Any]:
        """Get user's current location via IP or other means."""
        print("[LocationMCP] Fetching current location...")
        return {
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "coordinates": [37.7749, -122.4194],
            "ip": "127.0.0.1"
        }

    def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather for coordinates."""
        print(f"[LocationMCP] Fetching weather for {lat}, {lon}")
        # Mock OpenWeatherMap response
        return {
            "temperature": 68,
            "condition": "Partly Cloudy",
            "humidity": 45,
            "wind_speed": 10
        }

location_mcp = LocationMCP()
