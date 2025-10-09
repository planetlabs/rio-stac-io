import json
import warnings
from contextlib import ExitStack
from typing import Any, Iterable, Literal

import rasterio as rio
from packaging.version import parse
from pystac import Item, ItemCollection
from pystac_client import ItemSearch
from rasterio import DatasetReader
from rasterio.env import Env, GDALVersion, local
from rasterio.errors import RasterioIOError

from rio_stac_io.utils import infer_projection_metadata, vsi_href


def rewrite_item(
    item: Item,
    asset_key: str,
    merge_collections: bool,
    gdal_version: str,
    infer_projection: bool,
) -> Item:
    item.assets[asset_key].href = vsi_href(item.assets[asset_key].href)

    if merge_collections:
        # STACIT keeps item from different collections in separate subdatasets
        # We can bypass this by removing the collection reference
        item.collection_id = None

    if infer_projection:
        # Infer projection metadata if missing
        # This will call the file header of each asset to extract the projection info
        item = infer_projection_metadata(item, asset_key)

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


class STACITDatasetReader(DatasetReader):
    links: list[str | None]

    def __init__(
        self,
        item_collection: ItemCollection | ItemSearch,
        asset_key: str,
        merge_collections: bool,
        overlap_strategy: Literal["REMOVE_IF_NO_NODATA​", "​USE_ALL", "​USE_MOST_RECENT"]
        | None = None,
        infer_projection: bool = False,
        **profile: Any,
    ) -> None:
        stack = ExitStack()

        gdal_version = rio.__gdal_version__

        if isinstance(item_collection, ItemSearch):
            _items: Iterable[Item] = item_collection.items()
        else:
            _items = item_collection.items

        item_collection = ItemCollection(
            items=[
                rewrite_item(
                    item,
                    asset_key,
                    merge_collections=merge_collections,
                    gdal_version=gdal_version,
                    infer_projection=infer_projection,
                )
                for item in _items
            ]
        )

        if not item_collection.items:
            raise ValueError("Cannot open dataset. Got empty ItemCollection.")

        try:
            # Write ItemCollection to a temporary in-memory file
            # this will create a /vsimem/ path that can be used by the STACIT driver
            tmp_path = stack.enter_context(rio.MemoryFile(ext=".json"))
            tmp_path.write(json.dumps(item_collection.to_dict()).encode("utf-8"))
            tmp_path.seek(0)

            href = f'STACIT:"{tmp_path.name}":asset={asset_key}'

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

            if not local._env:
                stack.enter_context(Env.from_defaults())
            super().__init__(href, **profile)

            self.links = [
                item.get_self_href()
                for item in item_collection.items
                if item.assets[asset_key].href in self.files
            ]
            self._env = stack

        except RasterioIOError as e:
            stack.close()
            if str(e) == "No compatible asset found" and not infer_projection:
                raise RasterioIOError(
                    "No compatible asset found. "
                    "This is likely due to missing projection information "
                    "in the STAC Item or Asset. "
                    "Consider setting the `infer_projection` parameter to `True` "
                    "to infer missing projection information."
                ) from e
            else:
                raise
        except Exception:
            stack.close()
            raise
