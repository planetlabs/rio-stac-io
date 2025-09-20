import pytest
import rasterio as rio
from packaging.version import parse
from pystac_client import Client
from rasterio import __gdal_version__

import rio_stac_io as stacio


@pytest.mark.skipif(
    parse(__gdal_version__) < parse("3.10.0"),
    reason="Using GTI driver requires GDAL >= 3.10.0",
)
def test_stacit_driver_vrt(stac_item_collection):
    with stacio.open(stac_item_collection, asset_key="data") as src:
        src.driver = "VRT"


@pytest.mark.skipif(
    parse(__gdal_version__) >= parse("3.10.0"),
    reason="Using GTI driver requires GDAL >= 3.10.0",
)
def test_stacit_driver_stacit(stac_item_collection):
    with stacio.open(stac_item_collection, asset_key="data") as src:
        src.driver = "STACIT"


@pytest.mark.parametrize(
    "item_collection_name,crs,bounds",
    [
        ("stac_item_collection", "EPSG:4326", (0, -16, 64, 48)),
        ("stac_item_collection_proj", "EPSG:6933", (0, -160000, 640000, 480000)),
    ],
)
def test_open_stacit(item_collection_name, crs, bounds, request):
    item_collection = request.getfixturevalue(item_collection_name)

    with stacio.open(item_collection, asset_key="data") as src:
        assert src.profile["crs"] == crs
        assert src.bounds == bounds
        assert len(src.files) == len(item_collection.items)


@pytest.mark.parametrize(
    "item_collection_name,crs,bounds",
    [
        (
            "stac_item_collection_multi_collection",
            ["EPSG:4326", "EPSG:4326", "EPSG:4326", "EPSG:4326"],
            [(0, -16, 16, 0), (16, 0, 32, 16), (32, 16, 48, 32), (48, 32, 64, 48)],
        ),
        (
            "stac_item_collection_multi_proj",
            ["EPSG:5676", "EPSG:5677", "EPSG:5678", "EPSG:5679"],
            [
                (2500000.0, 5840000.0, 2660000.0, 6000000.0),
                (3500000.0, 5840000.0, 3660000.0, 6000000.0),
                (4500000.0, 5840000.0, 4660000.0, 6000000.0),
                (5500000.0, 5840000.0, 5660000.0, 6000000.0),
            ],
        ),
    ],
)
def test_open_stacit_subdatasets(item_collection_name, crs, bounds, request):
    item_collection = request.getfixturevalue(item_collection_name)

    with stacio.open(item_collection, asset_key="data") as src:
        assert len(src.subdatasets) == len(item_collection.items)

        for i, subdataset in enumerate(src.subdatasets):
            with rio.open(subdataset) as subsrc:
                assert subsrc.profile["crs"] == crs[i]
                assert subsrc.bounds == bounds[i]
                assert len(subsrc.files) == 1


@pytest.mark.parametrize("merge_collections", [True, False])
def test_open_stacit_merge_subdatasets(
    stac_item_collection_multi_collection, merge_collections
):
    with stacio.open(
        stac_item_collection_multi_collection,
        asset_key="data",
        merge_collections=merge_collections,
    ) as src:
        assert src.subdatasets is not merge_collections


@pytest.mark.vcr
def test_open_stacit_search():
    client = Client.open("https://earth-search.aws.element84.com/v1/")
    search = client.search(collections=["cop-dem-glo-30"], bbox=[10, 10, 20, 20])
    expected_bounds = [
        9.99986111111111,
        9.00013888888891,
        20.999861111111084,
        20.000138888888888,
    ]

    with stacio.open(search, "data") as src:
        assert len(src.files) == 121
        for i, val in enumerate(src.bounds):
            assert val == pytest.approx(expected_bounds[i]), (
                f"Source bounds: {src.bounds}, expected bounds {expected_bounds}"
            )


@pytest.mark.parametrize(
    "overlap_strategy, expected",
    [("USE_ALL", 4), ("REMOVE_IF_NO_NODATA​", 4), ("USE_MOST_RECENT", 2)],
)
def test_open_stacit_overlap(stac_item_collection_overlap, overlap_strategy, expected):
    # Driver changed in version 3.9.1 and introduced the USE_ALL option
    if parse(__gdal_version__) < parse("3.9.1"):
        expected = 2

    bounds = [0, -16, 16, 16]

    with stacio.open(
        stac_item_collection_overlap, "data", overlap_strategy=overlap_strategy
    ) as src:
        assert src.profile["crs"] == "EPSG:4326"
        for i, val in enumerate(src.bounds):
            assert val == pytest.approx(bounds[i]), (
                f"Source bounds: {src.bounds}, expected bounds {bounds}"
            )
        assert len(src.files) == expected
