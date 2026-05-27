"""Tests for :mod:`rio_stac_io.utils`."""

from unittest.mock import patch

import pytest
from rasterio.errors import GDALVersionError

from rio_stac_io.utils import (
    gdal_version_blocked,
    is_geodataframe,
    require_gdal_version,
)


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
