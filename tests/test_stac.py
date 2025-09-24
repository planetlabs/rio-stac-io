import contextlib

import pytest
from pystac import Item

import rio_stac_io as stacio


def test_stac_item(stac_item: Item):
    with stacio.open(stac_item, asset_key="data") as src:
        assert src.driver == "GTiff"
        assert src.bounds == (0, -16, 16, 0)


@pytest.mark.parametrize(
    "mode, allowed", [("r", True), ("rb", False), ("w", False), ("wb", False)]
)
def test_stac_item_mode(mode, allowed, stac_item):
    if not allowed:
        ctx = pytest.raises(ValueError)
    else:
        ctx = contextlib.suppress()

    with ctx:
        stacio.open(stac_item, mode, asset_key="data")  # type:ignore
