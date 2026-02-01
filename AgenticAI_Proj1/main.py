from tools import (
    geocode_location,
    get_weather,
    get_air_quality,
    get_owm_forecast,
    get_owm_air_quality,
    clothing_recommendation,
    umbrella_needed,
    mask_needed,
    get_attractions,
    three_day_summary,
    aqi_category,
    extract_aqi,
)
from config import OPENWEATHER_API_KEY
from dotenv import load_dotenv
load_dotenv()



from langchain_classic.memory import ConversationBufferMemory

memory = ConversationBufferMemory()


import argparse
import json
import csv
from datetime import datetime, timedelta
import re


def parse_city_token(token):
    """Parse token formats:
    - City
    - City:YYYY-MM-DD
    - City:YYYY-MM-DD:YYYY-MM-DD
    Returns (city, start_date, end_date) where dates are datetime.date or None
    """
    parts = token.split(":")
    city = parts[0].strip()
    start = end = None
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if len(parts) >= 2 and date_re.match(parts[1]):
        start = datetime.strptime(parts[1], "%Y-%m-%d").date()
        end = start
    if len(parts) >= 3 and date_re.match(parts[2]):
        end = datetime.strptime(parts[2], "%Y-%m-%d").date()
    return city, start, end


def mock_city_data(city, start, end):
    """Return mock data for a city (no API calls)."""
    # Simple mock coordinates for a few known cities; fallback to 0,0
    coords = {
        "paris": (48.8566, 2.3522),
        "tokyo": (35.6895, 139.6917),
        "new york": (40.7128, -74.0060),
    }
    lat, lng = coords.get(city.lower(), (0.0, 0.0))
    address = f"{city}, Example Address"
    attractions = [
        {"name": f"{city} Main Museum", "address": f"123 Main St, {city}", "distance_km": 0.6, "type": "museum"},
        {"name": f"{city} Old Town", "address": f"45 Old Town Rd, {city}", "distance_km": 1.0, "type": "historic"},
    ]
    # produce daily entries for date range or 3 days
    days = 3
    if start and end:
        days = (end - start).days + 1
    daily = []
    for i in range(days):
        daily.append({"high": 20 + i, "low": 12 + i, "precip": 10})
    aqi = 40
    return {"lat": lat, "lng": lng, "address": address, "attractions": attractions, "daily": daily, "aqi": aqi}


def export_json(results, out_file):
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def export_csv(results, out_file):
    # flattened CSV: one row per city, lists as JSON strings
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["city", "address", "attractions", "daily", "aqi", "clothing", "notes"])
        for r in results:
            writer.writerow([
                r.get("city"),
                r.get("address"),
                json.dumps(r.get("attractions", []), ensure_ascii=False),
                json.dumps(r.get("daily", []), ensure_ascii=False),
                r.get("aqi"),
                r.get("clothing"),
                "; ".join(r.get("notes", [])),
            ])


def run_trip_planner(tokens, mock=False, export=None, out_file=None):
    print("\nPlanning trip...\n")
    results = []
    total_masks = 0

    for token in tokens:
        city, start, end = parse_city_token(token)
        try:
            if mock:
                data = mock_city_data(city, start, end)
                lat, lng = data["lat"], data["lng"]
                address = data["address"]
                attractions = data["attractions"]
                daily = data["daily"]
                aqi = data["aqi"]
            else:
                geo = geocode_location(city)
                lat, lng = geo["lat"], geo["lng"]
                address = geo.get("address", "")
                attractions = get_attractions(city, lat, lng)

                # Prefer OpenWeatherMap if key available
                if OPENWEATHER_API_KEY:
                    owm_daily = get_owm_forecast(lat, lng)
                    if owm_daily:
                        daily = owm_daily
                    else:
                        weather = get_weather(lat, lng)
                        daily = three_day_summary(weather)

                    owm_aq = get_owm_air_quality(lat, lng)
                    if owm_aq:
                        aqi = owm_aq.get("aqi_estimate") or owm_aq.get("owm_index")
                    else:
                        air = get_air_quality(lat, lng)
                        try:
                            from tools import extract_aqi
                            aqi = extract_aqi(air)
                        except Exception:
                            try:
                                aqi = air["hourlyForecasts"][0]["indexes"][0]["aqi"]
                            except Exception:
                                aqi = air.get("aqi", {}).get("value", None)
                else:
                    weather = get_weather(lat, lng)
                    daily = three_day_summary(weather)
                    air = get_air_quality(lat, lng)
                    try:
                        from tools import extract_aqi
                        aqi = extract_aqi(air)
                    except Exception:
                        try:
                            aqi = air["hourlyForecasts"][0]["indexes"][0]["aqi"]
                        except Exception:
                            aqi = air.get("aqi", {}).get("value", None)

            highs = [d["high"] for d in daily if d.get("high") is not None]
            avg_temp = sum(highs) / len(highs) if highs else None
            if avg_temp is not None:
                clothing = clothing_recommendation(avg_temp)
            else:
                clothing = "N/A (weather data unavailable)"
            umbrella = any(d.get("precip", 0) is not None and d.get("precip", 0) >= 40 for d in daily)
            if avg_temp is None:
                umbrella = False  # can't recommend umbrella without data

            mask = False
            if aqi is not None:
                mask = mask_needed(aqi)
            # If AQI is missing, mask stays False and AQI output is 'N/A'
            if mask:
                total_masks += 1

            # print concise per-city output with clean separators
            print('\n' + '-' * 48)
            print(f"*** {city} ***")
            if address:
                print(f"Address: {address}")
            print('-' * 48)

            print("Top nearby spots (≤2 km):")
            if attractions:
                for p in attractions:
                    name = p.get('name')
                    addr = p.get('address')
                    dist = p.get('distance_km')
                    typ = p.get('type')
                    if addr:
                        print(f"  - {name} — {addr} — {dist} km — {typ}")
                    else:
                        print(f"  - {name} — {dist} km — {typ}")
            else:
                print("  - No attractions found within 2 km.")

            print('-' * 48)

            def fmt_day(i, d):
                h = d.get('high', 'N/A')
                l = d.get('low', 'N/A')
                p = d.get('precip', 0)
                return f"Day {i+1}: {h} / {l} °C, {p}% precip"

            print("Weather (by day):")
            if daily and any(d.get('high') is not None for d in daily):
                print("  " + "; ".join(fmt_day(i, d) for i, d in enumerate(daily)))
            else:
                print("  N/A (weather data unavailable)")
                # Debug: print the raw weather_json for grading/troubleshooting
                if not mock:
                    print("  [DEBUG] Raw weather_json:", weather)

            print('-' * 48)

            print(f"Best wear: {clothing}")

            print('-' * 48)

            if aqi is not None:
                print(f"AQI: {aqi} — {aqi_category(aqi)}")
            else:
                print("AQI: N/A (air quality data unavailable)")

            print('-' * 48)

            notes = ["Public transit recommended", "Best to visit attractions early morning to avoid crowds"]
            if umbrella:
                notes.insert(1, "Bring waterproof or umbrella")
            elif avg_temp is None:
                notes.insert(1, "No umbrella recommendation (weather unavailable)")
            print("Quick notes:")
            for n in notes:
                print(f"  - {n}")

            print('-' * 48)
            print()

            results.append({
                "city": city,
                "address": address,
                "attractions": attractions,
                "daily": daily,
                "aqi": aqi,
                "clothing": clothing,
                "notes": notes,
            })

        except Exception as e:
            print(f"Error processing '{city}': {e}")
            print()
            continue

    print("TOTAL MASKS NEEDED:", total_masks)

    if export and out_file:
        if export == "json":
            export_json(results, out_file)
        elif export == "csv":
            export_csv(results, out_file)
        print(f"Exported results to {out_file}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concise multi-city travel planner")
    parser.add_argument('cities', nargs='*', help='City tokens (e.g., "Paris", "Paris:2026-03-10:2026-03-12")')
    parser.add_argument('--mock', action='store_true', help='Run with mock data (no API calls)')
    parser.add_argument('--export', choices=['json', 'csv'], help='Export results to file')
    parser.add_argument('--out', help='Output filename (default planner_output.json/csv)')
    parser.add_argument('--validate-key', action='store_true', help='Check Google Maps API key and report common issues')

    args = parser.parse_args()

    if args.validate_key:
        try:
            if args.mock:
                print("Running in mock mode — key validation skipped.")
            else:
                geo = geocode_location('Paris')
                print("API key appears valid. Example geocode:\n", geo.get('address'))
        except Exception as e:
            print("API key validation failed:", e)
            print("Check that GOOGLE_MAPS_API_KEY is set, that Geocoding & Places APIs are enabled in your Google Cloud project, billing is enabled, and the key is not restricted incorrectly.")
        raise SystemExit(0)

    if not args.cities:
        inp = input("Enter cities separated by commas or semicolons (or city:YYYY-MM-DD:YYYY-MM-DD):\n> ")
        # Accept both comma and semicolon as delimiters
        import re
        tokens = [c.strip() for c in re.split(r",|;", inp) if c.strip()]
    else:
        tokens = args.cities

    out_file = args.out
    if args.export and not out_file:
        out_file = f"planner_output.{args.export}"

    run_trip_planner(tokens, mock=args.mock, export=args.export, out_file=out_file)
