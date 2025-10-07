from contextlib import ExitStack
from typing import Any, Iterable

import rasterio as rio
from pystac import Item, ItemCollection
from pystac_client import ItemSearch
from rasterio import DatasetReader

from rio_stac_io.utils import require_gdal_version, vsi_href


@require_gdal_version("3.10.0")
def open_gti(
    item_collection: ItemCollection | ItemSearch,
    asset_key: str,
    **profile: Any,
) -> rio.DatasetReader:
    try:
        from geopandas import GeoDataFrame
        from stac_geoparquet.arrow import parse_stac_items_to_arrow
        from stac_geoparquet.arrow._constants import DEFAULT_PARQUET_SCHEMA_VERSION
    except ImportError as e:
        raise ImportError(
            "Missing extra modules. Please install package with as rio-stac-io[gti]"
        ) from e

    def rewrite_href(assets: dict[str, Any]) -> dict[str, Any]:
        assets[asset_key]["href"] = vsi_href(assets[asset_key]["href"])
        return assets

    stack = ExitStack()

    if isinstance(item_collection, ItemSearch):
        _items: Iterable[Item] = item_collection.items()
    else:
        _items = item_collection.items

    try:
        # Write ItemCollection to a temporary in-memory Parquet file
        # This will create a /vsimem/ path that can be used by the GTI driver
        tmp_path = stack.enter_context(rio.MemoryFile(ext=".parquet"))
        arrow = parse_stac_items_to_arrow(_items)
        gdf = GeoDataFrame.from_arrow(arrow)
        gdf["assets"] = gdf["assets"].apply(rewrite_href)

        gdf.to_parquet(tmp_path, schema_version=DEFAULT_PARQUET_SCHEMA_VERSION)
        tmp_path.seek(0)

        href = f"GTI:{tmp_path.name}"
        profile.pop("driver", None)
        profile["LOCATION_FIELD"] = f"assets.{asset_key}.href"
        with rio.Env() as env:
            if not env.drivers().get("Parquet"):
                raise SystemError(
                    "Cannot open Stac Query using GTI driver. "
                    "Make sure your GDAL library is build with GeoParquet support."
                )
        dataset = rio.open(href, **profile)

        # GTI doesn't expose the contributing files
        # we need to patch the dataset reader to do that
        class GTIDatasetReader(DatasetReader):
            @property
            def files(self) -> list[str]:
                files: list[str] = (
                    gdf["assets"].apply(lambda x: x[asset_key]["href"]).to_list()
                )
                return files

        dataset.__class__ = GTIDatasetReader
        dataset._env = stack

    except TypeError as e:
        stack.close()
        if "got pyarrow.lib.NullArray" in str(e):
            raise ValueError("Cannot open dataset. Got empty ItemCollection.") from e

        else:
            raise
    except Exception:
        stack.close()
        raise

    return dataset
