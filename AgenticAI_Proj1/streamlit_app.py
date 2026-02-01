import streamlit as st
import json
import io
import csv
from tools import geocode_location, get_owm_forecast, get_owm_air_quality
from main import run_trip_planner, export_json, export_csv
from config import OPENWEATHER_API_KEY

st.set_page_config(page_title="Concise Travel Planner", layout="wide", page_icon="🧳")

# Sidebar with branding and instructions
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80", use_column_width=True)
    st.markdown("<h2 style='color:#3e2723;'>Travel Planner</h2>", unsafe_allow_html=True)
    st.write("Plan your multi-city trip with weather, air quality, and top attractions.")
    st.write(":round_pushpin: Enter cities (comma-separated). Optionally use `City:YYYY-MM-DD` or `City:YYYY-MM-DD:YYYY-MM-DD` for date ranges.")
    st.info("Tip: For best results, use major North American cities (e.g., Toronto, New York, Miami) to ensure weather data is available from Google.")
    st.markdown("---")
    st.write("Developed by Pamela | Powered by GitHub Copilot")

st.markdown("""
<style>
body {
    background-color: #f4f1ee;
}
.big-title {
    font-size:2.7rem !important;
    font-weight:700;
    color:#3e2723;
    margin-bottom:0.2em;
    letter-spacing: 1px;
}
.section-header {
    font-size:1.25rem !important;
    font-weight:600;
    color:#795548;
    margin-top:1.5em;
    margin-bottom:0.3em;
    letter-spacing: 0.5px;
}
.card {
    background: linear-gradient(135deg, #f4e7d4 0%, #e0d6c3 100%);
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(62,39,35,0.08);
    padding: 2em 2em 1.5em 2em;
    margin-bottom: 2em;
    border: 1.5px solid #bcaaa4;
}
hr {margin-top:1em;margin-bottom:1em;border:0;border-top:1.5px solid #bcaaa4;}
/* Table styling */
.css-1d391kg, .css-1d391kg th, .css-1d391kg td {
    background-color: #f4e7d4 !important;
    color: #3e2723 !important;
    border-color: #bcaaa4 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🌍 Concise Travel Planner</div>', unsafe_allow_html=True)
st.write(":round_pushpin: Enter cities (comma-separated). Optionally use `City:YYYY-MM-DD` or `City:YYYY-MM-DD:YYYY-MM-DD` for date ranges.")
st.info("Tip: For best results, use major North American cities (e.g., Toronto, New York, Miami) to ensure weather data is available from Google.")

# Indicate OpenWeatherMap availability
if OPENWEATHER_API_KEY:
    st.success("OpenWeatherMap: Enabled (will be used for weather & AQI where available)")
else:
    st.info("OpenWeatherMap: Disabled (falls back to Google where available). Add OPENWEATHER_API_KEY to .env to enable")

cities_input = st.text_input("Cities", value="Tokyo")
mock = st.checkbox("Mock mode (no API calls)")

col1, col2, col3 = st.columns(3)
with col1:
    validate = st.button("Validate Google API key")
with col2:
    validate_owm = st.button("Validate OpenWeatherMap key")
with col3:
    run = st.button("Run planner")

if validate:
    if mock:
        st.info("Mock mode: key validation skipped.")
    else:
        try:
            geo = geocode_location("Paris")
            st.success("Google API key appears valid. Example geocode: {}".format(geo.get("address")))
        except Exception as e:
            st.error(f"Google API key validation failed: {e}")
            st.write("Check GOOGLE_MAPS_API_KEY in your .env, ensure Geocoding & Places APIs are enabled and billing is active.")

if validate_owm:
    if mock:
        st.info("Mock mode: OWM validation skipped.")
    else:
        try:
            geo = geocode_location("Paris")
            owm_f = get_owm_forecast(geo.get("lat"), geo.get("lng"))
            owm_a = get_owm_air_quality(geo.get("lat"), geo.get("lng"))
            if owm_f or owm_a:
                st.success("OpenWeatherMap key appears valid and returned data.")
            else:
                st.error("OpenWeatherMap did not return forecast/AQI. Ensure OPENWEATHER_API_KEY is set and valid.")
        except Exception as e:
            st.error(f"OpenWeatherMap validation failed: {e}")

if run:
    tokens = [c.strip() for c in cities_input.split(",") if c.strip()]
    if OPENWEATHER_API_KEY and not mock:
        st.info("Using OpenWeatherMap for weather & AQI where available")
    elif not mock:
        st.info("Using Google (or fallback) for weather & AQI")

    with st.spinner("Planning trip..."):
        try:
            results = run_trip_planner(tokens, mock=mock)
        except Exception as e:
            st.error(f"Planner failed: {e}")
            results = []

    if not results:
        st.warning("No results returned. Check inputs or enable mock mode for a demo.")
    else:
        for r in results:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>🌆 {r.get('city')}</div>", unsafe_allow_html=True)
            addr = r.get("address")
            if addr:
                st.write(f"📍 **Address:** {addr}")
            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>🏛️ Top nearby spots (≤2 km):</div>", unsafe_allow_html=True)
            attractions = r.get("attractions", [])
            if attractions:
                df_rows = []
                for p in attractions:
                    df_rows.append({
                        "Name": p.get("name"),
                        "Address": p.get("address", ""),
                        "Distance (km)": p.get("distance_km"),
                        "Type": p.get("type"),
                    })
                st.table(df_rows)
            else:
                st.write("No attractions found within 2 km.")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>🌦️ Weather (by day):</div>", unsafe_allow_html=True)
            daily = r.get("daily", [])
            if daily and any(d.get('high') is not None for d in daily):
                for i, d in enumerate(daily):
                    st.write(f"Day {i+1}: {d.get('high', 'N/A')} / {d.get('low', 'N/A')} °C, {d.get('precip', 0)}% precip")
            else:
                st.write("N/A (weather data unavailable)")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>🧥 Best wear:</div>", unsafe_allow_html=True)
            st.write(f"{r.get('clothing')}")
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>😷 AQI:</div>", unsafe_allow_html=True)
            st.write(f"{r.get('aqi')}")
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>📝 Quick notes:</div>", unsafe_allow_html=True)
            for n in r.get("notes", []) or []:
                st.write(f"- {n}")
            st.markdown("</div>", unsafe_allow_html=True)

        # Downloads
        st.markdown("---")
        st.markdown("### Export results")
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button("Download JSON", data=json_str, file_name="planner_output.json", mime="application/json")

        # CSV
        csv_io = io.StringIO()
        writer = csv.writer(csv_io)
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
        st.download_button("Download CSV", data=csv_io.getvalue(), file_name="planner_output.csv", mime="text/csv")

    st.success("Done")
