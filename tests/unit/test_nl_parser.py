"""
Unit tests for the NL parser (pure function — no DB required).
"""

from __future__ import annotations

import pytest

from app.nl_parser.parser import UninterpretableQueryError, parse_query


class TestGenderParsing:
    def test_male_keyword(self):
        result = parse_query("male people")
        assert result["gender"] == "male"

    def test_males_keyword(self):
        result = parse_query("show me males")
        assert result["gender"] == "male"

    def test_female_keyword(self):
        result = parse_query("female profiles")
        assert result["gender"] == "female"

    def test_females_keyword(self):
        result = parse_query("all females")
        assert result["gender"] == "female"

    def test_male_and_female_omits_gender(self):
        result = parse_query("male and female teenagers")
        assert "gender" not in result

    def test_male_female_together_omits_gender(self):
        result = parse_query("male and female above 17")
        assert "gender" not in result


class TestYoungKeyword:
    def test_young_maps_to_16_24(self):
        result = parse_query("young people")
        assert result["min_age"] == 16
        assert result["max_age"] == 24

    def test_young_males(self):
        result = parse_query("young males")
        assert result["gender"] == "male"
        assert result["min_age"] == 16
        assert result["max_age"] == 24


class TestAgeComparisons:
    def test_above_n(self):
        result = parse_query("females above 30")
        assert result["min_age"] == 30

    def test_below_n(self):
        result = parse_query("people below 18")
        assert result["max_age"] == 18

    def test_over_n(self):
        result = parse_query("males over 40")
        assert result["min_age"] == 40

    def test_under_n(self):
        result = parse_query("females under 25")
        assert result["max_age"] == 25

    def test_older_than_n(self):
        result = parse_query("older than 50")
        assert result["min_age"] == 50

    def test_younger_than_n(self):
        result = parse_query("younger than 30")
        assert result["max_age"] == 30


class TestAgeGroupParsing:
    def test_child(self):
        assert parse_query("child profiles")["age_group"] == "child"

    def test_children(self):
        assert parse_query("children from nigeria")["age_group"] == "child"

    def test_teenager(self):
        assert parse_query("teenager")["age_group"] == "teenager"

    def test_teenagers(self):
        assert parse_query("teenagers above 17")["age_group"] == "teenager"

    def test_teen(self):
        assert parse_query("teen males")["age_group"] == "teenager"

    def test_adult(self):
        assert parse_query("adult females")["age_group"] == "adult"

    def test_adults(self):
        assert parse_query("adults from kenya")["age_group"] == "adult"

    def test_senior(self):
        assert parse_query("senior people")["age_group"] == "senior"

    def test_seniors(self):
        assert parse_query("seniors from ghana")["age_group"] == "senior"

    def test_elderly(self):
        assert parse_query("elderly people")["age_group"] == "senior"


class TestCountryParsing:
    def test_from_nigeria(self):
        result = parse_query("people from nigeria")
        assert result["country_id"] == "NG"

    def test_from_kenya(self):
        result = parse_query("adults from kenya")
        assert result["country_id"] == "KE"

    def test_from_angola(self):
        result = parse_query("people from angola")
        assert result["country_id"] == "AO"

    def test_from_south_africa(self):
        result = parse_query("females from south africa")
        assert result["country_id"] == "ZA"

    def test_from_united_states(self):
        result = parse_query("people from united states")
        assert result["country_id"] == "US"

    def test_unknown_country_ignored(self):
        # Unknown country should not add country_id but other filters still work
        result = parse_query("males from atlantis")
        assert "country_id" not in result
        assert result["gender"] == "male"


class TestMultiKeyword:
    def test_adult_males_from_kenya(self):
        result = parse_query("adult males from kenya")
        assert result["gender"] == "male"
        assert result["age_group"] == "adult"
        assert result["country_id"] == "KE"

    def test_male_and_female_teenagers_above_17(self):
        result = parse_query("male and female teenagers above 17")
        assert "gender" not in result
        assert result["age_group"] == "teenager"
        assert result["min_age"] == 17

    def test_young_females_from_nigeria(self):
        result = parse_query("young females from nigeria")
        assert result["gender"] == "female"
        assert result["min_age"] == 16
        assert result["max_age"] == 24
        assert result["country_id"] == "NG"


class TestErrorCases:
    def test_empty_string_raises(self):
        with pytest.raises(UninterpretableQueryError):
            parse_query("")

    def test_whitespace_only_raises(self):
        with pytest.raises(UninterpretableQueryError):
            parse_query("   ")

    def test_unrecognised_query_raises(self):
        with pytest.raises(UninterpretableQueryError):
            parse_query("xyzzy foobar baz")

    def test_numbers_only_raises(self):
        with pytest.raises(UninterpretableQueryError):
            parse_query("12345")
