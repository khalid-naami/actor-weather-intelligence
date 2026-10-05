"""Global Natural Disasters Client interfacing with USGS Earthquakes and NASA EONET APIs."""

import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import requests

logger = logging.getLogger(__name__)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in kilometers."""
    r = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 1)


class DisastersClient:
    """Fetches real-time geohazards from official USGS and NASA EONET endpoints (100% Free, No API Key)."""

    USGS_FEEDS = {
        "all_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        "all_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson",
        "4.5_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
        "significant_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
    }

    NASA_EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WeatherIntelligenceApp/1.0 (USGS-NASA Disasters Engine)"
        })

    def fetch_usgs_earthquakes(self, feed: str = "all_week", min_magnitude: float = 2.5) -> pd.DataFrame:
        """Fetch worldwide earthquakes with magnitude, depth, and tsunami warning flags."""
        url = self.USGS_FEEDS.get(feed, self.USGS_FEEDS["all_week"])
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                records = []
                for item in features:
                    props = item.get("properties", {})
                    geom = item.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])

                    mag = props.get("mag")
                    if mag is None or mag < min_magnitude:
                        continue

                    # USGS coords format: [longitude, latitude, depth_km]
                    lon = float(coords[0])
                    lat = float(coords[1])
                    depth = float(coords[2]) if len(coords) > 2 else 0.0

                    time_ms = props.get("time", 0)
                    dt_str = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                    tsunami_flag = bool(props.get("tsunami", 0) == 1)

                    records.append({
                        "id": item.get("id"),
                        "place": props.get("place", "Unknown location"),
                        "magnitude": round(float(mag), 2),
                        "depth_km": round(depth, 1),
                        "latitude": round(lat, 4),
                        "longitude": round(lon, 4),
                        "time_utc": dt_str,
                        "timestamp_ms": time_ms,
                        "tsunami_warning": tsunami_flag,
                        "felt_reports": props.get("felt") or 0,
                        "alert_level": props.get("alert") or "None",
                        "status": props.get("status", "reviewed"),
                        "event_type": "Earthquake",
                        "url": props.get("url", "")
                    })

                df = pd.DataFrame(records)
                if not df.empty:
                    df = df.sort_values("magnitude", ascending=False).reset_index(drop=True)
                return df
        except Exception as e:
            logger.error(f"Error fetching USGS earthquakes: {e}")
        return pd.DataFrame()

    def fetch_nasa_eonet_events(self, days: int = 30) -> pd.DataFrame:
        """Fetch active natural events from NASA EONET (Cyclones, Volcanoes, Wildfires, Floods)."""
        try:
            params = {
                "days": days,
                "status": "all"
            }
            resp = self.session.get(self.NASA_EONET_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                records = []
                for ev in events:
                    title = ev.get("title", "")
                    cats = ev.get("categories", [])
                    cat_name = cats[0].get("title", "Severe Storms") if cats else "Severe Storms"
                    
                    geometries = ev.get("geometry", [])
                    if not geometries:
                        continue

                    # Get latest geometry entry
                    latest_geom = geometries[-1]
                    coords = latest_geom.get("coordinates", [])
                    geom_date = latest_geom.get("date", "")
                    if len(coords) < 2:
                        continue

                    lon = float(coords[0])
                    lat = float(coords[1])

                    mag_val = latest_geom.get("magnitudeValue")
                    mag_unit = latest_geom.get("magnitudeUnit")
                    intensity_str = f"{mag_val} {mag_unit}" if mag_val is not None else "Active Alert"

                    records.append({
                        "id": ev.get("id"),
                        "title": title,
                        "category": cat_name,
                        "latitude": round(lat, 4),
                        "longitude": round(lon, 4),
                        "date_utc": geom_date[:19].replace("T", " "),
                        "intensity": intensity_str,
                        "event_type": cat_name,
                        "url": ev.get("link", "")
                    })

                df = pd.DataFrame(records)
                if not df.empty:
                    df = df.sort_values("date_utc", ascending=False).reset_index(drop=True)
                return df
        except Exception as e:
            logger.error(f"Error fetching NASA EONET events: {e}")
        return pd.DataFrame()

    def find_nearest_hazards(
        self,
        user_lat: float,
        user_lon: float,
        earthquakes_df: pd.DataFrame,
        nasa_events_df: pd.DataFrame,
        top_n: int = 10
    ) -> pd.DataFrame:
        """Calculate distances from a city coordinate to all active hazards and return the closest."""
        all_hazards = []

        if not earthquakes_df.empty:
            for _, r in earthquakes_df.iterrows():
                d = haversine_distance_km(user_lat, user_lon, r["latitude"], r["longitude"])
                tsunami_str = " 🚨 (TSUNAMI RISK)" if r.get("tsunami_warning") else ""
                all_hazards.append({
                    "hazard_type": f"💥 Earthquake (M {r['magnitude']}){tsunami_str}",
                    "name_location": r["place"],
                    "distance_km": d,
                    "magnitude_details": f"Mag {r['magnitude']} | Depth {r['depth_km']} km",
                    "time_utc": r["time_utc"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "source": "USGS",
                    "url": r["url"]
                })

        if not nasa_events_df.empty:
            for _, r in nasa_events_df.iterrows():
                d = haversine_distance_km(user_lat, user_lon, r["latitude"], r["longitude"])
                emoji = "🌀" if "Storm" in r["category"] else ("🌋" if "Volcano" in r["category"] else "🔥")
                all_hazards.append({
                    "hazard_type": f"{emoji} {r['category']}",
                    "name_location": r["title"],
                    "distance_km": d,
                    "magnitude_details": str(r["intensity"]),
                    "time_utc": r["date_utc"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "source": "NASA EONET",
                    "url": r["url"]
                })

        if not all_hazards:
            return pd.DataFrame()

        df = pd.DataFrame(all_hazards).sort_values("distance_km").head(top_n).reset_index(drop=True)
        return df
