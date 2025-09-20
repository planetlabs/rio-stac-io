import pytest
from pystac import Item

import rio_stac_io as stacio


@pytest.mark.parametrize("zoom", [9, 10, None])
def test_open_stacta(stacta_item: Item, zoom):
    _zoom = zoom or 10

    matrices = stacta_item.properties["tiles:tile_matrix_sets"]["WGS1984Quad"][
        "tileMatrices"
    ]
    res = [matrix["cellSize"] for matrix in matrices if matrix["id"] == str(_zoom)][0]

    with stacio.open(stacta_item, asset_key="data", zoom_level=zoom) as src:
        assert src.profile["driver"] == "STACTA"
        assert src.res[0] == src.res[1] == pytest.approx(res)


@pytest.mark.parametrize("zoom", [-1, 12])
def test_open_stacta_wrong_zoom(stacta_item: Item, zoom: int):
    with pytest.raises(ValueError):
        stacio.open(stacta_item, asset_key="data", zoom_level=zoom)
