import contextlib

import pytest
from pystac import Item
from rasterio.errors import RasterioIOError
from rasterio.windows import from_bounds

import rio_stac_io as stacio


@pytest.mark.parametrize("zoom", [9, 10, None])
@pytest.mark.parametrize("skip", [True, False])
@pytest.mark.parametrize("item_name", ["stacta_item", "stacta_item_raster"])
def test_open_stacta(item_name: str, skip: bool, zoom: int, request):
    stacta_item = request.getfixturevalue(item_name)

    _zoom = zoom or 10

    matrices = stacta_item.properties["tiles:tile_matrix_sets"]["WGS1984Quad"][
        "tileMatrices"
    ]
    res = [matrix["cellSize"] for matrix in matrices if matrix["id"] == str(_zoom)][0]

    with stacio.open(
        stacta_item, asset_key="data", zoom_level=zoom, skip_missing_metatile=skip
    ) as src:
        assert src.profile["driver"] == "STACTA"
        assert src.res[0] == src.res[1] == pytest.approx(res)

        # we must read some data to check
        # if the driver can resolve the path and infer dtype
        bounds = src.bounds
        sub_bounds = (
            bounds[0],
            bounds[1] + (bounds[3] - bounds[1]) / 2,
            bounds[0] + (bounds[2] - bounds[0]) / 2,
            bounds[3],
        )
        window = from_bounds(*sub_bounds, transform=src.transform)
        src.read(1, window=window)


@pytest.mark.parametrize("zoom", [9, 10, None])
@pytest.mark.parametrize("skip", [True, False])
@pytest.mark.parametrize(
    "item_name", ["stacta_item_sparse", "stacta_item_sparse_raster"]
)
def test_open_stacta_sparse(item_name: str, skip: bool, zoom: int, request):
    stacta_item = request.getfixturevalue(item_name)

    _zoom = zoom or 10

    matrices = stacta_item.properties["tiles:tile_matrix_sets"]["WGS1984Quad"][
        "tileMatrices"
    ]
    res = [matrix["cellSize"] for matrix in matrices if matrix["id"] == str(_zoom)][0]

    if not (skip and "raster" in item_name):
        ctx = contextlib.ExitStack()
        ctx.enter_context(pytest.raises(RasterioIOError))
        if skip:
            ctx.enter_context(pytest.warns(UserWarning))

    else:
        ctx = contextlib.suppress()

    with ctx:
        with stacio.open(
            stacta_item, asset_key="data", zoom_level=zoom, skip_missing_metatile=skip
        ) as src:
            assert src.profile["driver"] == "STACTA"
            assert src.res[0] == src.res[1] == pytest.approx(res)

            # we must read some data to check
            # if the driver can resolve the path and infer dtype
            bounds = src.bounds
            sub_bounds = (
                bounds[0],
                bounds[1] + (bounds[3] - bounds[1]) / 2,
                bounds[0] + (bounds[2] - bounds[0]) / 2,
                bounds[3],
            )
            window = from_bounds(*sub_bounds, transform=src.transform)
            src.read(1, window=window)


@pytest.mark.parametrize("zoom", [-1, 12])
def test_open_stacta_wrong_zoom(stacta_item: Item, zoom: int):
    with pytest.raises(ValueError):
        stacio.open(stacta_item, asset_key="data", zoom_level=zoom)
