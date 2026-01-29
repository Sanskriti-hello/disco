from fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PLACES_KEY = ''
DIRECTIONS_KEY = ''
WEATHER_KEY = ''

if not (PLACES_KEY and DIRECTIONS_KEY and WEATHER_KEY):
    raise RuntimeError("Missing required API keys in .env")


import requests

def places_search(query: str):
    # --- Nominatim Search ---
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    resp = requests.get(url, params=params, headers={"User-Agent": "custom-mcp-client"})
    data = resp.json()
    
    out = []
    for r in data:
        lat = float(r["lat"])
        lon = float(r["lon"])

        out.append({
            "name": r.get("display_name"),
            "address": r.get("address"),
            "location": {"lat": lat, "lon": lon},
            "types": [r.get("type"), r.get("class")],
            "osm_id": r.get("osm_id"),
            "osm_type": r.get("osm_type"),
            "map_url": f"https://www.openstreetmap.org/{r.get('osm_type')}/{r.get('osm_id')}"
        })

    # If no results, nothing to query
    if not out:
        return {"query": query, "results": [], "amenities": []}
    
    # --- Overpass Query for Amenities near the FIRST result ---
    lat = out[0]["location"]["lat"]
    lon = out[0]["location"]["lon"]

    # Create bounding box
    radius = 0.005  # ~500m
    south = lat - radius
    west = lon - radius
    north = lat + radius
    east = lon + radius

    # Build Overpass query for restaurants (you can change amenity type)
    amenity_query = f"""
[out:json];
node["amenity"="restaurant"]({south},{west},{north},{east});
out;
"""

    # Execute Overpass
    amenity_resp = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": amenity_query}
    )
    amenity_data = amenity_resp.json()

    return {"query": query, "results": out, "amenities": amenity_data}



def openweather_coordinates(lat: float, lon: float):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": WEATHER_KEY, "units": "metric"}
    resp = requests.get(url, params=params)
    return resp.json()

def geocode_nominatim(place: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }
    resp = requests.get(url, params=params, headers={"User-Agent": "custom-mcp-client"})
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])

def format_osrm_instruction(step):
    maneuver = step.get("maneuver", {})
    mtype    = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")
    name     = step.get("name", "")

    parts = []

    # Map OSRM maneuver types to readable verbs
    type_map = {
        "depart": "Depart",
        "arrive": "Arrive",
        "turn": "Turn",
        "new name": "Continue",
        "continue": "Continue",
        "roundabout": "Enter roundabout",
        "exit roundabout": "Exit roundabout",
        "fork": "Fork",
        "merge": "Merge",
        "ramp": "Take ramp"
    }

    # Get readable type
    verb = type_map.get(mtype, mtype.replace("_", " ").capitalize())
    if verb:
        parts.append(verb)

    # Add modifier (left/right/straight)
    if modifier:
        parts.append(modifier)

    # Add road name
    if name:
        parts.append(f"onto {name}")

    return " ".join(parts).strip()


def google_compute_route(origin: str, destination: str, profile="driving"):
    # Geocode origin
    start = geocode_nominatim(origin)
    if not start:
        return {"error": f"Could not geocode origin '{origin}'"}

    # Geocode destination
    end = geocode_nominatim(destination)
    if not end:
        return {"error": f"Could not geocode destination '{destination}'"}

    lat1, lon1 = start
    lat2, lon2 = end

    # OSRM expects lon,lat
    url = f"https://router.project-osrm.org/route/v1/{profile}/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "overview": "full",
        "steps": "true"
    }
    
    resp = requests.get(url, params=params)
    data = resp.json()

    if "routes" not in data:
        return {"origin": origin, "destination": destination, "routes": []}

    routes = []
    for route in data["routes"]:
        leg = route["legs"][0]
        routes.append({
            "distance": f"{leg['distance']/1000:.2f} km",
            "duration": f"{leg['duration']/60:.1f} min",
            "start": origin,
            "end": destination,
            "steps": [
                {
                    "instruction": format_osrm_instruction(step),
                    "distance": f"{step['distance']} m",
                    "duration": f"{step['duration']:.1f} s"
                }
                for step in leg["steps"]
            ],
            "map_url": f"https://www.openstreetmap.org/directions?engine=osrm_{profile}&route={lat1}%2C{lon1}%3B{lat2}%2C{lon2}"
        })

    return {"origin": origin, "destination": destination, "routes": routes}

mcp = FastMCP("custom-grounding-lite")


@mcp.tool
def search_places(queries: list[str]):
    """Structured search for places."""
    results = [places_search(q) for q in queries]
    return {"queries": queries, "results": results}


@mcp.tool
def lookup_weather(lat: float, lon: float):
    """Structured weather lookup given coordinates."""
    return {
        "lat": lat,
        "lon": lon,
        "weather": openweather_coordinates(lat, lon)
    }


@mcp.tool
def compute_routes(origin: str, destination: str):
    """Compute driving/walking routes between two points."""
    return google_compute_route(origin, destination)


if __name__ == "__main__":
    mcp.run()