import os
import time
import logging

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITIES = [city.strip() for city in os.getenv("CITIES", "").split(",") if city.strip()]

logger.info(f"Loaded {len(CITIES)} cities: {CITIES}")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def fetch_weather_for_city(city: str) -> dict | None:
    """Fetch current weather for a single city, retrying on transient failures.

    Returns the parsed JSON response, or None if the city couldn't be
    fetched after all retries were exhausted.
    """
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                logger.info(f"Fetched weather for {city}")
                return response.json()

            if response.status_code == 401:
                logger.error("Invalid API key (401) - check your .env file. Not retrying.")
                return None

            if response.status_code == 404:
                logger.error(f"City not found (404): {city}. Not retrying.")
                return None

            logger.warning(
                f"Attempt {attempt}/{MAX_RETRIES} for {city} failed "
                f"with status {response.status_code}. Retrying..."
            )

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} for {city} raised {e}. Retrying...")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    logger.error(f"Giving up on {city} after {MAX_RETRIES} attempts.")
    return None


def fetch_all_weather() -> list[dict]:
    """Fetch weather for every configured city, skipping any that fail."""
    results = []
    for city in CITIES:
        data = fetch_weather_for_city(city)
        if data is not None:
            results.append(data)

    logger.info(f"Successfully fetched {len(results)}/{len(CITIES)} cities.")
    return results


if __name__ == "__main__":
    all_data = fetch_all_weather()
    print(f"\nFetched {len(all_data)} cities total.")