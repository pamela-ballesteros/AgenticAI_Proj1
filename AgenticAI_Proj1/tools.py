def aqi_category(aqi):
    """Return AQI category string for a given AQI value (US EPA standard)."""
    if aqi is None:
        return "Unknown"
    try:
        aqi = float(aqi)
    except Exception:
        return "Unknown"
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"
import requests
import math
from config import GOOGLE_MAPS_API_KEY, OPENWEATHER_API_KEY


def geocode_location(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError(f"Geocoding request failed (status code {response.status_code})")
    data = response.json()

    status = data.get("status")
    if status != "OK" or not data.get("results"):
        err_msg = data.get("error_message") or "No results"
        raise ValueError(f"No geocoding results for '{address}' (status: {status}) - {err_msg}")

    location = data["results"][0]["geometry"]["location"]
    formatted_address = data["results"][0].get("formatted_address", address)

    return {"lat": location["lat"], "lng": location["lng"], "address": formatted_address}


def get_weather(lat, lng):
    url = "https://weather.googleapis.com/v1/currentConditions:lookup"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "location.latitude": lat,
        "location.longitude": lng
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception:
        data = {}

    # If the response lacks useful fields, try POSTing a JSON body as a fallback
    if not any(k in data for k in ("dailyForecasts", "daily", "temperature", "currentConditions")):
        try:
            body = {"location": {"latitude": lat, "longitude": lng}}
            response = requests.post(url, params={"key": GOOGLE_MAPS_API_KEY}, json=body, timeout=10)
            data = response.json()
        except Exception:
            pass

    return data


def get_air_quality(lat, lng):
    """Get current air quality using Google Air Quality API."""
    url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
    body = {"location": {"latitude": lat, "longitude": lng}}
    try:
        response = requests.post(url, params={"key": GOOGLE_MAPS_API_KEY}, json=body, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes
        data = response.json()
    except Exception as e:
        print(f"Air quality API error: {e}")
        data = {}
    return data


def extract_aqi(air_json):
    """Try multiple patterns to extract a numeric AQI from Air Quality responses."""
    if not air_json:
        return None
    
    # Priority 1: Current conditions with top-level indexes (Google Air Quality API v1)
    try:
        if "indexes" in air_json and len(air_json["indexes"]) > 0:
            # Find UAQI (Universal AQI) index
            for idx in air_json["indexes"]:
                if idx.get("code") == "uaqi" and "aqi" in idx:
                    return idx["aqi"]
            # Fallback to first index
            return air_json["indexes"][0].get("aqi")
    except Exception:
        pass
    
    # Priority 2: Hourly forecast format
    try:
        return air_json["hourlyForecasts"][0]["indexes"][0]["aqi"]
    except Exception:
        pass
    # check common list keys
    for key in ("data", "forecasts", "results", "hourly"):
        if key in air_json and isinstance(air_json[key], list) and air_json[key]:
            item = air_json[key][0]
            for subk in ("aqi", "AQI", "value"):
                if subk in item:
                    return item[subk]
    # nested search
    def find_aqi(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == "aqi" and isinstance(v, (int, float)):
                    return v
                res = find_aqi(v)
                if res is not None:
                    return res
        elif isinstance(obj, list):
            for it in obj:
                res = find_aqi(it)
                if res is not None:
                    return res
        return None

    return find_aqi(air_json)


def clothing_recommendation(temp_c):
    if temp_c < 5:
        return "Heavy winter jacket, gloves, scarf"
    elif temp_c < 15:
        return "Light coat or sweater"
    elif temp_c < 25:
        return "Long sleeve shirt or light layers"
    else:
        return "Shorts, t-shirt, breathable clothing"


def umbrella_needed(precip_percent):
    return precip_percent >= 40


def mask_needed(aqi):
    return aqi >= 101


def haversine(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lon pairs."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_attractions(city, lat, lng, radius_km=2, max_results=5):
    """Use Google Places Text Search to find tourist attractions in a city and return those within radius_km of (lat,lng)."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": f"tourist attractions in {city}", "key": GOOGLE_MAPS_API_KEY}
    response = requests.get(url, params=params)
    data = response.json()

    results = data.get("results", [])
    places = []
    for r in results:
        loc = r.get("geometry", {}).get("location")
        if not loc:
            continue
        d = haversine(lat, lng, loc.get("lat"), loc.get("lng"))
        place_type = r.get("types", [])
        type_label = place_type[0] if place_type else "attraction"
        addr = r.get("formatted_address") or r.get("vicinity") or ""
        places.append({
            "name": r.get("name"),
            "address": addr,
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "distance_km": round(d, 2),
            "type": type_label,
        })

    # keep only those within radius_km and sort by distance
    filtered = [p for p in places if p["distance_km"] <= radius_km]
    filtered.sort(key=lambda x: x["distance_km"]) 
    # if none found within radius, return the closest up to max_results
    if not filtered:
        places.sort(key=lambda x: x["distance_km"])
        return places[:max_results]

    return filtered[:max_results]


def three_day_summary(weather_json):
    """Return a list of three dicts: [{'high':, 'low':, 'precip':}, ...] using available data or fallback to current."""
    daily = []
    # Several APIs use different keys; try common patterns
    if not weather_json:
        return [{"high": None, "low": None, "precip": 0}] * 3

    if "dailyForecasts" in weather_json:
        for d in weather_json.get("dailyForecasts", [])[:3]:
            high = d.get("maxTemp", {}).get("degrees") or d.get("temperature", {}).get("high")
            low = d.get("minTemp", {}).get("degrees") or d.get("temperature", {}).get("low")
            precip = d.get("precipitation", {}).get("probability", {}).get("percent", 0) if d.get("precipitation") else 0
            daily.append({"high": high, "low": low, "precip": precip})
    elif "daily" in weather_json:
        for d in weather_json.get("daily", [])[:3]:
            high = d.get("temp", {}).get("max")
            low = d.get("temp", {}).get("min")
            precip = int(d.get("pop", 0) * 100)
            daily.append({"high": high, "low": low, "precip": precip})
    else:
        # fallback: repeat current/observation 3 times
        temp = weather_json.get("temperature", {}).get("degrees")
        precip = weather_json.get("precipitation", {}).get("probability", {}).get("percent", 0)
        for _ in range(3):
            daily.append({"high": temp, "low": temp, "precip": precip})

    # ensure list is length 3
    while len(daily) < 3:
        daily.append({"high": None, "low": None, "precip": 0})

    return daily


# OpenWeatherMap helpers (optional, used when OPENWEATHER_API_KEY is set)
def get_owm_forecast(lat, lng, days=3):
    """Return a list of day dicts using OpenWeatherMap One Call API (metric units)."""
    if not OPENWEATHER_API_KEY:
        return None
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {"lat": lat, "lon": lng, "exclude": "current,minutely,hourly,alerts", "units": "metric", "appid": OPENWEATHER_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
    except Exception:
        return None

    res = []
    for d in data.get("daily", [])[:days]:
        high = d.get("temp", {}).get("max")
        low = d.get("temp", {}).get("min")
        pop = int(d.get("pop", 0) * 100)
        res.append({"high": high, "low": low, "precip": pop})

    if not res:
        return None
    return res


def get_owm_air_quality(lat, lng):
    """Return a dict with OWM AQI index and a category/estimate."""
    if not OPENWEATHER_API_KEY:
        return None
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lng, "appid": OPENWEATHER_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
    except Exception:
        return None

    try:
        idx = data["list"][0]["main"]["aqi"]  # 1..5
    except Exception:
        return None

    mapping = {
        1: ("Good", 40),
        2: ("Fair", 75),
        3: ("Moderate", 125),
        4: ("Poor", 175),
        5: ("Very Poor", 250),
    }
    cat, est = mapping.get(idx, ("Unknown", None))
    return {"owm_index": idx, "category": cat, "aqi_estimate": est}

