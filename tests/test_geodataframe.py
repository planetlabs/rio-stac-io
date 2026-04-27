"""Tests for :func:`rio_stac_io.open` with :class:`geopandas.GeoDataFrame` input.

GeoDataFrame handling tries GTI first, then falls back to STACIT on
``SystemError`` (e.g. no Parquet), :class:`rasterio.errors.GDALVersionError` (GTI
requires GDAL >= 3.10), etc. :class:`ImportError` is not caught. See ``io.open``.

The no-Parquet fallback is exercised with real :class:`rasterio.env.Env` (no
mocking), typically in CI with ``dev-gdal311-noparquet`` where
``libgdal-arrow-parquet`` is not installed. Local runs may still see a Parquet
driver until the env is clean / cache-free.
"""

import pytest
import rasterio as rio
from packaging.version import parse
from rasterio import __gdal_version__
from stac_geoparquet import to_geodataframe

import rio_stac_io as stacio

_GTI_MIN_GDAL = parse("3.10.0")
_GDAL = parse(__gdal_version__)


def _parquet_driver_available() -> bool:
    with rio.Env() as env:
        return bool(env.drivers().get("Parquet"))


@pytest.fixture
def stac_geodataframe(stac_item_collection):
    return to_geodataframe(
        [item.to_dict() for item in stac_item_collection.items],
        add_self_link=True,
    )


@pytest.mark.skipif(
    _GDAL < _GTI_MIN_GDAL,
    reason="GTI requires GDAL >= 3.10.0; older versions use STACIT fallback",
)
@pytest.mark.skipif(
    not _parquet_driver_available(),
    reason="GTI for GeoDataFrame needs the GDAL Parquet driver "
    "(e.g. libgdal-arrow-parquet)",
)
def test_open_geodataframe_uses_gti(stac_geodataframe, stac_item_collection) -> None:
    with stacio.open(stac_geodataframe, asset_key="data") as src:
        assert src.profile["driver"] == "GTI"
        assert len(src.files) == len(stac_item_collection.items)
        # Some GDAL / GTI builds return CRS as None; when set, expect WGS84 + bounds
        if src.crs is not None:
            assert str(src.crs) == "EPSG:4326"
            assert src.bounds == (0, -16, 64, 48)


@pytest.mark.skipif(
    _GDAL >= _GTI_MIN_GDAL,
    reason="Applies to GDAL < 3.10 where GTI raises GDALVersionError",
)
def test_open_geodataframe_falls_back_when_gdal_too_old_for_gti(
    stac_geodataframe, stac_item_collection
) -> None:
    with stacio.open(stac_geodataframe, asset_key="data") as src:
        # Same STACIT presentation as for ItemCollection on this GDAL
        assert src.profile["crs"] == "EPSG:4326"
        assert src.bounds == (0, -16, 64, 48)
        assert len(src.files) == len(stac_item_collection.items)
        assert src.profile["driver"] == "VRT"


@pytest.mark.skipif(
    _GDAL < _GTI_MIN_GDAL,
    reason="GTI is not used below GDAL 3.10 (GDALVersionError, not SystemError)",
)
@pytest.mark.skipif(
    _parquet_driver_available(),
    reason="Requires GDAL without a Parquet driver. Omit libgdal-arrow-parquet in "
    "the conda env (e.g. dev-gdal311-noparquet). May skip locally if the driver "
    "is cached; CI uses a clean install.",
)
def test_open_geodataframe_falls_back_without_parquet_driver(
    stac_geodataframe, stac_item_collection
) -> None:
    """GTI raises SystemError; ``io.open`` falls back to STACIT.
    Uses real rasterio/ GDAL."""

    with stacio.open(stac_geodataframe, asset_key="data") as src:
        assert src.driver == "STACIT"
        assert src.profile["crs"] == "EPSG:4326"
        assert src.bounds == (0, -16, 64, 48)
        assert len(src.files) == len(stac_item_collection.items)
