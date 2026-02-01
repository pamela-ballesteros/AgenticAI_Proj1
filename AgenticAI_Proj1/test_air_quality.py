"""Test air quality API calls to debug the issue"""
import requests
from config import GOOGLE_MAPS_API_KEY, OPENWEATHER_API_KEY

# Test coordinates for Paris
lat, lng = 48.8566, 2.3522

print("=" * 60)
print("Testing Air Quality APIs")
print("=" * 60)

# Test 1: Google Air Quality API - Current
print("\n1. Testing Google Air Quality (current):")
url1 = "https://airquality.googleapis.com/v1/currentConditions:lookup"
body = {"location": {"latitude": lat, "longitude": lng}}
try:
    response = requests.post(url1, params={"key": GOOGLE_MAPS_API_KEY}, json=body, timeout=10)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    
    # Try to extract AQI
    if "indexes" in data:
        for idx in data["indexes"]:
            if "aqi" in idx:
                print(f"✓ Found AQI: {idx['aqi']} ({idx.get('category', 'N/A')})")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Google Air Quality API - Forecast
print("\n2. Testing Google Air Quality (forecast):")
url2 = "https://airquality.googleapis.com/v1/forecast:lookup"
try:
    response = requests.post(url2, params={"key": GOOGLE_MAPS_API_KEY}, json=body, timeout=10)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Try to extract AQI from hourly forecasts
    if "hourlyForecasts" in data and len(data["hourlyForecasts"]) > 0:
        first_hour = data["hourlyForecasts"][0]
        if "indexes" in first_hour:
            for idx in first_hour["indexes"]:
                if "aqi" in idx:
                    print(f"✓ Found AQI: {idx['aqi']} ({idx.get('category', 'N/A')})")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: OpenWeatherMap Air Quality (if key available)
if OPENWEATHER_API_KEY and OPENWEATHER_API_KEY != "your_openweathermap_api_key_here":
    print("\n3. Testing OpenWeatherMap Air Quality:")
    url3 = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lng, "appid": OPENWEATHER_API_KEY}
    try:
        response = requests.get(url3, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if "list" in data and len(data["list"]) > 0:
            aqi_idx = data["list"][0]["main"]["aqi"]
            print(f"✓ Found OWM AQI Index: {aqi_idx} (1=Good, 5=Very Poor)")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("\n3. OpenWeatherMap: No API key configured")

print("\n" + "=" * 60)
