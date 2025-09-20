from typing import Any

import rasterio as rio
from pystac import Item, ItemCollection
from pystac_client import ItemSearch

from rio_stac_io.drivers.gti import open_gti
from rio_stac_io.drivers.stacit import open_stacit
from rio_stac_io.drivers.stacta import open_stacta


def open(
    items: Item | ItemCollection | ItemSearch,
    asset_key: str,
    use_gti: bool = False,
    merge_collections: bool = False,
    zoom_level: int | None = None,
    **kwargs: Any,
) -> rio.DatasetReader:
    if isinstance(items, Item):
        if any([ext for ext in items.stac_extensions if "tiled-assets" in ext]):
            return open_stacta(items, asset_key, zoom_level=zoom_level, **kwargs)
        else:
            return rio.open(items.assets[asset_key].href)

    if use_gti:
        return open_gti(items, asset_key, **kwargs)

    else:
        return open_stacit(items, asset_key, merge_collections, **kwargs)
