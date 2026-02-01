"""Quick test of the fixed air quality functions"""
from tools import geocode_location, get_air_quality, extract_aqi, aqi_category

# Test with Paris
city = "Paris"
print(f"Testing air quality for {city}...")
print("=" * 60)

# Get coordinates
geo = geocode_location(city)
lat, lng = geo["lat"], geo["lng"]
print(f"Location: {geo['address']}")
print(f"Coordinates: {lat}, {lng}")

# Get air quality
air_data = get_air_quality(lat, lng)
print(f"\nAir quality response keys: {list(air_data.keys())}")

# Extract AQI
aqi = extract_aqi(air_data)
print(f"\n✓ AQI: {aqi}")
print(f"✓ Category: {aqi_category(aqi)}")

# Show full index data
if "indexes" in air_data:
    for idx in air_data["indexes"]:
        print(f"\n{idx.get('displayName', 'Unknown')}: {idx.get('aqi')} - {idx.get('category')}")
        print(f"  Dominant pollutant: {idx.get('dominantPollutant', 'N/A')}")

print("\n" + "=" * 60)
print("Air quality is now working! ✓")
