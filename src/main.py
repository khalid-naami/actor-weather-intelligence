"""Apify Actor Entrypoint: Global Weather, Climate & Natural Disasters Intelligence."""

import asyncio
import math
import os
import sys
from typing import Any, Dict, List

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from apify import Actor
from src.openmeteo_client import OpenMeteoClient, decode_weather_code
from src.disasters_client import DisastersClient
from src.marine_space_client import MarineSpaceClient
from src.analytics_engine import WeatherAnalyticsEngine
from src.tectonic_data import find_nearest_fault


def sanitize_value(val: Any) -> Any:
    """Recursively converts pandas/numpy/timestamp objects and strips None/NaN/Inf."""
    if val is None:
        return None
    if isinstance(val, (pd.Timestamp,)):
        return val.isoformat()
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if hasattr(val, "item") and callable(getattr(val, "item")):
        try:
            scalar = val.item()
            return sanitize_value(scalar)
        except Exception:
            pass
    if isinstance(val, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in val.items():
            sv = sanitize_value(v)
            if sv is not None:
                cleaned[str(k)] = sv
        return cleaned
    if isinstance(val, list):
        cleaned_list = []
        for item in val:
            si = sanitize_value(item)
            if si is not None:
                cleaned_list.append(si)
        return cleaned_list
    return val


def summarize_air_quality_df(aqi_df: pd.DataFrame) -> Dict[str, Any]:
    """Extracts a JSON-serializable current and 24h summary from the Air Quality DataFrame."""
    if aqi_df is None or aqi_df.empty:
        return {}
    df_valid = aqi_df.dropna(how="all")
    if df_valid.empty:
        return {}
    latest = df_valid.iloc[0]

    def _safe_float(col: str, row: pd.Series) -> Any:
        v = row.get(col)
        if v is None or pd.isna(v):
            s = df_valid[col].dropna() if col in df_valid.columns else pd.Series(dtype=float)
            v = s.iloc[0] if not s.empty else None
        return round(float(v), 2) if v is not None and not pd.isna(v) else None

    us_aqi = _safe_float("us_aqi", latest)
    eu_aqi = _safe_float("european_aqi", latest)
    pm25 = _safe_float("pm2_5", latest)
    pm10 = _safe_float("pm10", latest)
    no2 = _safe_float("nitrogen_dioxide", latest)
    o3 = _safe_float("ozone", latest)
    uv = _safe_float("uv_index", latest)
    max_uv = round(float(df_valid["uv_index"].max()), 2) if "uv_index" in df_valid.columns and not df_valid["uv_index"].dropna().empty else uv

    category = "Good"
    if us_aqi is not None:
        if us_aqi > 200:
            category = "Very Unhealthy"
        elif us_aqi > 150:
            category = "Unhealthy"
        elif us_aqi > 100:
            category = "Unhealthy for Sensitive Groups"
        elif us_aqi > 50:
            category = "Moderate"

    return sanitize_value({
        "us_aqi": us_aqi,
        "european_aqi": eu_aqi,
        "aqi_category": category,
        "pm2_5_ug_m3": pm25,
        "pm10_ug_m3": pm10,
        "nitrogen_dioxide_ug_m3": no2,
        "ozone_ug_m3": o3,
        "uv_index": uv,
        "max_uv_index_forecast": max_uv,
    })


def summarize_marine_df(marine_df: pd.DataFrame) -> Dict[str, Any]:
    """Extracts a JSON-serializable summary from the Marine Weather DataFrame."""
    if marine_df is None or marine_df.empty:
        return {"is_coastal_or_marine": False}
    df_valid = marine_df.dropna(how="all")
    if df_valid.empty or ("wave_height" in df_valid.columns and df_valid["wave_height"].dropna().empty):
        return {"is_coastal_or_marine": False}

    non_null_waves = df_valid.dropna(subset=["wave_height"]) if "wave_height" in df_valid.columns else df_valid
    latest = non_null_waves.iloc[0] if not non_null_waves.empty else df_valid.iloc[0]

    def _val(col: str) -> Any:
        v = latest.get(col)
        return round(float(v), 2) if v is not None and not pd.isna(v) else None

    max_wave = (
        round(float(df_valid["wave_height"].max()), 2)
        if "wave_height" in df_valid.columns and not df_valid["wave_height"].dropna().empty
        else None
    )

    return sanitize_value({
        "is_coastal_or_marine": True,
        "wave_height_m": _val("wave_height"),
        "wave_direction_deg": _val("wave_direction"),
        "wave_period_s": _val("wave_period"),
        "swell_wave_height_m": _val("swell_wave_height"),
        "swell_wave_period_s": _val("swell_wave_period"),
        "wind_wave_height_m": _val("wind_wave_height"),
        "max_wave_height_7d_m": max_wave,
    })


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        locations = actor_input.get("locations") or [
            "Casablanca",
            "Paris",
            "Dubai",
            "Tokyo",
        ]
        forecast_days = int(actor_input.get("forecastDays", 7))
        include_air_quality = bool(actor_input.get("includeAirQuality", True))
        include_marine = bool(actor_input.get("includeMarineWeather", actor_input.get("includeMarineAndSpace", True)))
        include_space = bool(actor_input.get("includeSpaceWeather", actor_input.get("includeMarineAndSpace", True)))
        include_disasters = bool(actor_input.get("includeEarthquakes", actor_input.get("includeDisasters", True)))
        api_key = actor_input.get("apiKey") or os.getenv("APIFY_TOKEN") or os.getenv("API_KEY", "")

        Actor.log.info(f"Starting Weather & Disasters Intelligence for {len(locations)} location(s)...")
        if api_key:
            Actor.log.info("API Key / Token authentication provided.")

        client = OpenMeteoClient()
        disasters_client = DisastersClient()
        marine_client = MarineSpaceClient()

        # Fetch global space weather & earthquake feeds once if enabled
        space_weather_clean: Dict[str, Any] = {}
        recent_earthquakes: List[Dict[str, Any]] = []
        quakes_df = pd.DataFrame()
        eonet_df = pd.DataFrame()

        if include_space:
            try:
                Actor.log.info("Fetching NOAA SWPC planetary K-index & space weather telemetry...")
                raw_sw = marine_client.fetch_space_weather()
                kp_df = raw_sw.get("kp_history_df")
                kp_history_records: List[Dict[str, Any]] = []
                if isinstance(kp_df, pd.DataFrame) and not kp_df.empty:
                    kp_tail = kp_df.tail(8).copy()
                    if "time" in kp_tail.columns:
                        kp_tail["time"] = kp_tail["time"].astype(str)
                    kp_history_records = kp_tail.to_dict(orient="records")

                space_weather_clean = sanitize_value({
                    "current_kp": raw_sw.get("current_kp"),
                    "max_24h_kp": raw_sw.get("max_24h_kp"),
                    "storm_level": raw_sw.get("storm_level"),
                    "aurora_visibility": raw_sw.get("aurora_visibility"),
                    "radio_blackout_risk": raw_sw.get("radio_blackout_risk"),
                    "solar_wind_Estimate_kms": raw_sw.get("solar_wind_Estimate_kms"),
                    "recent_kp_observations": kp_history_records,
                })
            except Exception as e:
                Actor.log.warning(f"Space weather fetch warning: {e}")

        if include_disasters:
            try:
                Actor.log.info("Fetching live USGS global seismic events & NASA EONET natural hazards...")
                quakes_df = disasters_client.fetch_usgs_earthquakes(feed="all_week", min_magnitude=4.5)
                if quakes_df is not None and not quakes_df.empty:
                    q_copy = quakes_df.head(15).copy()
                    if "time" in q_copy.columns:
                        q_copy["time"] = q_copy["time"].apply(
                            lambda t: t.isoformat() if hasattr(t, "isoformat") else str(t)
                        )
                    recent_earthquakes = sanitize_value(q_copy.to_dict(orient="records"))
                eonet_df = disasters_client.fetch_nasa_eonet_events(days=20, limit=30)
            except Exception as e:
                Actor.log.warning(f"USGS/NASA disasters fetch warning: {e}")

        results: List[Dict[str, Any]] = []

        for loc_query in locations:
            Actor.log.info(f"Geocoding and analyzing location: {loc_query}")
            geo_results = client.search_locations(loc_query, count=1)
            if not geo_results:
                Actor.log.warning(f"Could not geocode '{loc_query}', skipping.")
                continue

            loc = geo_results[0]
            lat = float(loc["latitude"])
            lon = float(loc["longitude"])
            city_name = loc.get("name", loc_query)
            country = loc.get("country", "")
            tz = loc.get("timezone", "auto")

            # 1. Core Forecast & Atmospheric Telemetry
            forecast = client.fetch_forecast(lat, lon, timezone_str=tz, forecast_days=forecast_days)
            current_raw = dict(forecast.get("current", {}) or {})
            wmo_info = decode_weather_code(int(current_raw.get("weather_code", 0) or 0))
            current_weather = sanitize_value({
                **current_raw,
                "temperature_c": current_raw.get("temperature_2m"),
                "apparent_temperature_c": current_raw.get("apparent_temperature"),
                "weather_desc": f"{wmo_info.get('icon', '')} {wmo_info.get('label', 'Clear')}".strip(),
                "weather_label": wmo_info.get("label", "Clear"),
                "wind_speed_kmh": current_raw.get("wind_speed_10m"),
            })

            daily_df = forecast.get("daily_df")
            hourly_df = forecast.get("hourly_df")
            daily_records: List[Dict[str, Any]] = []
            if isinstance(daily_df, pd.DataFrame) and not daily_df.empty:
                d_copy = daily_df.copy()
                if "time" in d_copy.columns:
                    d_copy["time"] = d_copy["time"].apply(
                        lambda t: t.strftime("%Y-%m-%d") if hasattr(t, "strftime") else str(t)
                    )
                daily_records = sanitize_value(d_copy.to_dict(orient="records"))

            # Climate & Renewable Energy Analytics
            analytics_summary: Dict[str, Any] = {}
            try:
                if isinstance(daily_df, pd.DataFrame) and not daily_df.empty:
                    dd_df = WeatherAnalyticsEngine.compute_degree_days(daily_df)
                    anom_df = WeatherAnalyticsEngine.detect_temperature_anomalies(daily_df)
                    analytics_summary["total_hdd"] = round(float(dd_df["hdd"].sum()), 1) if "hdd" in dd_df.columns else 0.0
                    analytics_summary["total_cdd"] = round(float(dd_df["cdd"].sum()), 1) if "cdd" in dd_df.columns else 0.0
                    analytics_summary["max_temp_z_score"] = round(float(anom_df["temp_z_score"].abs().max()), 2) if "temp_z_score" in anom_df.columns else 0.0
                if isinstance(hourly_df, pd.DataFrame) and not hourly_df.empty:
                    ren = WeatherAnalyticsEngine.calculate_renewable_potential(hourly_df)
                    analytics_summary["solar_Suitability"] = ren.get("solar_Suitability")
                    analytics_summary["wind_Suitability"] = ren.get("wind_Suitability")
                    analytics_summary["avg_daily_solar_kwh_m2"] = ren.get("avg_daily_solar_kwh_m2")
                    analytics_summary["avg_wind_power_density_wm2"] = ren.get("avg_wind_power_density_wm2")
            except Exception as e:
                Actor.log.warning(f"Analytics engine warning for {city_name}: {e}")

            # 2. Air Quality
            air_quality: Dict[str, Any] = {}
            if include_air_quality:
                try:
                    aqi_df = client.fetch_air_quality(lat, lon, timezone_str=tz)
                    air_quality = summarize_air_quality_df(aqi_df)
                except Exception as e:
                    Actor.log.warning(f"Air quality warning for {city_name}: {e}")

            # 3. Marine Weather
            marine_data: Dict[str, Any] = {}
            if include_marine:
                try:
                    m_df = marine_client.fetch_marine_weather(lat, lon, timezone_str=tz)
                    marine_data = summarize_marine_df(m_df)
                except Exception as e:
                    Actor.log.warning(f"Marine weather warning for {city_name}: {e}")

            # 4. Tectonic Plate & Nearest Natural Hazards
            fault_info = find_nearest_fault(lat, lon)
            nearest_hazards: List[Dict[str, Any]] = []
            if include_disasters:
                try:
                    nearest_hazards = sanitize_value(
                        disasters_client.find_nearest_hazards(lat, lon, quakes_df, eonet_df, radius_km=2500.0)[:5]
                    )
                except Exception:
                    nearest_hazards = []

            location_label = f"{city_name}, {country}".strip(", ")
            result_item = sanitize_value({
                # Snake_case schema fields (used by dataset_schema.json & Overview table)
                "type": "weather_climate_intelligence",
                "location": location_label,
                "coordinates": {"latitude": lat, "longitude": lon, "timezone": tz},
                "current_weather": current_weather,
                "air_quality": air_quality,
                "marine_forecast": marine_data,
                "solar_activity": space_weather_clean.get("storm_level", "G0 (Quiet)") if include_space else "Not Requested",
                "geomagnetic_k_index": space_weather_clean.get("current_kp", 2.0) if include_space else 0.0,
                "usgs_earthquakes": recent_earthquakes[:5] if include_disasters else [],
                # CamelCase fields for backward-compatible API consumers
                "query": loc_query,
                "resolvedName": city_name,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
                "tectonicPlate": fault_info,
                "currentWeather": current_weather,
                "airQuality": air_quality,
                "marineWeather": marine_data,
                "spaceWeather": space_weather_clean,
                "dailyForecast": daily_records,
                "analyticsSummary": analytics_summary,
                "nearestNaturalHazards": nearest_hazards,
                "recentMajorEarthquakes": recent_earthquakes[:5] if include_disasters else [],
            })

            results.append(result_item)
            await Actor.push_data(result_item)

        # Save summary report to Key-Value Store (OUTPUT)
        summary_payload = sanitize_value({
            "analyzedLocationsCount": len(results),
            "forecastDays": forecast_days,
            "spaceWeatherSummary": {
                "solarActivity": space_weather_clean.get("storm_level", "G0 (Quiet)"),
                "kpIndex": space_weather_clean.get("current_kp", 2.0),
                "max24hKp": space_weather_clean.get("max_24h_kp", 2.0),
                "auroraVisibility": space_weather_clean.get("aurora_visibility"),
            } if include_space else None,
            "recentEarthquakesCount": len(recent_earthquakes),
            "weatherHighlights": [
                {
                    "city": r.get("resolvedName"),
                    "country": r.get("country"),
                    "temperature": r.get("currentWeather", {}).get("temperature_c"),
                    "weather": r.get("currentWeather", {}).get("weather_desc"),
                    "windSpeed": r.get("currentWeather", {}).get("wind_speed_kmh"),
                    "usAqi": r.get("airQuality", {}).get("us_aqi"),
                }
                for r in results
            ],
        })

        await Actor.set_value("OUTPUT", summary_payload)
        if not results:
            await Actor.fail(status_message="No weather intelligence records could be resolved for the provided locations.")
            return
        Actor.log.info(f"Successfully processed {len(results)} locations and saved OUTPUT summary.")


if __name__ == "__main__":
    asyncio.run(main())
