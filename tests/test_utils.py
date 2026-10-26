"""Tests for :mod:`rio_stac_io.utils`."""

from itertools import pairwise
from unittest.mock import patch

import pytest
from rasterio.errors import GDALVersionError

from rio_stac_io.utils import (
    gdal_version_blocked,
    is_geodataframe,
    parse_version,
    require_gdal_version,
)

_ORDERED_VERSIONS = [
    "3.9.1",
    "3.10.0.dev0",
    "3.10.0dev",
    "3.10.0dev1",
    "3.10.0a1",
    "3.10.0alpha2",
    "3.10.0b1.dev0",
    "3.10.0b1",
    "3.10.0beta2",
    "3.10.0rc1",
    "3.10.0-rc2",
    "3.10.0",
    "3.10.1",
    "3.10.10",
    "3.11.0dev",
    "3.11",
    "4.0.0",
]


@pytest.mark.parametrize(("lower", "higher"), list(pairwise(_ORDERED_VERSIONS)))
def test_parse_version_order(lower: str, higher: str) -> None:
    assert parse_version(lower) <= parse_version(higher)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("3.10", "3.10.0"),
        ("3.10.0.0", "3.10.0"),
        ("3.10.0dev", "3.10.0.dev0"),
        ("3.10.0RC1", "3.10.0rc1"),
        ("3.10.0c1", "3.10.0rc1"),
        ("3.10.0pre1", "3.10.0rc1"),
        ("3.10.0preview1", "3.10.0rc1"),
        ("3.10.0-abc123", "3.10.0"),
        ("3.10.0+local", "3.10.0"),
        ("v3.10.0", "3.10.0"),
        (" 3.10.0\n", "3.10.0"),
        ("3.11.0dev-5bf4e8ac5f", "3.11.0dev"),
    ],
)
def test_parse_version_equal(left: str, right: str) -> None:
    assert parse_version(left) == parse_version(right)


@pytest.mark.parametrize("version", ["", "dev", "3.10.0foo", "3..10", "a3.10"])
def test_parse_version_invalid(version: str) -> None:
    with pytest.raises(ValueError, match="Invalid version"):
        parse_version(version)


def test_parse_version_matches_packaging() -> None:
    pv = pytest.importorskip("packaging.version")
    for left in _ORDERED_VERSIONS:
        for right in _ORDERED_VERSIONS:
            ours = parse_version(left) < parse_version(right)
            assert ours == (pv.parse(left) < pv.parse(right)), (left, right)


def test_gdal_version_blocked() -> None:
    assert gdal_version_blocked("3.12.2", ["3.12.2", "3.12.3"])
    assert not gdal_version_blocked("3.13.0", ["3.12.2", "3.12.3"])


@require_gdal_version("3.10.0", exclude=["3.12.2", "3.12.3"])
def _stub() -> str:
    return "ok"


def test_require_gdal_version_exclude() -> None:
    with patch("rio_stac_io.utils.__gdal_version__", "3.12.1"):
        assert _stub() == "ok"

    with patch("rio_stac_io.utils.__gdal_version__", "3.12.2"):
        with pytest.raises(GDALVersionError, match="excluded"):
            _stub()

    with patch("rio_stac_io.utils.__gdal_version__", "3.9.0"):
        with pytest.raises(GDALVersionError, match="3.10.0 or higher"):
            _stub()


def test_is_geodataframe_real() -> None:
    """A real GeoDataFrame is recognized; a plain DataFrame is not."""
    pd = pytest.importorskip("pandas")
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.GeoDataFrame({"a": [1]}, geometry=gpd.points_from_xy([0], [0]))
    assert is_geodataframe(gdf)

    df = pd.DataFrame({"a": [1]})
    assert not is_geodataframe(df)


def test_is_geodataframe_subclass() -> None:
    """A subclass of GeoDataFrame is also accepted."""
    gpd = pytest.importorskip("geopandas")

    class MyGDF(gpd.GeoDataFrame):
        pass

    gdf = MyGDF({"a": [1]}, geometry=gpd.points_from_xy([0], [0]))
    assert is_geodataframe(gdf)


def test_is_geodataframe_lookalike_rejected() -> None:
    """A duck-typed look-alike from another module is not accepted."""

    class GeoDataFrame:
        pass

    assert not is_geodataframe(GeoDataFrame())


def test_is_geodataframe_non_dataframe_inputs() -> None:
    assert not is_geodataframe(None)
    assert not is_geodataframe(42)
    assert not is_geodataframe("GeoDataFrame")
    assert not is_geodataframe({"a": 1})
