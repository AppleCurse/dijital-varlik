"""
Weather Bridge — Open-Meteo (ücretsiz, API keysiz).

Gerçek zamanlı hava durumu: sıcaklık, rüzgar, gün doğumu/batımı.
5 dakika önbellek.

Kullanim:
    from mudahale.weather_bridge import get_weather
    w = get_weather()
    w.get(41.0082, 28.9784)  # Istanbul
"""
import time, requests
from typing import Optional

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
_cache = {}
CACHE_TTL = 300  # 5 dakika


class WeatherBridge:
    """Open-Meteo hava durumu."""

    def __init__(self):
        self._ready = True

    def hazir_mi(self) -> bool:
        return self._ready

    def get(self, lat: float, lon: float) -> dict:
        """Konuma gore hava durumu. Istanbul: 41.0, 29.0"""
        key = (round(lat, 1), round(lon, 1))
        if key in _cache and time.time() - _cache[key]["ts"] < CACHE_TTL:
            return {"status": "ok", "cached": True, "data": _cache[key]["data"]}

        try:
            r = requests.get(OPEN_METEO, params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m",
                "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
                "timezone": "auto"
            }, timeout=10)
            data = r.json()
            current = data.get("current", {})
            daily = data.get("daily", {})

            # Hava durumu kodu → metin
            codes = {0: "Açık", 1: "Az bulutlu", 2: "Parçalı bulutlu", 3: "Kapalı",
                     45: "Sisli", 51: "Çiseleme", 61: "Yağmurlu", 71: "Karlı", 95: "Fırtınalı"}
            code = current.get("weather_code", 0)
            weather_text = codes.get(code, f"Kod:{code}")

            result = {
                "temperature": current.get("temperature_2m", "?"),
                "feels_like": current.get("apparent_temperature", "?"),
                "humidity": current.get("relative_humidity_2m", "?"),
                "wind_speed": current.get("wind_speed_10m", "?"),
                "weather": weather_text,
                "weather_code": code,
            }
            if daily:
                result["temp_max"] = daily.get("temperature_2m_max", [0])[0] if daily.get("temperature_2m_max") else "?"
                result["temp_min"] = daily.get("temperature_2m_min", [0])[0] if daily.get("temperature_2m_min") else "?"
                result["sunrise"] = daily.get("sunrise", ["?"])[0] if daily.get("sunrise") else "?"
                result["sunset"] = daily.get("sunset", ["?"])[0] if daily.get("sunset") else "?"

            _cache[key] = {"ts": time.time(), "data": result}
            return {"status": "ok", "cached": False, "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def city(self, name: str) -> dict:
        """Sehir ismiyle hava durumu. Istanbul, Ankara, Izmir..."""
        cities = {
            "istanbul": (41.0, 29.0), "ankara": (39.9, 32.8), "izmir": (38.4, 27.1),
            "bursa": (40.2, 29.1), "antalya": (36.9, 30.7), "adana": (37.0, 35.3),
            "konya": (37.9, 32.5), "gaziantep": (37.1, 37.4), "mersin": (36.8, 34.6),
            "diyarbakir": (37.9, 40.2), "samsun": (41.3, 36.3), "trabzon": (41.0, 39.7),
            "erzurum": (39.9, 41.3), "london": (51.5, -0.1), "new york": (40.7, -74.0),
            "paris": (48.9, 2.3), "berlin": (52.5, 13.4), "tokyo": (35.7, 139.7),
        }
        n = name.lower().strip()
        if n in cities:
            return self.get(*cities[n])
        return {"status": "error", "message": f"Sehir bulunamadi: {name}. Bilinen: {list(cities.keys())[:10]}"}


_weather: Optional[WeatherBridge] = None

def get_weather() -> WeatherBridge:
    global _weather
    if _weather is None: _weather = WeatherBridge()
    return _weather
