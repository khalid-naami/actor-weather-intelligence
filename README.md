# Global Weather, Marine & Earth Intelligence Apify Actor 🌦️

Comprehensive meteorology, atmospheric science, and planetary geophysics Actor powered by Open-Meteo, USGS, and NOAA public APIs.

## Features
- **Accurate Hyper-Local Meteorology:** Real-time temperature, apparent feels-like, humidity, wind gusts, UV index, and precipitation.
- **Up to 16-Day Forecasts:** Daily high/low temps, precipitation probability, and weather codes.
- **Air Quality & Pollution (AQI):** PM2.5, PM10, Nitrogen Dioxide, Ozone, and European AQI scale.
- **Marine & Ocean State:** Significant wave height, wave period, swell direction.
- **Space Weather & Geomagnetics:** NOAA solar flare activity, radio blackout risks, planetary Kp-index.
- **Crustal Geophysics:** Tectonic plate boundary identification and live USGS seismic earthquake events.

## Input Example
```json
{
  "locations": ["Casablanca", "Paris", "Tokyo", "New York"],
  "forecastDays": 7,
  "includeAirQuality": true,
  "includeMarineWeather": true,
  "includeSpaceWeather": true,
  "includeEarthquakes": true
}
```
