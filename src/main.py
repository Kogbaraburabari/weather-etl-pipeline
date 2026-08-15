import logging

from extract import fetch_all_weather
from transform import transform_weather_data
from load import load_to_sqlite, export_to_csv

logger = logging.getLogger(__name__)


def summarize(df) -> None:
    """Log a short comparative summary across today's fetched cities."""
    hottest = df.loc[df["temperature_c"].idxmax()]
    coldest = df.loc[df["temperature_c"].idxmin()]
    most_humid = df.loc[df["humidity_pct"].idxmax()]

    logger.info(
        f"Hottest: {hottest['city']} ({hottest['temperature_c']}°C) | "
        f"Coldest: {coldest['city']} ({coldest['temperature_c']}°C) | "
        f"Most humid: {most_humid['city']} ({most_humid['humidity_pct']}%)"
    )

    conditions = df.groupby("weather_condition")["city"].apply(list).to_dict()
    for condition, cities in conditions.items():
        logger.info(f"{condition}: {', '.join(cities)}")


def run_pipeline() -> None:
    """Run the full Extract -> Transform -> Load pipeline once."""
    raw = fetch_all_weather()
    if not raw:
        logger.error("No data fetched for any city. Aborting run.")
        return

    df = transform_weather_data(raw)
    load_to_sqlite(df)
    export_to_csv(df)
    summarize(df)


if __name__ == "__main__":
    run_pipeline()