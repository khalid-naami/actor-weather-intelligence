"""Quantitative Weather Analytics, Anomaly Detection, Energy HDD/CDD, and Climate Trend Engine."""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

class WeatherAnalyticsEngine:
    """Analytical engine for energy metrics, anomalies, renewable potential, and climate statistics."""

    @staticmethod
    def compute_degree_days(df: pd.DataFrame, base_temp_c: float = 18.0) -> pd.DataFrame:
        """
        Calculate Heating Degree Days (HDD) and Cooling Degree Days (CDD):
        - HDD = max(0, Base - T_mean) -> proxy for natural gas / heating demand
        - CDD = max(0, T_mean - Base) -> proxy for air conditioning / power grid demand
        """
        res = df.copy()
        if "temperature_2m_mean" in res.columns:
            mean_col = "temperature_2m_mean"
        elif "temperature_2m_max" in res.columns and "temperature_2m_min" in res.columns:
            res["temperature_2m_mean"] = (res["temperature_2m_max"] + res["temperature_2m_min"]) / 2.0
            mean_col = "temperature_2m_mean"
        else:
            return res

        res["HDD"] = np.maximum(0.0, base_temp_c - res[mean_col])
        res["CDD"] = np.maximum(0.0, res[mean_col] - base_temp_c)
        return res

    @staticmethod
    def detect_temperature_anomalies(df: pd.DataFrame, temp_col: str = "temperature_2m_mean", window: int = 30) -> pd.DataFrame:
        """
        Compute rolling Z-score to detect statistical heatwaves and cold snaps:
        Z = (T - rolling_mean) / rolling_std
        """
        res = df.copy()
        if temp_col not in res.columns:
            return res

        rolling_mean = res[temp_col].rolling(window=window, min_periods=7).mean()
        rolling_std = res[temp_col].rolling(window=window, min_periods=7).std().replace(0, np.nan)
        
        # Fallback to global mean/std if series is short
        if rolling_mean.isna().all():
            rolling_mean = res[temp_col].mean()
            rolling_std = max(res[temp_col].std(), 0.1)

        res["rolling_mean"] = rolling_mean.bfill().ffill()
        res["rolling_std"] = rolling_std.bfill().ffill()
        res["z_score"] = (res[temp_col] - res["rolling_mean"]) / res["rolling_std"]
        res["anomaly_type"] = "Normal"
        res.loc[res["z_score"] >= 2.0, "anomaly_type"] = "Severe Heatwave 🔥"
        res.loc[res["z_score"] >= 1.5, "anomaly_type"] = "Moderate Heatwave ☀️"
        res.loc[res["z_score"] <= -2.0, "anomaly_type"] = "Severe Cold Snap ❄️"
        res.loc[res["z_score"] <= -1.5, "anomaly_type"] = "Moderate Cold Snap 🧊"
        return res

    @staticmethod
    def calculate_renewable_potential(hourly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Estimate Solar PV and Wind Energy Potential:
        - Solar Output Index: Radiation (W/m^2) with PV thermal derating (-0.4% per °C above 25°C).
        - Wind Power Density: P = 0.5 * rho * v^3 (Air density rho ~ 1.225 kg/m^3).
        """
        if hourly_df.empty:
            return {"avg_solar_index": 0, "avg_wind_density_w_m2": 0, "hourly_summary": hourly_df}

        df = hourly_df.copy()
        
        # 1. Solar Index
        if "direct_normal_irradiance" in df.columns and "temperature_2m" in df.columns:
            irradiance = df["direct_normal_irradiance"].fillna(0)
            temp = df["temperature_2m"].fillna(20)
            # Temperature derating factor
            thermal_loss = np.maximum(0, (temp - 25.0) * 0.004)
            df["solar_pv_index_w_m2"] = np.maximum(0, irradiance * (1.0 - thermal_loss))
        else:
            df["solar_pv_index_w_m2"] = 0.0

        # 2. Wind Power Density (W/m^2)
        if "wind_speed_10m" in df.columns:
            # v is in km/h or m/s? Open-Meteo returns km/h by default or m/s
            v_ms = df["wind_speed_10m"] / 3.6  # convert km/h to m/s
            rho = 1.225  # kg/m^3 standard air density
            df["wind_power_density_w_m2"] = 0.5 * rho * (v_ms ** 3)
        else:
            df["wind_power_density_w_m2"] = 0.0

        return {
            "avg_solar_index": round(float(df["solar_pv_index_w_m2"].mean()), 1),
            "peak_solar_index": round(float(df["solar_pv_index_w_m2"].max()), 1),
            "avg_wind_density_w_m2": round(float(df["wind_power_density_w_m2"].mean()), 1),
            "peak_wind_density_w_m2": round(float(df["wind_power_density_w_m2"].max()), 1),
            "enriched_df": df
        }

    @staticmethod
    def calculate_climate_warming_trend(historical_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute multi-year warming trend rate (°C per decade) and annual temperature statistics.
        """
        if historical_df.empty or "Date" not in historical_df.columns:
            return {"slope_c_per_decade": 0.0, "p_value": 1.0, "annual_df": pd.DataFrame()}

        df = historical_df.copy()
        df["Year"] = pd.to_datetime(df["Date"]).dt.year
        
        temp_col = "temperature_2m_mean" if "temperature_2m_mean" in df.columns else "temperature_2m_max"
        
        annual = df.groupby("Year").agg({
            temp_col: "mean",
            "precipitation_sum": "sum"
        }).reset_index().rename(columns={temp_col: "mean_temp_c", "precipitation_sum": "total_precip_mm"})

        if len(annual) < 3:
            return {"slope_c_per_decade": 0.0, "p_value": 1.0, "annual_df": annual}

        # Linear regression on year vs mean temperature
        x = annual["Year"].values
        y = annual["mean_temp_c"].values
        valid = ~np.isnan(y)
        if valid.sum() < 3:
            return {"slope_c_per_decade": 0.0, "p_value": 1.0, "annual_df": annual}

        slope, intercept, r_value, p_value, std_err = stats.linregress(x[valid], y[valid])
        slope_per_decade = slope * 10.0

        annual["trend_line"] = intercept + slope * x

        return {
            "slope_c_per_decade": round(float(slope_per_decade), 3),
            "r_squared": round(float(r_value ** 2), 3),
            "p_value": round(float(p_value), 5),
            "annual_df": annual,
            "warming_narrative": (
                f"+{slope_per_decade:.2f}°C per decade (Warming)" if slope_per_decade > 0
                else f"{slope_per_decade:.2f}°C per decade (Cooling / Stable)"
            )
        }
