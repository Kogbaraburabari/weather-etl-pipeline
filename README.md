# Weather ETL Pipeline

An automated ETL (Extract, Transform, Load) pipeline that pulls live weather data for 5 cities across 4 continents via the OpenWeather API, cleans and structures it with Pandas, and persists it to a SQLite database — running on an autonomous 3-hour schedule via GitHub Actions.

Built as part of the AnalystLab Africa Data Analytics Internship (Week 7), extended beyond the base requirements as a standalone portfolio project.

## Why these 5 cities

Port Harcourt, Nairobi, Cairo, London, and New York were chosen deliberately to span tropical, highland, arid, maritime, and continental climates — so a "compare cities" analysis produces a genuinely interesting answer instead of five similar numbers. It worked: on the first real run, **Cairo (desert climate) came out hottest and Port Harcourt (tropical, coastal) came out most humid** — exactly what the climate data would predict, which is a nice sanity check that the pipeline is capturing real signal, not noise.

## How it works

```
OpenWeather API
      │
      ▼
  extract.py    →  fetch_weather_for_city()   (retry logic: 3 attempts, exponential backoff)
      │             fetch_all_weather()        (loops all cities, skips failures gracefully)
      ▼
 transform.py   →  parse_weather_record()      (flattens nested JSON → flat dict)
      │             transform_weather_data()   (builds DataFrame, drops bad rows, fixes dtypes)
      ▼
   load.py      →  load_to_sqlite()            (dedup-safe insert via UNIQUE constraint)
      │             export_to_csv()            (snapshot of latest run)
      ▼
   main.py      →  run_pipeline()               (orchestrates all three + logs comparison summary)
```

`main.py` is the single entry point — it's what both a human running this locally and the GitHub Actions workflow call to execute a full run.

## Data source

[OpenWeather Current Weather Data API](https://openweathermap.org/current) — free tier, capped at 60 calls/minute and ~1,000,000 calls/month. The underlying weather data itself only refreshes roughly every 10 minutes, which is why the automated schedule runs every 3 hours rather than more frequently — there's no benefit to polling faster than the source data changes.

## Tech stack

- **Python 3** — `requests`, `pandas`, `python-dotenv`, `pytest`
- **SQLite** — persistent storage, queryable directly with SQL
- **GitHub Actions** — scheduled automation (cron) + manual trigger support
- **pytest** — unit tests on the transform logic

## Project structure

```
weather-etl-pipeline/
├── .github/workflows/
│   └── etl_schedule.yml     # runs main.py every 3 hours, commits fresh data back
├── src/
│   ├── extract.py           # API calls with retry logic + structured logging
│   ├── transform.py         # JSON → clean DataFrame
│   ├── load.py               # writes to SQLite (dedup-safe) + CSV export
│   └── main.py                # orchestrates the pipeline + logs a comparison summary
├── tests/
│   └── test_transform.py    # unit tests on the cleaning logic
├── data/
│   ├── weather.db            # SQLite database, growing with every automated run
│   └── weather_latest.csv    # snapshot of the most recent run
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Design decisions worth knowing about

**SQLite over a plain CSV.** A CSV can't be queried and can't safely handle repeated appends without risking duplicate rows. SQLite gives real SQL access to the pipeline's own output and, combined with a `UNIQUE(city, recorded_at_utc)` constraint and `INSERT OR IGNORE`, guarantees that if the pipeline ever runs twice on the same data, duplicates are silently skipped instead of corrupting the historical record. (Verified directly: running the pipeline twice within the same OpenWeather refresh window correctly inserted only the cities whose underlying data had actually changed, and skipped the rest.)

**Retry logic distinguishes retryable from non-retryable failures.** A `401` (bad API key) or `404` (city not found) won't fix itself no matter how many times it's retried, so those fail immediately. Transient issues — timeouts, `429` rate limits, `5xx` server errors — get up to 3 attempts with increasing backoff (5s, then 10s).

**Structured logging instead of `print()`.** Once this runs unattended on a schedule, `print()` output has nowhere to go. Every run's logs — including successes, retries, and failures — are visible in GitHub Actions' run history, which is also what makes the automation independently verifiable rather than something you have to take my word for.

**UTC timestamps, not local time.** The 5 tracked cities span 4+ time zones; storing everything on one absolute timeline is what makes cross-city comparisons actually correct.

## Automation

A GitHub Actions workflow (`.github/workflows/etl_schedule.yml`) runs `src/main.py` every 3 hours, using a repository secret for the API key, and commits any new data straight back into the repo — so the commit history itself is a running, timestamped log of the pipeline executing unattended in the cloud. It can also be triggered manually from the **Actions** tab for on-demand runs.

## Running it locally

```bash
git clone https://github.com/Kogbaraburabari/weather-etl-pipeline.git
cd weather-etl-pipeline
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
cp .env.example .env              # then add your own OpenWeather API key
python src/main.py
```

## Testing

```bash
python -m pytest -v
```

4 tests cover the transform logic: field-flattening correctness, graceful handling of missing fields, dropping of invalid records, and correct (nullable) dtype handling for humidity.

## Key findings (first live run)

- **Hottest:** Cairo, 35.42°C
- **Coldest:** Nairobi, 21.98°C
- **Most humid:** Port Harcourt, 95%
- Weather conditions split cleanly along climate lines: Cairo and New York both showed clear skies, while Port Harcourt, Nairobi, and London all showed cloud cover — consistent with each city's typical climate profile at the time of the run.

## What I'd do next in production

This is intentionally scoped as a lightweight pipeline, not a production data platform. If this were going into real production use, the next steps would be:

- **Orchestration:** replace the GitHub Actions cron with Airflow or Dagster for retry policies, backfills, and dependency graphs across multiple pipelines.
- **Storage:** move from SQLite to a managed warehouse (Postgres, BigQuery, or Snowflake) once data volume or concurrent access needs grow past what a single-file database handles well.
- **Alerting:** a Slack or email webhook on pipeline failure, rather than relying on someone checking the Actions tab.
- **Data quality checks:** automated validation (e.g. Great Expectations) to catch schema drift or anomalous values before they land in the database, not just missing-field handling.
- **Secrets rotation:** periodic API key rotation rather than a long-lived static key.

## Author

Burabari Kogbara — [GitHub](https://github.com/Kogbaraburabari)

Built as part of the AnalystLab Africa Data Analytics Internship.
