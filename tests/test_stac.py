import rio_stac_io as stacio


def test_stac_item(stac_item):
    with stacio.open(stac_item, "data") as src:
        assert src.driver == "GTiff"
        assert src.bounds == (0, -16, 16, 0)
