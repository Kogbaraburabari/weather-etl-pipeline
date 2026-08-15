import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "weather.db"
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "weather_latest.csv"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    country TEXT,
    temperature_c REAL,
    feels_like_c REAL,
    humidity_pct INTEGER,
    weather_condition TEXT,
    weather_description TEXT,
    wind_speed_mps REAL,
    recorded_at_utc TEXT NOT NULL,
    UNIQUE(city, recorded_at_utc)
);
"""


def load_to_sqlite(df: pd.DataFrame) -> int:
    """Insert transformed weather records into SQLite, skipping exact duplicates.

    Returns the number of rows actually inserted (excludes skipped duplicates).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(CREATE_TABLE_SQL)

        records = df.copy()
        records["recorded_at_utc"] = records["recorded_at_utc"].astype(str)

        cursor = conn.cursor()
        inserted = 0
        for _, row in records.iterrows():
            cursor.execute(
                """
                INSERT OR IGNORE INTO weather_readings
                (city, country, temperature_c, feels_like_c, humidity_pct,
                 weather_condition, weather_description, wind_speed_mps, recorded_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["city"], row["country"], row["temperature_c"], row["feels_like_c"],
                    int(row["humidity_pct"]) if pd.notna(row["humidity_pct"]) else None,
                    row["weather_condition"], row["weather_description"],
                    row["wind_speed_mps"], row["recorded_at_utc"],
                ),
            )
            inserted += cursor.rowcount

        conn.commit()
        logger.info(f"Inserted {inserted} new row(s) into SQLite ({DB_PATH.name}).")
        return inserted
    finally:
        conn.close()


def export_to_csv(df: pd.DataFrame) -> None:
    """Overwrite a CSV snapshot of the most recent run's data."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    logger.info(f"Exported {len(df)} row(s) to {CSV_PATH.name}.")


if __name__ == "__main__":
    from extract import fetch_all_weather
    from transform import transform_weather_data

    raw = fetch_all_weather()
    df = transform_weather_data(raw)
    load_to_sqlite(df)
    export_to_csv(df)