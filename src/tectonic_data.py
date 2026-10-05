"""Tectonic Plate Boundaries, Fault Lines, and Crustal Plates Geometry Data."""

from typing import Dict, List, Any

# Simplified Global Tectonic Plate Boundaries Coordinates [lon, lat]
TECTONIC_PLATES: Dict[str, List[List[float]]] = {
    "Pacific Plate (Ring of Fire)": [
        [-122.4, 37.8], [-124.0, 40.0], [-130.0, 50.0], [-150.0, 58.0], [-170.0, 60.0],
        [180.0, 55.0], [160.0, 50.0], [145.0, 40.0], [140.0, 35.0], [130.0, 20.0],
        [125.0, 10.0], [130.0, 0.0], [140.0, -10.0], [150.0, -15.0], [170.0, -20.0],
        [178.0, -35.0], [175.0, -45.0], [160.0, -55.0], [-140.0, -60.0], [-110.0, -55.0],
        [-90.0, -30.0], [-80.0, -10.0], [-85.0, 5.0], [-105.0, 20.0], [-115.0, 30.0], [-122.4, 37.8]
    ],
    "Eurasian Plate Boundary": [
        [-20.0, 65.0], [0.0, 70.0], [40.0, 75.0], [100.0, 75.0], [170.0, 70.0],
        [160.0, 55.0], [145.0, 45.0], [135.0, 35.0], [120.0, 25.0], [100.0, 20.0],
        [85.0, 28.0], [65.0, 30.0], [45.0, 38.0], [30.0, 40.0], [15.0, 38.0],
        [-5.0, 36.0], [-15.0, 35.0], [-25.0, 40.0], [-20.0, 65.0]
    ],
    "African Plate (East African Rift)": [
        [-15.0, 35.0], [0.0, 37.0], [20.0, 35.0], [35.0, 30.0], [40.0, 15.0],
        [50.0, 12.0], [55.0, 0.0], [45.0, -15.0], [40.0, -30.0], [30.0, -45.0],
        [10.0, -40.0], [-5.0, -30.0], [-15.0, -10.0], [-20.0, 5.0], [-20.0, 20.0], [-15.0, 35.0]
    ],
    "North American Plate": [
        [-170.0, 60.0], [-140.0, 70.0], [-90.0, 75.0], [-40.0, 70.0], [-20.0, 65.0],
        [-30.0, 45.0], [-40.0, 30.0], [-60.0, 20.0], [-80.0, 18.0], [-95.0, 16.0],
        [-105.0, 20.0], [-115.0, 30.0], [-125.0, 40.0], [-140.0, 55.0], [-170.0, 60.0]
    ],
    "South American Plate & Nazca Boundary (Andes)": [
        [-80.0, 10.0], [-50.0, 8.0], [-35.0, -5.0], [-35.0, -25.0], [-50.0, -50.0],
        [-70.0, -55.0], [-75.0, -45.0], [-72.0, -30.0], [-75.0, -15.0], [-80.0, 0.0], [-80.0, 10.0]
    ],
    "Indo-Australian Plate": [
        [65.0, 25.0], [80.0, 10.0], [95.0, -5.0], [115.0, -10.0], [130.0, -10.0],
        [150.0, -15.0], [165.0, -30.0], [160.0, -50.0], [110.0, -50.0], [75.0, -40.0],
        [60.0, -20.0], [60.0, 10.0], [65.0, 25.0]
    ],
    "Mid-Atlantic Ridge": [
        [-20.0, 70.0], [-22.0, 55.0], [-30.0, 40.0], [-40.0, 25.0], [-35.0, 10.0],
        [-25.0, 0.0], [-15.0, -15.0], [-12.0, -35.0], [-15.0, -50.0], [-20.0, -60.0]
    ],
    "Arabian Plate Boundary": [
        [35.0, 30.0], [40.0, 38.0], [55.0, 30.0], [60.0, 22.0], [55.0, 14.0],
        [45.0, 12.0], [40.0, 15.0], [35.0, 30.0]
    ]
}

def identify_tectonic_plate(lat: float, lon: float) -> str:
    """Identify the approximate tectonic plate for given coordinates."""
    if lat > 20 and -20 <= lon <= 180 and lat <= 80:
        if 12 <= lat <= 38 and 35 <= lon <= 60:
            return "Arabian Plate 🏜️"
        if -10 <= lat <= 35 and 65 <= lon <= 100:
            return "Indian Plate 🇮🇳"
        return "Eurasian Plate 🌍"
    elif -40 <= lat <= 38 and -20 <= lon <= 55:
        return "African Plate 🌍 (Nubian/Somalian Plates)"
    elif lat >= 15 and -170 <= lon <= -30:
        return "North American Plate 🌎"
    elif lat < 15 and -90 <= lon <= -30:
        return "South American Plate 🌎"
    elif -60 <= lat <= 15 and 90 <= lon <= 180:
        return "Australian / Indo-Australian Plate 🌏"
    elif -50 <= lat <= 60 and (lon >= 130 or lon <= -90):
        return "Pacific Plate (Pacific Ring of Fire 🔥)"
    elif -60 <= lat <= 10 and -110 <= lon <= -70:
        return "Nazca Plate (Andes Subduction Zone 🏔️)"
    else:
        return "Major Crustal Plate Boundary / Oceanic Basin"
