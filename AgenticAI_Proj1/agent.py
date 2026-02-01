"""
Agent-based travel planner that uses LangChain to orchestrate tool calls
for weather, air quality, attractions, and recommendations.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from config import OPENAI_API_KEY
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

from datetime import datetime
from dotenv import load_dotenv
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENWEATHER_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  #

# Define tools for the agent
@tool
def get_location_coordinates(city: str) -> dict:
    """Get latitude, longitude, and formatted address for a city using geocoding.
    
    Args:
        city: Name of the city to geocode
        
    Returns:
        Dictionary with lat, lng, and address
    """
    try:
        return geocode_location(city)
    except Exception as e:
        return {"error": str(e), "lat": None, "lng": None, "address": city}


@tool
def get_weather_forecast(lat: float, lng: float) -> dict:
    """Get 3-day weather forecast for a location.
    
    Args:
        lat: Latitude of the location
        lng: Longitude of the location
        
    Returns:
        Dictionary containing weather forecast data
    """
    try:
        if OPENWEATHER_API_KEY:
            owm_daily = get_owm_forecast(lat, lng)
            if owm_daily:
                return {"daily": owm_daily, "source": "OpenWeatherMap"}
        
        # Fallback to Google Weather API
        weather = get_weather(lat, lng)
        daily = three_day_summary(weather)
        return {"daily": daily, "source": "Google Weather", "raw": weather}
    except Exception as e:
        return {"error": str(e), "daily": [{"high": None, "low": None, "precip": 0}] * 3}


@tool
def get_air_quality_data(lat: float, lng: float) -> dict:
    """Get current air quality index (AQI) for a location.
    
    Args:
        lat: Latitude of the location
        lng: Longitude of the location
        
    Returns:
        Dictionary with AQI value and category
    """
    try:
        aqi = None
        
        # Try OpenWeatherMap first if available
        if OPENWEATHER_API_KEY:
            owm_aq = get_owm_air_quality(lat, lng)
            if owm_aq:
                aqi = owm_aq.get("aqi_estimate") or owm_aq.get("owm_index")
                if aqi:
                    return {
                        "aqi": aqi,
                        "category": aqi_category(aqi),
                        "source": "OpenWeatherMap"
                    }
        
        # Fallback to Google Air Quality API
        air = get_air_quality(lat, lng)
        aqi = extract_aqi(air)
        
        if aqi is None:
            return {"aqi": None, "category": "Unknown", "error": "Could not extract AQI from response"}
        
        return {
            "aqi": aqi,
            "category": aqi_category(aqi),
            "source": "Google Air Quality"
        }
    except Exception as e:
        return {"error": str(e), "aqi": None, "category": "Unknown"}


@tool
def get_tourist_attractions(city: str, lat: float, lng: float, radius_km: int = 5) -> list:
    """Get tourist attractions near a location.
    
    Args:
        city: Name of the city
        lat: Latitude of the location
        lng: Longitude of the location
        radius_km: Search radius in kilometers (default 5)
        
    Returns:
        List of attractions with name, address, distance, and type
    """
    try:
        return get_attractions(city, lat, lng, radius_km=radius_km, max_results=5)
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_clothing_advice(temp_celsius: float) -> str:
    """Get clothing recommendation based on temperature.
    
    Args:
        temp_celsius: Temperature in Celsius
        
    Returns:
        Clothing recommendation string
    """
    return clothing_recommendation(temp_celsius)


@tool
def check_umbrella_needed(precipitation_percent: int) -> bool:
    """Check if umbrella is needed based on precipitation probability.
    
    Args:
        precipitation_percent: Precipitation probability as percentage (0-100)
        
    Returns:
        True if umbrella is recommended, False otherwise
    """
    return umbrella_needed(precipitation_percent)


@tool
def check_mask_needed(aqi_value: int) -> bool:
    """Check if face mask is needed based on air quality index.
    
    Args:
        aqi_value: Air Quality Index value
        
    Returns:
        True if mask is recommended (AQI >= 101), False otherwise
    """
    return mask_needed(aqi_value)


# Create the agent
def create_travel_agent():
    """Create and configure the travel planning agent."""
    
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
    
    # Define the tools
    tools = [
        get_location_coordinates,
        get_weather_forecast,
        get_air_quality_data,
        get_tourist_attractions,
        get_clothing_advice,
        check_umbrella_needed,
        check_mask_needed,
    ]
    
    # Create the agent using the new API
    agent_executor = create_agent(
        llm,
        tools=tools,
        system_prompt="""You are a helpful travel planning assistant. You have access to tools to:
- Get location coordinates for cities
- Fetch weather forecasts  
- Check air quality (AQI)
- Find tourist attractions
- Provide clothing recommendations
- Determine if umbrella or mask is needed

When a user asks about a city, you MUST:
1. Get coordinates using get_location_coordinates
2. Get weather using get_weather_forecast
3. Get air quality using get_air_quality_data
4. Get attractions using get_tourist_attractions
5. Calculate average temperature and get clothing advice
6. Check if umbrella is needed based on precipitation
7. Check if mask is needed based on AQI

Always call ALL these tools to provide a complete travel plan. Be thorough and organized in your response.""",
        debug=True
    )
    
    return agent_executor


def run_agent_planner(cities: list):
    """Run the agent-based travel planner for multiple cities.
    
    Args:
        cities: List of city names to plan for
    """
    agent = create_travel_agent()
    
    print("\n" + "=" * 60)
    print("AGENTIC TRAVEL PLANNER")
    print("=" * 60 + "\n")
    
    for city in cities:
        print(f"\n{'=' * 60}")
        print(f"Planning trip to: {city}")
        print(f"{'=' * 60}\n")
        
        query = f"""Please provide a complete travel plan for {city}. 
        
I need:
1. Location coordinates and address
2. 3-day weather forecast with temperatures and precipitation
3. Air quality index (AQI) and its category
4. Top tourist attractions within 5km
5. Clothing recommendations based on the weather
6. Whether I should bring an umbrella
7. Whether I should wear a mask based on air quality

Please use ALL the available tools to gather this information."""
        
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": query}]})
            print("\n" + "-" * 60)
            print("AGENT RESPONSE:")
            print("-" * 60)
            # Get the last message from the agent
            if "messages" in result:
                last_message = result["messages"][-1]
                print(last_message.content if hasattr(last_message, 'content') else str(last_message))
            else:
                print(result)
            print("\n")
        except Exception as e:
            print(f"Error processing {city}: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Planning complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cities = sys.argv[1:]
    else:
        city_input = input("Enter cities separated by commas: ")
        cities = [c.strip() for c in city_input.split(",") if c.strip()]
    
    if not cities:
        print("No cities provided. Using default: Paris")
        cities = ["Paris"]
    
    run_agent_planner(cities)
