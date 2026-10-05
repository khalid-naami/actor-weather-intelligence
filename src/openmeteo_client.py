"""Open-Meteo API Client with Geocoding, Forecast, Historical Climate Archive, and Air Quality."""

import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# WMO Weather Code Translations
WMO_CODE_MAP = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌧️❄️"),
    57: ("Dense freezing drizzle", "🌧️❄️"),
    61: ("Slight rain", "🌧️"),
    62: ("Moderate rain", "🌧️"),
    63: ("Heavy rain", "🌧️🌧️"),
    65: ("Very heavy rain", "🌊"),
    66: ("Light freezing rain", "🌨️"),
    67: ("Heavy freezing rain", "🌨️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Moderate snow fall", "❄️"),
    75: ("Heavy snow fall", "❄️❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⚡⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️🌩️"),
    99: ("Thunderstorm with heavy hail", "⛈️⚡🌩️")
}

def decode_weather_code(code: int) -> Tuple[str, str]:
    """Return text description and emoji for a WMO weather code."""
    return WMO_CODE_MAP.get(int(code), ("Unknown", "🌡️"))


class OpenMeteoClient:
    """Client for querying Open-Meteo APIs (No API key required)."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WeatherIntelligenceApp/1.0 (Streamlit Open-Meteo Analytics Engine)"
        })

    def search_location(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Search cities and locations by name using Open-Meteo Geocoding API."""
        if not query or len(query.strip()) < 2:
            return []

        try:
            params = {
                "name": query.strip(),
                "count": count,
                "language": "en",
                "format": "json"
            }
            resp = self.session.get(self.GEOCODING_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                locations = []
                for item in results:
                    name = item.get("name", "")
                    admin1 = item.get("admin1", "")
                    country = item.get("country", "")
                    country_code = item.get("country_code", "")
                    flag = f" ({country_code})" if country_code else ""
                    
                    label_parts = [p for p in [name, admin1, country] if p]
                    label = ", ".join(label_parts) + flag

                    locations.append({
                        "id": item.get("id"),
                        "name": name,
                        "latitude": float(item.get("latitude")),
                        "longitude": float(item.get("longitude")),
                        "elevation": item.get("elevation", 0),
                        "timezone": item.get("timezone", "UTC"),
                        "country": country,
                        "country_code": country_code,
                        "admin1": admin1,
                        "display_name": label
                    })
                return locations
        except Exception as e:
            logger.error(f"Geocoding error for '{query}': {e}")
        return []

    def fetch_forecast(self, latitude: float, longitude: float, timezone_str: str = "auto", forecast_days: int = 14) -> Dict[str, Any]:
        """Fetch comprehensive real-time, hourly, and daily forecasts."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone_str,
            "forecast_days": min(max(forecast_days, 1), 16),
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "weather_code", "pressure_msl",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"
            ],
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "dew_point_2m",
                "apparent_temperature", "precipitation_probability", "precipitation",
                "weather_code", "pressure_msl", "surface_pressure", "cloud_cover",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
                "direct_normal_irradiance", "uv_index", "soil_temperature_0cm",
                "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm",
                "et0_fao_evapotranspiration", "vapour_pressure_deficit"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset",
                "uv_index_max", "precipitation_sum", "precipitation_hours",
                "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max",
                "wind_direction_10m_dominant", "shortwave_radiation_sum", "et0_fao_evapotranspiration"
            ]
        }
        try:
            resp = self.session.get(self.FORECAST_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                
                # Convert hourly dict to DataFrame
                hourly_dict = data.get("hourly", {})
                if hourly_dict:
                    df_hourly = pd.DataFrame(hourly_dict)
                    if "time" in df_hourly.columns:
                        df_hourly["time"] = pd.to_datetime(df_hourly["time"])
                    data["hourly_df"] = df_hourly

                # Convert daily dict to DataFrame
                daily_dict = data.get("daily", {})
                if daily_dict:
                    df_daily = pd.DataFrame(daily_dict)
                    if "time" in df_daily.columns:
                        df_daily["time"] = pd.to_datetime(df_daily["time"])
                    data["daily_df"] = df_daily

                return data
        except Exception as e:
            logger.error(f"Error fetching forecast for lat={latitude}, lon={longitude}: {e}")
        return {}

    def fetch_historical_climate(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        timezone_str: str = "auto"
    ) -> pd.DataFrame:
        """Fetch historical daily climate records from Open-Meteo Archive (1940 - present)."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone_str,
            "daily": [
                "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
                "apparent_temperature_max", "apparent_temperature_min", "apparent_temperature_mean",
                "precipitation_sum", "rain_sum", "snowfall_sum", "precipitation_hours",
                "wind_speed_10m_max", "wind_gusts_10m_max", "shortwave_radiation_sum"
            ]
        }
        try:
            resp = self.session.get(self.ARCHIVE_URL, params=params, timeout=self.timeout + 15)
            if resp.status_code == 200:
                data = resp.json()
                daily_dict = data.get("daily", {})
                if daily_dict:
                    df = pd.DataFrame(daily_dict)
                    if "time" in df.columns:
                        df["time"] = pd.to_datetime(df["time"])
                        df.rename(columns={"time": "Date"}, inplace=True)
                    return df
        except Exception as e:
            logger.error(f"Error fetching climate archive: {e}")
        return pd.DataFrame()

    def fetch_air_quality(self, latitude: float, longitude: float, timezone_str: str = "auto") -> pd.DataFrame:
        """Fetch hourly air quality indices and pollutant concentrations."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone_str,
            "hourly": [
                "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide",
                "sulphur_dioxide", "ozone", "european_aqi", "us_aqi"
            ]
        }
        try:
            resp = self.session.get(self.AIR_QUALITY_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                hourly_dict = data.get("hourly", {})
                if hourly_dict:
                    df = pd.DataFrame(hourly_dict)
                    if "time" in df.columns:
                        df["time"] = pd.to_datetime(df["time"])
                    return df
        except Exception as e:
            logger.error(f"Error fetching air quality: {e}")
        return pd.DataFrame()
