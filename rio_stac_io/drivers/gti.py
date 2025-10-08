from contextlib import ExitStack
from typing import Any, Iterable

import rasterio as rio
from pystac import Item, ItemCollection
from pystac_client import ItemSearch
from rasterio import DatasetReader
from rasterio.env import Env, local

from rio_stac_io.utils import require_gdal_version, vsi_href


class GTIDatasetReader(DatasetReader):
    links: list[str | None]

    @require_gdal_version("3.10.0")
    def __init__(
        self,
        item_collection: ItemCollection | ItemSearch,
        asset_key: str,
        **profile: Any,
    ) -> None:
        try:
            from geopandas import GeoDataFrame
            from stac_geoparquet.arrow import parse_stac_items_to_arrow
            from stac_geoparquet.arrow._constants import DEFAULT_PARQUET_SCHEMA_VERSION
        except ImportError as e:
            raise ImportError(
                "Missing extra modules. Please install package with as rio-stac-io[gti]"
            ) from e

        with rio.Env() as env:
            if not env.drivers().get("Parquet"):
                raise SystemError(
                    "Cannot open Stac Query using GTI driver. "
                    "Make sure your GDAL library is build with GeoParquet support."
                )

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

            self._files: list[str] = (
                gdf["assets"].apply(lambda x: x[asset_key]["href"]).to_list()
            )
            self.links = [item.get_self_href() for item in _items]

            if not local._env:
                stack.enter_context(Env.from_defaults())

            super().__init__(href, **profile)

            self._env = stack

        except TypeError as e:
            stack.close()
            if "got pyarrow.lib.NullArray" in str(e):
                raise ValueError(
                    "Cannot open dataset. Got empty ItemCollection."
                ) from e

            else:
                raise
        except Exception:
            stack.close()
            raise

    @property
    def files(self) -> list[str]:
        return self._files
