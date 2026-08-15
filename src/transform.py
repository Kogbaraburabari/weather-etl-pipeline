import logging
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)


def parse_weather_record(data: dict) -> dict:
    """Flatten one raw OpenWeather API response into a clean, flat record."""
    weather = data.get("weather", [{}])[0]

    return {
        "city": data.get("name"),
        "country": data.get("sys", {}).get("country"),
        "temperature_c": data.get("main", {}).get("temp"),
        "feels_like_c": data.get("main", {}).get("feels_like"),
        "humidity_pct": data.get("main", {}).get("humidity"),
        "weather_condition": weather.get("main"),
        "weather_description": weather.get("description"),
        "wind_speed_mps": data.get("wind", {}).get("speed"),
        "recorded_at_utc": datetime.fromtimestamp(data.get("dt"), tz=timezone.utc),
    }


def transform_weather_data(raw_records: list[dict]) -> pd.DataFrame:
    """Convert a list of raw OpenWeather API responses into a clean DataFrame."""
    parsed = [parse_weather_record(r) for r in raw_records]
    df = pd.DataFrame(parsed)

    before = len(df)
    df = df.dropna(subset=["city", "temperature_c"])
    dropped = before - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped} record(s) missing critical fields.")

    df["humidity_pct"] = df["humidity_pct"].astype("Int64")

    logger.info(f"Transformed {len(df)} records.")
    return df


if __name__ == "__main__":
    from extract import fetch_all_weather

    raw = fetch_all_weather()
    df = transform_weather_data(raw)
    print(df)