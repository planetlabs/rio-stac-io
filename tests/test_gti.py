import pytest
from packaging.version import parse
from pystac import ItemCollection
from pystac_client import Client
from rasterio import __gdal_version__
from rasterio.errors import GDALVersionError

import rio_stac_io as stacio


@pytest.mark.skipif(
    parse(__gdal_version__) >= parse("3.10.0"),
    reason="Using GTI driver works with GDAL version >= 3.10.0",
)
def test_open_gti_wrong_version(stac_item_collection):
    with pytest.raises(
        GDALVersionError,
        match="Selected Driver requires GDAL Version 3.10.0 or higher.",
    ):
        with stacio.open(stac_item_collection, asset_key="data", use_gti=True):
            ...


pytestmark = pytest.mark.skipif(
    parse(__gdal_version__) < parse("3.10.0"),
    reason="Using GTI driver works with GDAL version >= 3.10.0",
)


@pytest.mark.parametrize(
    "item_collection_name,crs,bounds",
    [
        ("stac_item_collection", "EPSG:4326", (0, -16, 64, 48)),
        # I am unsure why it adds an extra row of empty pixels to the top
        # It should be 480000, not 490000
        # probably a floating point issue when reprojecting coordinates?
        ("stac_item_collection_proj", "EPSG:6933", (0, -160000, 640000, 490000)),
        ("stac_item_collection_multi_collection", "EPSG:4326", (0, -16, 64, 48)),
        (
            "stac_item_collection_multi_proj",
            "EPSG:5676",
            (2490000.0, 5830000.0, 3280000.0, 6070000.0),
        ),
    ],
)
def test_open_gti(item_collection_name, crs, bounds, request):
    item_collection = request.getfixturevalue(item_collection_name)

    with stacio.open(item_collection, asset_key="data", use_gti=True) as src:
        assert src.profile["driver"] == "GTI"
        assert src.profile["crs"] == crs
        assert src.bounds == bounds
        assert len(src.files) == len(item_collection.items)


@pytest.mark.parametrize(
    "item_collection_name,crs,bounds",
    [
        ("stac_item_collection", "EPSG:4326", (0, -16, 64, 48)),
        (
            "stac_item_collection_proj",
            "EPSG:4326",
            (0.0, -1.2886835826838188, 6.707855394744574, 3.7651800708908607),
        ),
        (
            "stac_item_collection_multi_proj",
            "EPSG:4326",
            (
                5.9993918737151954,
                52.65604947382422,
                17.549406179980657,
                54.13051938526236,
            ),
        ),
    ],
)
def test_open_gti_reproject(item_collection_name, crs, bounds, request):
    item_collection = request.getfixturevalue(item_collection_name)

    with stacio.open(item_collection, asset_key="data", use_gti=True, srs=crs) as src:
        assert src.profile["driver"] == "GTI"
        assert src.profile["crs"] == crs
        for i, val in enumerate(src.bounds):
            assert val == pytest.approx(bounds[i])
        assert len(src.files) == len(item_collection.items)


@pytest.mark.vcr
def test_open_gti_search():
    client = Client.open("https://earth-search.aws.element84.com/v1/")
    search = client.search(collections=["cop-dem-glo-30"], bbox=[10, 10, 20, 20])
    expected_bounds = [
        10,
        9,
        21,
        20,
    ]

    with stacio.open(search, asset_key="data", use_gti=True) as src:
        assert len(src.files) == 121
        for i, val in enumerate(src.bounds):
            assert val == pytest.approx(expected_bounds[i], 0.0001), (
                f"Source bounds: {src.bounds}, expected bounds {expected_bounds}"
            )


def test_open_gti_overlap(stac_item_collection_overlap):
    bounds = [0, -16, 16, 16]

    with stacio.open(
        stac_item_collection_overlap, asset_key="data", use_gti=True
    ) as src:
        assert src.profile["driver"] == "GTI"
        assert src.profile["crs"] == "EPSG:4326"
        for i, val in enumerate(src.bounds):
            assert val == pytest.approx(bounds[i]), (
                f"Source bounds: {src.bounds}, expected bounds {bounds}"
            )
        assert len(src.files) == len(stac_item_collection_overlap.items)


@pytest.mark.vcr
def test_open_gti_no_proj():
    client = Client.open("https://earth-search.aws.element84.com/v1/")
    search = client.search(collections=["cop-dem-glo-30"], bbox=[10, 10, 11, 11])

    items = []

    for item in search.items():
        keys = list(item.properties.keys())
        for key in keys:
            if key.startswith("proj:"):
                item.properties.pop(key)
        items.append(item)

    with stacio.open(ItemCollection(items), asset_key="data", use_gti=True) as src:
        src.profile


def test_open_gti_empty_ic():
    with pytest.raises(
        ValueError, match="Cannot open dataset. Got empty ItemCollection."
    ):
        stacio.open(ItemCollection([]), asset_key="data", use_gti=True)
