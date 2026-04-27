from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Iterable

import rasterio as rio
from pystac import Item, ItemCollection
from pystac_client import ItemSearch
from rasterio import DatasetReader
from rasterio.env import Env, local

from rio_stac_io.utils import require_gdal_version, vsi_href

if TYPE_CHECKING:
    from geopandas import GeoDataFrame


class GTIDatasetReader(DatasetReader):
    links: list[str | None]

    @require_gdal_version("3.10.0")
    def __init__(
        self,
        item_collection: ItemCollection | ItemSearch | GeoDataFrame,
        asset_key: str,
        **profile: Any,
    ) -> None:
        try:
            from geopandas import GeoDataFrame
            from stac_geoparquet.arrow import parse_stac_items_to_arrow
            from stac_geoparquet.arrow._constants import DEFAULT_PARQUET_SCHEMA_VERSION
            from stac_geoparquet.stac_geoparquet import SELF_LINK_COLUMN
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

        if isinstance(item_collection, GeoDataFrame):
            gdf = item_collection

        else:
            if isinstance(item_collection, ItemSearch):
                _items: Iterable[Item] = item_collection.items()
            else:
                _items = item_collection.items
            try:
                arrow = parse_stac_items_to_arrow(_items)
                gdf = GeoDataFrame.from_arrow(arrow)
            except TypeError as e:
                if "got pyarrow.lib.NullArray" in str(e):
                    raise ValueError(
                        "Cannot open dataset. Got empty ItemCollection."
                    ) from e

                else:
                    raise

        gdf["assets"] = gdf["assets"].apply(rewrite_href)

        stack = ExitStack()
        # Write ItemCollection to a temporary in-memory Parquet file
        # This will create a /vsimem/ path that can be used by the GTI driver
        tmp_path = stack.enter_context(rio.MemoryFile(ext=".parquet"))

        try:
            gdf.to_parquet(tmp_path, schema_version=DEFAULT_PARQUET_SCHEMA_VERSION)
            tmp_path.seek(0)

            href = f"GTI:{tmp_path.name}"
            profile.pop("driver", None)
            profile["LOCATION_FIELD"] = f"assets.{asset_key}.href"

            self._files: list[str] = (
                gdf["assets"].apply(lambda x: x[asset_key]["href"]).to_list()
            )
            if isinstance(item_collection, GeoDataFrame):
                if SELF_LINK_COLUMN in gdf.columns:
                    self.links = gdf[SELF_LINK_COLUMN].tolist()
                else:
                    self.links = [None] * len(gdf)
            else:
                self.links = [item.get_self_href() for item in _items]

            if not local._env:
                stack.enter_context(Env.from_defaults())

            super().__init__(href, **profile)

            self._env = stack

        except Exception:
            stack.close()
            raise

    @property
    def files(self) -> list[str]:
        return self._files
