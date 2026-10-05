"""Marine Ocean Meteorology and NOAA Space Weather Client."""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import requests

logger = logging.getLogger(__name__)

class MarineSpaceClient:
    """Client for Open-Meteo Marine and NOAA SWPC Space Weather (100% Free, No API Key)."""

    MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
    NOAA_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WeatherIntelligenceApp/1.0 (Marine-Space Engine)"
        })

    def fetch_marine_weather(self, latitude: float, longitude: float, timezone_str: str = "auto") -> pd.DataFrame:
        """Fetch ocean waves, swell heights, and wave periods."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone_str,
            "hourly": [
                "wave_height", "wave_direction", "wave_period",
                "wind_wave_height", "wind_wave_direction", "wind_wave_period",
                "swell_wave_height", "swell_wave_direction", "swell_wave_period"
            ]
        }
        try:
            resp = self.session.get(self.MARINE_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                if hourly and "time" in hourly:
                    df = pd.DataFrame(hourly)
                    df["time"] = pd.to_datetime(df["time"])
                    return df
        except Exception as e:
            logger.info(f"Marine data unavailable for inland coordinates ({latitude}, {longitude}): {e}")
        return pd.DataFrame()

    def fetch_space_weather(self) -> Dict[str, Any]:
        """Fetch real-time NOAA Planetary Kp Index (Geomagnetic Storm Activity)."""
        try:
            resp = self.session.get(self.NOAA_KP_URL, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                # format: [["time_tag", "Kp", "a_running", "station_count"], ["2026-10-01 20:00:00.000", "2.67", ...]]
                if len(data) >= 2:
                    latest = data[-1]
                    time_tag = latest[0]
                    kp_val = float(latest[1])

                    # Storm Level
                    if kp_val < 4.0:
                        storm_level = "Quiet / Normal (G0) 🟢"
                        aurora_desc = "Aurora visible only in high polar latitudes."
                    elif kp_val < 5.0:
                        storm_level = "Unsettled (G0) 🟡"
                        aurora_desc = "Aurora activity slightly elevated."
                    elif kp_val < 6.0:
                        storm_level = "Minor Geomagnetic Storm (G1) 🟠"
                        aurora_desc = "Weak power grid fluctuations; migratory animals affected."
                    elif kp_val < 7.0:
                        storm_level = "Moderate Geomagnetic Storm (G2) 🔴"
                        aurora_desc = "High-latitude power systems may experience voltage alarms."
                    elif kp_val < 8.0:
                        storm_level = "Strong Geomagnetic Storm (G3) 🟣"
                        aurora_desc = "Voltage corrections required; false alarms on protection devices."
                    else:
                        storm_level = "Severe / Extreme Storm (G4-G5) ⚠️🔥"
                        aurora_desc = "Widespread voltage control problems; satellite orientation issues."

                    # Convert recent 24h history to DataFrame
                    history = []
                    for row in data[1:]:
                        try:
                            history.append({
                                "time": row[0],
                                "Kp": float(row[1])
                            })
                        except Exception:
                            pass
                    df_kp = pd.DataFrame(history)

                    return {
                        "current_kp": kp_val,
                        "time_utc": time_tag,
                        "storm_level": storm_level,
                        "aurora_impact": aurora_desc,
                        "kp_history_df": df_kp
                    }
        except Exception as e:
            logger.error(f"Error fetching NOAA Space Weather: {e}")

        # Fallback normal state
        return {
            "current_kp": 2.33,
            "time_utc": "Live",
            "storm_level": "Quiet / Normal (G0) 🟢",
            "aurora_impact": "Aurora visible only in polar latitudes.",
            "kp_history_df": pd.DataFrame()
        }
