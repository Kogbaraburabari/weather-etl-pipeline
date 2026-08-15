from transform import parse_weather_record, transform_weather_data


SAMPLE_RAW_RECORD = {
    "name": "Port Harcourt",
    "sys": {"country": "NG"},
    "main": {"temp": 23.27, "feels_like": 24.13, "humidity": 95},
    "weather": [{"main": "Clouds", "description": "overcast clouds"}],
    "wind": {"speed": 3.01},
    "dt": 1786805605,
}


def test_parse_weather_record_flattens_fields_correctly():
    record = parse_weather_record(SAMPLE_RAW_RECORD)

    assert record["city"] == "Port Harcourt"
    assert record["country"] == "NG"
    assert record["temperature_c"] == 23.27
    assert record["humidity_pct"] == 95
    assert record["weather_condition"] == "Clouds"
    assert record["wind_speed_mps"] == 3.01


def test_parse_weather_record_handles_missing_fields_gracefully():
    incomplete_record = {"name": "Nowhere", "dt": 1786805605}

    record = parse_weather_record(incomplete_record)

    assert record["city"] == "Nowhere"
    assert record["temperature_c"] is None
    assert record["weather_condition"] is None


def test_transform_drops_records_missing_temperature():
    broken_record = {"name": "Ghost City", "dt": 1786805605}  # no "main" -> no temperature

    df = transform_weather_data([SAMPLE_RAW_RECORD, broken_record])

    assert len(df) == 1
    assert df.iloc[0]["city"] == "Port Harcourt"


def test_transform_humidity_is_nullable_integer_dtype():
    df = transform_weather_data([SAMPLE_RAW_RECORD])

    assert df["humidity_pct"].dtype == "Int64"