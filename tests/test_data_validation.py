"""Unit tests for data cleaning, coordinate bounds, and schema validation."""

import numpy as np
import pandas as pd
import pytest

from spatial_justice.cleaning import clean_census_demographics


def test_clean_census_demographics():
    raw_df = pd.DataFrame(
        {
            "GEOID": [17031010100, " 17031010201 ", "17031999900"],
            "B01003_001E": ["3000", "5000", "0"],
            "B01003_001M": ["250", "400", "10"],
            "B17001_001E": ["2800", "4800", "0"],
            "B17001_001M": ["200", "350", "10"],
            "B17001_002E": ["280", "1200", "0"],
            "B17001_002M": ["50", "150", "10"],
            "B19013_001E": ["65000", "-666666666", "0"],  # sentinel in row 1
            "B19013_001M": ["5000", "-666666666", "0"],
        }
    )

    cleaned = clean_census_demographics(raw_df)

    # GEOID formatted as 11 digits
    assert all(len(g) == 11 for g in cleaned["GEOID"])
    assert cleaned["GEOID"].iloc[0] == "17031010100"
    assert cleaned["GEOID"].iloc[1] == "17031010201"

    # Numeric conversions
    assert cleaned["poverty_rate"].iloc[0] == pytest.approx(280 / 2800)
    assert cleaned["poverty_rate"].iloc[1] == pytest.approx(1200 / 4800)
    assert np.isnan(cleaned["poverty_rate"].iloc[2])  # 0 denominator

    # Sentinel value replaced by NaN
    assert np.isnan(cleaned["median_income"].iloc[1])
    assert cleaned["median_income"].iloc[0] == 65000.0

    # Unpopulated flag
    assert not cleaned["is_unpopulated"].iloc[0]
    assert cleaned["is_unpopulated"].iloc[2]


def test_clean_census_demographics_b_greater_than_u():
    # If b > u, it should cap or handle gracefully without crashing
    bad_df = pd.DataFrame(
        {
            "GEOID": ["17031010100"],
            "B01003_001E": ["1000"],
            "B17001_001E": ["500"],
            "B17001_002E": ["800"],  # Error: 800 > 500
            "B19013_001E": ["40000"],
        }
    )
    cleaned = clean_census_demographics(bad_df)
    # Must cap at u so poverty rate does not exceed 1.0
    assert cleaned["poverty_rate"].iloc[0] <= 1.0
