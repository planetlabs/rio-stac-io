import warnings
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Literal

import rasterio as rio
from packaging.version import parse
from pystac import Asset, Item, ItemCollection
from pystac_client import ItemSearch
from rasterio.env import GDALVersion

from rio_stac_io.utils import vsi_href


def rewrite_item(
    item: Item, asset_key: str, merge_collections: bool, gdal_version: str
) -> Item:
    item = Item(
        id=item.id,
        geometry=item.geometry,
        bbox=item.bbox,
        datetime=item.datetime,
        properties=item.properties,
        stac_extensions=item.stac_extensions,
        collection=None if merge_collections else item.collection_id,
        assets={
            asset_key: Asset(
                vsi_href(item.assets[asset_key].href),
                extra_fields=item.assets[asset_key].extra_fields,
            )
        },
    )
    # STACIT driver only starts supporting STAC v1.1.0 starting in GDAL v3.10.2
    # For lower versions, we need to substitute the `proj:code` property
    # with the now deprecated `proj:epsg`` property
    if parse(gdal_version) < parse("3.10.2"):
        if "proj:code" in item.properties:
            item.properties["proj:epsg"] = int(
                item.properties["proj:code"].replace("EPSG:", "")
            )

        if "proj:code" in item.assets[asset_key].extra_fields:
            item.assets[asset_key].extra_fields["proj:epsg"] = int(
                item.assets[asset_key].extra_fields["proj:code"].replace("EPSG:", "")
            )

    return item


def open_stacit(
    item_collection: ItemCollection | ItemSearch,
    asset_key: str,
    merge_collections: bool,
    overlap_strategy: Literal["REMOVE_IF_NO_NODATA​", "​USE_ALL", "​USE_MOST_RECENT"]
    | None = None,
    **profile: Any,
) -> rio.DatasetReader:
    stack = ExitStack()

    gdal_version = rio.__gdal_version__

    if isinstance(item_collection, ItemSearch):
        _items: Iterable[Item] = item_collection.items()
    else:
        _items = item_collection.items

    item_collection = ItemCollection(
        items=[
            rewrite_item(item, asset_key, merge_collections, gdal_version)
            for item in _items
        ]
    )

    try:
        tmp_dir = stack.enter_context(TemporaryDirectory())
        tmp_path = f"{tmp_dir}/stacit.json"

        item_collection.save_object(dest_href=tmp_path)

        href = f'STACIT:"{tmp_path}":asset={asset_key}'

        if GDALVersion.runtime() < GDALVersion.parse("3.9.1") and (
            overlap_strategy == "USE_ALL"
        ):
            warnings.warn(
                "USE_ALL overlap strategy is only supported "
                "starting at GDAL Version 3.9.1. "
                "Using USE_MOST_RECENT instead."
            )
            overlap_strategy = "USE_MOST_RECENT"

        profile["overlap_strategy"] = overlap_strategy
        dataset = rio.open(href, **profile)

    except Exception:
        stack.close()
        raise

    dataset._env = stack
    return dataset
