"""Main execution entrypoint for Weather Intelligence Apify Actor."""

import asyncio
import os
from typing import Dict, Any, List
from apify import Actor

from src.openmeteo_client import OpenMeteoClient, decode_weather_code
from src.disasters_client import DisastersClient
from src.marine_space_client import MarineSpaceClient
from src.tectonic_data import identify_tectonic_plate

async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        locations: List[str] = actor_input.get("locations", ["Casablanca", "Paris", "Tokyo"])
        forecast_days: int = int(actor_input.get("forecastDays", 7))
        include_aqi: bool = bool(actor_input.get("includeAirQuality", True))
        include_marine: bool = bool(actor_input.get("includeMarineWeather", True))
        include_space: bool = bool(actor_input.get("includeSpaceWeather", True))
        include_quakes: bool = bool(actor_input.get("includeEarthquakes", True))
        api_key: str = actor_input.get("apiKey") or os.getenv("APIFY_TOKEN") or os.getenv("API_KEY", "")

        client = OpenMeteoClient()
        marine_client = MarineSpaceClient()
        disasters_client = DisastersClient()

        Actor.log.info(f"Starting Weather Intelligence extraction for {len(locations)} locations...")
        if api_key:
            Actor.log.info("API Key / Token authentication provided.")

        # Global Space Weather & Earthquakes if requested
        space_weather_data = {}
        if include_space:
            try:
                space_weather_data = marine_client.fetch_space_weather()
                Actor.log.info("Fetched global space weather and geomagnetic telemetry.")
            except Exception as e:
                Actor.log.warning(f"Error fetching space weather: {e}")

        recent_earthquakes = []
        if include_quakes:
            try:
                quakes_df = disasters_client.fetch_recent_earthquakes(min_magnitude=4.5)
                recent_earthquakes = quakes_df.to_dict(orient="records") if not quakes_df.empty else []
                Actor.log.info(f"Fetched {len(recent_earthquakes)} recent global earthquakes.")
            except Exception as e:
                Actor.log.warning(f"Error fetching earthquakes: {e}")

        all_results = []

        # Process each location
        for loc_name in locations:
            Actor.log.info(f"Geocoding and processing location: {loc_name}...")
            search_results = client.search_location(loc_name)
            if not search_results:
                Actor.log.warning(f"Could not geocode location '{loc_name}'. Skipping.")
                continue

            best_loc = search_results[0]
            lat = best_loc["latitude"]
            lon = best_loc["longitude"]
            tz = best_loc.get("timezone", "auto")
            country = best_loc.get("country", "")

            # Crustal Tectonic Plate
            tectonic_plate = identify_tectonic_plate(lat, lon)

            # Forecast
            forecast = client.fetch_forecast(lat, lon, timezone_str=tz, forecast_days=forecast_days)
            current_weather = forecast.get("current", {})
            daily_df = forecast.get("daily_df")
            daily_forecast = daily_df.to_dict(orient="records") if daily_df is not None and not daily_df.empty else []

            # Air Quality
            air_quality = {}
            if include_aqi:
                try:
                    aqi_data = client.fetch_air_quality(lat, lon, timezone_str=tz)
                    air_quality = aqi_data.get("current", {})
                except Exception as e:
                    Actor.log.warning(f"Failed to fetch AQI for {loc_name}: {e}")

            # Marine Weather
            marine_data = {}
            if include_marine:
                try:
                    m_res = marine_client.fetch_marine_weather(lat, lon, timezone_str=tz)
                    marine_data = m_res.get("current", {})
                except Exception as e:
                    Actor.log.warning(f"Failed to fetch Marine data for {loc_name}: {e}")

            result_item = {
                "query": loc_name,
                "resolvedName": best_loc.get("display_name", loc_name),
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
                "tectonicPlate": tectonic_plate,
                "currentWeather": current_weather,
                "airQuality": air_quality,
                "marineWeather": marine_data,
                "spaceWeather": space_weather_data,
                "dailyForecast": daily_forecast,
                "recentMajorEarthquakes": recent_earthquakes[:5]
            }

            await Actor.push_data(result_item)
            all_results.append(result_item)
            Actor.log.info(f"Pushed weather record for {loc_name} to dataset.")

        # Save executive summary to Key-Value store for MCP tools & instant API payloads
        summary_payload = {
            "totalLocationsAnalyzed": len(all_results),
            "locations": [r["resolvedName"] for r in all_results],
            "spaceWeatherSummary": {
                "solarFlareFlux": space_weather_data.get("flux_level", "Quiet"),
                "kpIndex": space_weather_data.get("kp_index", 2)
            },
            "recentEarthquakesCount": len(recent_earthquakes),
            "weatherHighlights": [
                {
                    "location": r["resolvedName"],
                    "temperature": r["currentWeather"].get("temperature_c"),
                    "weather": r["currentWeather"].get("weather_desc"),
                    "windSpeed": r["currentWeather"].get("wind_speed_kmh"),
                    "airQualityAqi": r["airQuality"].get("european_aqi")
                }
                for r in all_results
            ]
        }
        await Actor.set_value("OUTPUT", summary_payload)
        Actor.log.info(f"Weather Intelligence Actor finished. Stored OUTPUT in Key-Value store with {len(all_results)} locations.")

if __name__ == "__main__":
    asyncio.run(main())
