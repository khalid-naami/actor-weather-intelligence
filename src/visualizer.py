"""High-Performance Interactive Plotly Visualizations for Weather, Climate & Energy Analytics."""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Institutional Dark Color Palette
PALETTE = {
    "bg": "#0e1117",
    "card_bg": "#1e222b",
    "text": "#e0e6ed",
    "primary": "#38bdf8",     # Sky Blue
    "secondary": "#f59e0b",   # Amber / Sun
    "accent": "#10b981",      # Emerald
    "danger": "#ef4444",      # Red / Heat
    "cold": "#60a5fa",        # Blue / Cold
    "purple": "#a855f7",
    "grid": "#2a303c"
}

def create_forecast_overview_chart(hourly_df: pd.DataFrame, city_name: str) -> go.Figure:
    """Create a high-impact dual-axis chart with Temperature, Apparent Temp, and Precipitation."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=(f"🌡️ Temperature & Thermal Comfort Forecast ({city_name})", "🌧️ Precipitation & Rain Probability")
    )

    if hourly_df.empty or "time" not in hourly_df.columns:
        return fig

    x = hourly_df["time"]

    # Row 1: Temperature & Apparent Temp
    if "temperature_2m" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(
                x=x, y=hourly_df["temperature_2m"],
                name="Temperature (°C)",
                mode="lines",
                line=dict(color=PALETTE["secondary"], width=2.5),
                hovertemplate="%{x}<br>Temp: %{y:.1f}°C<extra></extra>"
            ),
            row=1, col=1
        )

    if "apparent_temperature" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(
                x=x, y=hourly_df["apparent_temperature"],
                name="Feels Like (°C)",
                mode="lines",
                line=dict(color=PALETTE["primary"], width=1.5, dash="dot"),
                hovertemplate="%{x}<br>Feels Like: %{y:.1f}°C<extra></extra>"
            ),
            row=1, col=1
        )

    # Row 2: Precipitation mm and Probability %
    if "precipitation" in hourly_df.columns:
        fig.add_trace(
            go.Bar(
                x=x, y=hourly_df["precipitation"],
                name="Precipitation (mm)",
                marker_color=PALETTE["primary"],
                opacity=0.7,
                hovertemplate="%{x}<br>Rain: %{y:.1f} mm<extra></extra>"
            ),
            row=2, col=1
        )

    if "precipitation_probability" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(
                x=x, y=hourly_df["precipitation_probability"],
                name="Rain Prob (%)",
                mode="lines",
                line=dict(color=PALETTE["accent"], width=1.5),
                yaxis="y3",
                hovertemplate="%{x}<br>Prob: %{y}%<extra></extra>"
            ),
            row=2, col=1
        )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"], family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=85, b=30),
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Temp (°C)", row=1, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Rain (mm)", row=2, col=1, gridcolor=PALETTE["grid"])
    return fig

def create_daily_temperature_bands(daily_df: pd.DataFrame, city_name: str) -> go.Figure:
    """Create range band chart showing daily Max, Min, and Apparent temperature envelopes."""
    fig = go.Figure()
    if daily_df.empty or "time" not in daily_df.columns:
        return fig

    x = daily_df["time"]

    # Max Temp
    fig.add_trace(go.Scatter(
        x=x, y=daily_df["temperature_2m_max"],
        name="Max Temp (°C)",
        mode="lines+markers",
        line=dict(color=PALETTE["danger"], width=2.5),
        marker=dict(size=6)
    ))

    # Min Temp
    fig.add_trace(go.Scatter(
        x=x, y=daily_df["temperature_2m_min"],
        name="Min Temp (°C)",
        mode="lines+markers",
        fill="tonexty",
        fillcolor="rgba(56, 189, 248, 0.15)",
        line=dict(color=PALETTE["cold"], width=2.5),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f"📅 14-Day Temperature Range & Diurnal Variation ({city_name})",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        yaxis=dict(title="Temperature (°C)", gridcolor=PALETTE["grid"]),
        xaxis=dict(gridcolor=PALETTE["grid"]),
        margin=dict(l=40, r=40, t=75, b=30)
    )
    return fig

def create_wind_and_pressure_chart(hourly_df: pd.DataFrame) -> go.Figure:
    """Plot Wind Speed, Wind Gusts, and Barometric MSL Pressure."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if hourly_df.empty or "time" not in hourly_df.columns:
        return fig

    x = hourly_df["time"]
    if "wind_speed_10m" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=hourly_df["wind_speed_10m"], name="Wind Speed (km/h)", line=dict(color=PALETTE["primary"], width=2)),
            secondary_y=False
        )
    if "wind_gusts_10m" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=hourly_df["wind_gusts_10m"], name="Wind Gusts (km/h)", line=dict(color=PALETTE["danger"], width=1.5, dash="dash")),
            secondary_y=False
        )
    if "pressure_msl" in hourly_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=hourly_df["pressure_msl"], name="Pressure (hPa)", line=dict(color=PALETTE["purple"], width=2)),
            secondary_y=True
        )

    fig.update_layout(
        title="💨 Wind Speed, Gusts & Atmospheric Pressure",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=75, b=30)
    )
    fig.update_yaxes(title_text="Wind (km/h)", secondary_y=False, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Pressure (hPa)", secondary_y=True, gridcolor=PALETTE["grid"])
    return fig

def create_degree_days_chart(degree_days_df: pd.DataFrame) -> go.Figure:
    """Create Energy Degree Days (Heating HDD vs Cooling CDD) chart."""
    fig = go.Figure()
    if degree_days_df.empty:
        return fig

    date_col = "Date" if "Date" in degree_days_df.columns else "time"
    x = degree_days_df[date_col]

    if "HDD" in degree_days_df.columns:
        fig.add_trace(go.Bar(
            x=x, y=degree_days_df["HDD"],
            name="Heating Demand (HDD) 🔥",
            marker_color=PALETTE["cold"]
        ))

    if "CDD" in degree_days_df.columns:
        fig.add_trace(go.Bar(
            x=x, y=degree_days_df["CDD"],
            name="Cooling Demand (CDD) ❄️",
            marker_color=PALETTE["danger"]
        ))

    fig.update_layout(
        title="⚡ Energy Demand Profile: Heating (HDD) vs. Cooling (CDD) Degree Days",
        template="plotly_dark",
        barmode="group",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        yaxis=dict(title="Degree Days (°C-days)", gridcolor=PALETTE["grid"]),
        xaxis=dict(gridcolor=PALETTE["grid"]),
        margin=dict(l=40, r=40, t=75, b=30)
    )
    return fig

def create_climate_warming_chart(annual_df: pd.DataFrame, city_name: str, slope_per_decade: float) -> go.Figure:
    """Plot multi-decade mean temperature trend and linear warming regression line."""
    fig = go.Figure()
    if annual_df.empty:
        return fig

    fig.add_trace(go.Scatter(
        x=annual_df["Year"], y=annual_df["mean_temp_c"],
        mode="markers+lines",
        name="Annual Mean Temp (°C)",
        marker=dict(color=PALETTE["primary"], size=7),
        line=dict(color=PALETTE["primary"], width=1.5, dash="dot")
    ))

    if "trend_line" in annual_df.columns:
        fig.add_trace(go.Scatter(
            x=annual_df["Year"], y=annual_df["trend_line"],
            mode="lines",
            name=f"Warming Trend ({slope_per_decade:+.2f}°C / decade)",
            line=dict(color=PALETTE["danger"], width=3)
        ))

    fig.update_layout(
        title=f"🌍 Multi-Decade Climate Trend & Warming Rate: {city_name} (1950 - Present)",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        yaxis=dict(title="Annual Mean Temperature (°C)", gridcolor=PALETTE["grid"]),
        xaxis=dict(title="Year", gridcolor=PALETTE["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=75, b=30)
    )
    return fig

def create_air_quality_gauge(aqi_value: float, index_type: str = "US AQI") -> go.Figure:
    """Generate Gauge Indicator for Air Quality Index with unclipped clear typography."""
    val = float(aqi_value) if (aqi_value is not None and not pd.isna(aqi_value)) else 0.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'font': {'size': 38, 'color': PALETTE["text"]}},
        title={'text': f"<b>{index_type}</b>", 'font': {'size': 16, 'color': PALETTE["primary"]}},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': PALETTE["text"]},
            'bar': {'color': "#ffffff", 'thickness': 0.25},
            'steps': [
                {'range': [0, 50], 'color': "#10b981"},    # Good (Green)
                {'range': [50, 100], 'color': "#f59e0b"},  # Moderate (Yellow)
                {'range': [100, 150], 'color': "#f97316"}, # Unhealthy for Sensitive (Orange)
                {'range': [150, 200], 'color': "#ef4444"}, # Unhealthy (Red)
                {'range': [200, 300], 'color': "#7c3aed"}  # Very Unhealthy (Purple)
            ]
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        height=320,
        margin=dict(l=40, r=40, t=70, b=30)
    )
    return fig

def create_pollutants_timeline_chart(aq_df: pd.DataFrame) -> go.Figure:
    """Multi-row timeline of Particulate Matter (PM2.5/PM10) and Chemical Gases (NO2, O3, SO2, CO, Dust)."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.55, 0.45],
        subplot_titles=("🔬 Particulate Matter (PM2.5 & PM10) vs. WHO Safe Limits", "💨 Atmospheric Toxic Gases (NO₂, O₃, SO₂ & Dust)")
    )
    if aq_df.empty or "time" not in aq_df.columns:
        return fig

    x = aq_df["time"]

    # Row 1: PM2.5 and PM10
    if "pm2_5" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["pm2_5"], name="PM2.5 Fine Particles", line=dict(color="#f43f5e", width=2.5),
                       hovertemplate="%{x}<br>PM2.5: %{y:.1f} µg/m³<extra></extra>"),
            row=1, col=1
        )
    if "pm10" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["pm10"], name="PM10 Coarse Particles", line=dict(color="#f59e0b", width=2),
                       hovertemplate="%{x}<br>PM10: %{y:.1f} µg/m³<extra></extra>"),
            row=1, col=1
        )

    # Add WHO 24h Guideline Threshold Lines
    fig.add_hline(y=15, line_dash="dash", line_color="#10b981", annotation_text="WHO PM2.5 Limit (15 µg/m³)", row=1, col=1)
    fig.add_hline(y=45, line_dash="dash", line_color="#38bdf8", annotation_text="WHO PM10 Limit (45 µg/m³)", row=1, col=1)

    # Row 2: Atmospheric Gases
    if "nitrogen_dioxide" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["nitrogen_dioxide"], name="NO₂ (Nitrogen Dioxide)", line=dict(color="#a855f7", width=1.5)),
            row=2, col=1
        )
    if "ozone" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["ozone"], name="O₃ (Ground-Level Ozone)", line=dict(color="#38bdf8", width=1.5)),
            row=2, col=1
        )
    if "sulphur_dioxide" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["sulphur_dioxide"], name="SO₂ (Sulfur Dioxide)", line=dict(color="#10b981", width=1.5)),
            row=2, col=1
        )
    if "dust" in aq_df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=aq_df["dust"], name="Mineral Dust", line=dict(color="#eab308", width=1.5, dash="dot")),
            row=2, col=1
        )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=85, b=30)
    )
    fig.update_yaxes(title_text="Concentration (µg/m³)", row=1, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Gas Conc (µg/m³)", row=2, col=1, gridcolor=PALETTE["grid"])
    return fig

def create_aqi_comparison_chart(aq_df: pd.DataFrame) -> go.Figure:
    """Comparative AQI evolution: US EPA AQI vs European AQI."""
    fig = go.Figure()
    if aq_df.empty or "time" not in aq_df.columns:
        return fig

    x = aq_df["time"]
    if "us_aqi" in aq_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=aq_df["us_aqi"], name="US EPA AQI (0-500 scale)",
            line=dict(color="#38bdf8", width=2.5),
            fill="tozeroy", fillcolor="rgba(56, 189, 248, 0.08)"
        ))
    if "european_aqi" in aq_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=aq_df["european_aqi"], name="European AQI (0-100 scale)",
            line=dict(color="#a855f7", width=2)
        ))

    # Add AQI Health Categories
    fig.add_hrect(y0=0, y1=50, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0, annotation_text="🟢 Good (0-50)")
    fig.add_hrect(y0=50, y1=100, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0, annotation_text="🟡 Moderate (50-100)")
    fig.add_hrect(y0=100, y1=150, fillcolor="rgba(249, 115, 22, 0.1)", line_width=0, annotation_text="🟠 Sensitive (100-150)")
    fig.add_hrect(y0=150, y1=300, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0, annotation_text="🔴 Unhealthy (>150)")

    fig.update_layout(
        title="📊 Multi-Scale Air Quality Index (AQI) Forecast & Health Bands",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="AQI Score", gridcolor=PALETTE["grid"]),
        xaxis=dict(gridcolor=PALETTE["grid"]),
        margin=dict(l=40, r=40, t=60, b=30)
    )
    return fig

def create_pollutants_radar(latest_dict: dict) -> go.Figure:
    """Radar Chart showing relative intensity of main pollutants against standard limits."""
    # Benchmarks (approximate 24h moderate threshold): PM2.5: 35, PM10: 50, NO2: 40, O3: 100, SO2: 40, CO: 4000
    categories = ['PM2.5', 'PM10', 'NO₂', 'Ozone (O₃)', 'SO₂', 'Carbon Monoxide']
    
    raw_pm25 = latest_dict.get('pm2_5', 10)
    raw_pm10 = latest_dict.get('pm10', 20)
    raw_no2 = latest_dict.get('nitrogen_dioxide', 15)
    raw_o3 = latest_dict.get('ozone', 45)
    raw_so2 = latest_dict.get('sulphur_dioxide', 5)
    raw_co = latest_dict.get('carbon_monoxide', 300)

    # Normalize to 0 - 100% of threshold
    values = [
        min(100.0, (raw_pm25 / 35.0) * 100.0),
        min(100.0, (raw_pm10 / 50.0) * 100.0),
        min(100.0, (raw_no2 / 40.0) * 100.0),
        min(100.0, (raw_o3 / 100.0) * 100.0),
        min(100.0, (raw_so2 / 40.0) * 100.0),
        min(100.0, (raw_co / 4000.0) * 100.0)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Concentration % of Threshold',
        fillcolor='rgba(56, 189, 248, 0.3)',
        line=dict(color=PALETTE["primary"], width=2)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=PALETTE["grid"]),
            angularaxis=dict(gridcolor=PALETTE["grid"])
        ),
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        title="🎯 Atmospheric Pollutant Load (% of Safety Threshold)",
        height=320,
        margin=dict(l=40, r=40, t=50, b=30)
    )
    return fig

def create_global_disasters_map(
    earthquakes_df: pd.DataFrame,
    nasa_events_df: pd.DataFrame,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    user_city: Optional[str] = None
) -> go.Figure:
    """Create a high-impact global dark-themed hazard map with Earthquakes, Cyclones, Volcanoes, and Tsunamis."""
    fig = go.Figure()

    # 0. Tectonic Plate Boundaries Layer
    try:
        from src.tectonic_data import TECTONIC_PLATES
        first_plate = True
        for plate_name, coords in TECTONIC_PLATES.items():
            lons = [pt[0] for pt in coords]
            lats = [pt[1] for pt in coords]
            fig.add_trace(go.Scattergeo(
                lon=lons,
                lat=lats,
                mode="lines",
                name="🧩 Tectonic Plate Boundaries & Faults",
                line=dict(width=1.5, color="#f97316", dash="dot"),
                hoverinfo="text",
                text=f"Crustal Plate Boundary: {plate_name}",
                showlegend=first_plate
            ))
            first_plate = False
    except Exception:
        pass

    # 1. Earthquakes Layer (USGS)
    if not earthquakes_df.empty:
        hover_texts = []
        sizes = []
        colors = []
        for _, r in earthquakes_df.iterrows():
            mag = r["magnitude"]
            depth = r["depth_km"]
            place = r["place"]
            tsu = "🌊 <b>TSUNAMI WARNING ACTIVE!</b><br>" if r["tsunami_warning"] else ""
            hover_texts.append(
                f"💥 <b>Earthquake M {mag:.1f}</b><br>{place}<br>"
                f"{tsu}Depth: {depth:.1f} km<br>Time: {r['time_utc']}"
            )
            sizes.append(max(6, (mag ** 1.8) * 1.5))
            colors.append(mag)

        fig.add_trace(go.Scattergeo(
            lon=earthquakes_df["longitude"],
            lat=earthquakes_df["latitude"],
            text=hover_texts,
            hoverinfo="text",
            name="💥 Earthquakes (USGS)",
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                colorscale="YlOrRd",
                colorbar=dict(title="Earthquake<br>Richter (M)", x=1.02, len=0.6),
                cmin=2.5,
                cmax=7.5,
                opacity=0.85,
                line=dict(width=1, color="rgba(255, 255, 255, 0.4)")
            )
        ))

        # Separate Tsunami Warnings Layer
        tsu_df = earthquakes_df[earthquakes_df["tsunami_warning"] == True]
        if not tsu_df.empty:
            fig.add_trace(go.Scattergeo(
                lon=tsu_df["longitude"],
                lat=tsu_df["latitude"],
                name="🌊 Tsunami Alert Warning",
                mode="markers",
                marker=dict(
                    size=16,
                    symbol="diamond",
                    color="#38bdf8",
                    line=dict(width=2, color="#ffffff")
                ),
                text=[f"🌊 <b>TSUNAMI ALERT</b><br>{p}<br>Mag: {m}" for p, m in zip(tsu_df["place"], tsu_df["magnitude"])],
                hoverinfo="text"
            ))

    # 2. NASA EONET Active Hazards (Cyclones, Volcanoes, Wildfires)
    if not nasa_events_df.empty:
        # Severe Storms / Cyclones
        storms_df = nasa_events_df[nasa_events_df["category"].str.contains("Storm|Cyclone|Hurricane|Typhoon", case=False, na=False)]
        if not storms_df.empty:
            fig.add_trace(go.Scattergeo(
                lon=storms_df["longitude"],
                lat=storms_df["latitude"],
                name="🌀 Severe Storms / Cyclones (NASA)",
                mode="markers",
                marker=dict(
                    size=12,
                    symbol="circle-open-dot",
                    color="#ec4899",
                    line=dict(width=2.5, color="#ec4899")
                ),
                text=[f"🌀 <b>{t}</b><br>{c}<br>Date: {d}" for t, c, d in zip(storms_df["title"], storms_df["category"], storms_df["date_utc"])],
                hoverinfo="text"
            ))

        # Volcanoes
        volcano_df = nasa_events_df[nasa_events_df["category"].str.contains("Volcano", case=False, na=False)]
        if not volcano_df.empty:
            fig.add_trace(go.Scattergeo(
                lon=volcano_df["longitude"],
                lat=volcano_df["latitude"],
                name="🌋 Active Volcanoes (NASA)",
                mode="markers",
                marker=dict(
                    size=14,
                    symbol="triangle-up",
                    color="#f97316",
                    line=dict(width=1.5, color="#ffffff")
                ),
                text=[f"🌋 <b>{t}</b><br>Active Eruption<br>Date: {d}" for t, d in zip(volcano_df["title"], volcano_df["date_utc"])],
                hoverinfo="text"
            ))

        # Wildfires
        fires_df = nasa_events_df[nasa_events_df["category"].str.contains("Fire|Wildfire", case=False, na=False)]
        if not fires_df.empty:
            fig.add_trace(go.Scattergeo(
                lon=fires_df["longitude"],
                lat=fires_df["latitude"],
                name="🔥 Wildfires (NASA)",
                mode="markers",
                marker=dict(
                    size=9,
                    symbol="square",
                    color="#ef4444",
                    opacity=0.8
                ),
                text=[f"🔥 <b>{t}</b><br>Active Fire<br>Date: {d}" for t, d in zip(fires_df["title"], fires_df["date_utc"])],
                hoverinfo="text"
            ))

    # 3. User Selected City Marker
    if user_lat is not None and user_lon is not None:
        fig.add_trace(go.Scattergeo(
            lon=[user_lon],
            lat=[user_lat],
            name=f"📍 {user_city or 'Selected Location'}",
            mode="markers+text",
            text=[f"📍 {user_city or 'Your City'}"],
            textposition="top center",
            textfont=dict(color="#38bdf8", size=13, family="Inter"),
            marker=dict(
                size=16,
                symbol="star",
                color="#38bdf8",
                line=dict(width=2, color="#ffffff")
            ),
            hoverinfo="text"
        ))

    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#1e2430",
        showocean=True,
        oceancolor="#0c1017",
        showlakes=True,
        lakecolor="#0c1017",
        showrivers=False,
        showcountries=True,
        countrycolor="#334155",
        coastlinecolor="#475569",
        showsubunits=True,
        subunitcolor="#1e293b",
        bgcolor=PALETTE["bg"]
    )

    fig.update_layout(
        title=dict(
            text="🌐 Global Real-Time Geohazards & Crustal Plates Map (USGS & NASA)",
            font=dict(size=16, color=PALETTE["text"]),
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        height=640,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(l=10, r=10, t=80, b=10)
    )
    return fig

def create_earthquake_distribution_chart(earthquakes_df: pd.DataFrame) -> go.Figure:
    """Magnitude vs. Depth Scatter Distribution Chart."""
    fig = go.Figure()
    if earthquakes_df.empty:
        return fig

    fig.add_trace(go.Scatter(
        x=earthquakes_df["magnitude"],
        y=earthquakes_df["depth_km"],
        mode="markers",
        marker=dict(
            size=earthquakes_df["magnitude"] * 2.5,
            color=earthquakes_df["magnitude"],
            colorscale="YlOrRd",
            showscale=True,
            colorbar=dict(title="Mag"),
            opacity=0.8
        ),
        text=[f"{p}<br>Mag: {m}<br>Depth: {d} km" for p, m, d in zip(earthquakes_df["place"], earthquakes_df["magnitude"], earthquakes_df["depth_km"])],
        hoverinfo="text"
    ))

    fig.update_layout(
        title="📊 Earthquake Magnitude vs. Focal Depth (km)",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        yaxis=dict(title="Focal Depth (km)", autorange="reversed", gridcolor=PALETTE["grid"]),
        xaxis=dict(title="Richter Magnitude (M)", gridcolor=PALETTE["grid"]),
        margin=dict(l=40, r=40, t=60, b=30)
    )
    return fig

def create_city_comparison_charts(df_a: pd.DataFrame, df_b: pd.DataFrame, name_a: str, name_b: str) -> go.Figure:
    """Side-by-side multi-variable comparison between two cities."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.45, 0.30, 0.25],
        subplot_titles=(
            f"🌡️ Temperature Comparison: {name_a} vs. {name_b} (°C)",
            "🌧️ Hourly Precipitation Comparison (mm)",
            "💨 Wind Speed & Gusts (km/h)"
        )
    )
    if df_a.empty or df_b.empty or "time" not in df_a.columns:
        return fig

    # Align on common time length
    min_len = min(len(df_a), len(df_b))
    time_series = df_a["time"].iloc[:min_len]

    # Row 1: Temperature
    if "temperature_2m" in df_a.columns and "temperature_2m" in df_b.columns:
        fig.add_trace(go.Scatter(
            x=time_series, y=df_a["temperature_2m"].iloc[:min_len],
            name=f"🌡️ {name_a} Temp", line=dict(color="#38bdf8", width=2.5)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=time_series, y=df_b["temperature_2m"].iloc[:min_len],
            name=f"🌡️ {name_b} Temp", line=dict(color="#f59e0b", width=2.5)
        ), row=1, col=1)

    # Row 2: Precipitation
    if "precipitation" in df_a.columns and "precipitation" in df_b.columns:
        fig.add_trace(go.Bar(
            x=time_series, y=df_a["precipitation"].iloc[:min_len],
            name=f"🌧️ {name_a} Rain", marker_color="rgba(56, 189, 248, 0.7)"
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=time_series, y=df_b["precipitation"].iloc[:min_len],
            name=f"🌧️ {name_b} Rain", marker_color="rgba(245, 158, 11, 0.7)"
        ), row=2, col=1)

    # Row 3: Wind Speed
    if "wind_speed_10m" in df_a.columns and "wind_speed_10m" in df_b.columns:
        fig.add_trace(go.Scatter(
            x=time_series, y=df_a["wind_speed_10m"].iloc[:min_len],
            name=f"💨 {name_a} Wind", line=dict(color="#10b981", width=2)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=time_series, y=df_b["wind_speed_10m"].iloc[:min_len],
            name=f"💨 {name_b} Wind", line=dict(color="#ec4899", width=2)
        ), row=3, col=1)

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"]),
        hovermode="x unified",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=85, b=30),
        height=680
    )
    fig.update_yaxes(title_text="Temp (°C)", row=1, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Rain (mm)", row=2, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Wind (km/h)", row=3, col=1, gridcolor=PALETTE["grid"])
    return fig

def create_marine_chart(marine_df: pd.DataFrame, location_name: str) -> go.Figure:
    """Ocean wave height, swell wave, and wave periods chart."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            f"🌊 Ocean Wave & Swell Height ({location_name})",
            "⏱️ Wave & Swell Period (Seconds)"
        )
    )
    if marine_df.empty or "time" not in marine_df.columns:
        return fig

    x = marine_df["time"]

    # Row 1: Wave Heights
    if "wave_height" in marine_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=marine_df["wave_height"], name="Significant Wave Height (m)",
            line=dict(color="#38bdf8", width=2.5), fill="tozeroy", fillcolor="rgba(56, 189, 248, 0.1)"
        ), row=1, col=1)
    if "swell_wave_height" in marine_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=marine_df["swell_wave_height"], name="Swell Height (m)",
            line=dict(color="#a855f7", width=1.8, dash="dash")
        ), row=1, col=1)
    if "wind_wave_height" in marine_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=marine_df["wind_wave_height"], name="Wind Wave (m)",
            line=dict(color="#10b981", width=1.5, dash="dot")
        ), row=1, col=1)

    # Row 2: Periods
    if "wave_period" in marine_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=marine_df["wave_period"], name="Wave Period (s)",
            line=dict(color="#f59e0b", width=2)
        ), row=2, col=1)
    if "swell_wave_period" in marine_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=marine_df["swell_wave_period"], name="Swell Period (s)",
            line=dict(color="#ec4899", width=1.5, dash="dash")
        ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=85, b=30),
        height=540
    )
    fig.update_yaxes(title_text="Height (meters)", row=1, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="Period (seconds)", row=2, col=1, gridcolor=PALETTE["grid"])
    return fig

def create_space_weather_gauge(kp_val: float) -> go.Figure:
    """NOAA Planetary Kp Index Space Weather Gauge."""
    val = float(kp_val) if (kp_val is not None and not pd.isna(kp_val)) else 0.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'font': {'size': 38, 'color': PALETTE["text"]}, 'suffix': " Kp"},
        title={'text': "<b>Planetary Geomagnetic Kp-Index</b>", 'font': {'size': 16, 'color': PALETTE["primary"]}},
        gauge={
            'axis': {'range': [0, 9], 'tickwidth': 1, 'tickcolor': PALETTE["text"], 'dtick': 1},
            'bar': {'color': "#ffffff", 'thickness': 0.25},
            'steps': [
                {'range': [0, 3], 'color': "#10b981"},   # Quiet G0 (Green)
                {'range': [3, 5], 'color': "#f59e0b"},   # Unsettled (Yellow)
                {'range': [5, 6], 'color': "#f97316"},   # G1 Minor Storm (Orange)
                {'range': [6, 7], 'color': "#ef4444"},   # G2 Moderate Storm (Red)
                {'range': [7, 8], 'color': "#a855f7"},   # G3 Strong Storm (Purple)
                {'range': [8, 9], 'color': "#7e22ce"}    # G4-G5 Severe/Extreme (Deep Purple)
            ]
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        height=320,
        margin=dict(l=40, r=40, t=70, b=30)
    )
    return fig

def create_space_weather_history(df_kp: pd.DataFrame) -> go.Figure:
    """Planetary Kp Index Trend with Geomagnetic Storm Warning Thresholds."""
    fig = go.Figure()
    if df_kp.empty or "time" not in df_kp.columns or "Kp" not in df_kp.columns:
        return fig

    fig.add_trace(go.Scatter(
        x=df_kp["time"], y=df_kp["Kp"],
        mode="lines+markers",
        name="NOAA Planetary Kp",
        line=dict(color="#38bdf8", width=2.5),
        marker=dict(size=5, color="#f59e0b")
    ))

    # Storm threshold line
    fig.add_hline(y=5.0, line_dash="dash", line_color="#ef4444", annotation_text="G1 Storm Threshold (Kp >= 5.0)")

    fig.update_layout(
        title="🛰️ Real-Time NOAA Geomagnetic Kp Activity (Recent Observations)",
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        yaxis=dict(title="Kp-Index (0-9)", range=[0, 9], gridcolor=PALETTE["grid"]),
        xaxis=dict(title="UTC Timestamp", gridcolor=PALETTE["grid"]),
        margin=dict(l=40, r=40, t=60, b=30),
        height=340
    )
    return fig

def create_soil_moisture_chart(hourly_df: pd.DataFrame, city_name: str) -> go.Figure:
    """Multi-depth Soil Moisture Stratification & Agro-meteorology Chart."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            f"🌱 Multi-Depth Soil Moisture Profile ({city_name})",
            "💧 Evapotranspiration (ET₀) & Vapor Pressure Deficit (VPD)"
        )
    )
    if hourly_df.empty or "time" not in hourly_df.columns:
        return fig

    x = hourly_df["time"]

    # Soil Moisture Layers
    if "soil_moisture_0_to_1cm" in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=hourly_df["soil_moisture_0_to_1cm"], name="Surface Soil (0-1 cm)",
            line=dict(color="#38bdf8", width=2)
        ), row=1, col=1)
    if "soil_moisture_1_to_3cm" in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=hourly_df["soil_moisture_1_to_3cm"], name="Topsoil (1-3 cm)",
            line=dict(color="#10b981", width=2)
        ), row=1, col=1)
    if "soil_moisture_3_to_9cm" in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=hourly_df["soil_moisture_3_to_9cm"], name="Root Zone (3-9 cm)",
            line=dict(color="#f59e0b", width=2)
        ), row=1, col=1)
    if "soil_moisture_9_to_27cm" in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=hourly_df["soil_moisture_9_to_27cm"], name="Subsoil (9-27 cm)",
            line=dict(color="#a855f7", width=2)
        ), row=1, col=1)

    # Row 2: ET0 and VPD
    if "et0_fao_evapotranspiration" in hourly_df.columns:
        fig.add_trace(go.Bar(
            x=x, y=hourly_df["et0_fao_evapotranspiration"], name="Evapotranspiration ET₀ (mm)",
            marker_color="rgba(56, 189, 248, 0.6)"
        ), row=2, col=1)
    if "vapour_pressure_deficit" in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=hourly_df["vapour_pressure_deficit"], name="VPD (kPa)",
            line=dict(color="#ec4899", width=2, dash="dash")
        ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=85, b=30),
        height=580
    )
    fig.update_yaxes(title_text="Moisture (m³/m³)", row=1, col=1, gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="ET₀ (mm) / VPD (kPa)", row=2, col=1, gridcolor=PALETTE["grid"])
    return fig


