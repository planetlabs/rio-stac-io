import os
import warnings
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from typing import Any

import rasterio as rio
from pystac import Item
from rasterio.env import Env, local

from rio_stac_io.utils import require_gdal_version


class STACTADatasetReader(rio.DatasetReader):
    links: list[str | None]

    @require_gdal_version("3.8.2")
    def __init__(
        self,
        item: Item,
        asset_key: str,
        zoom_level: int | None = None,
        skip_missing_metatile: bool | None = None,
        **profile: Any,
    ) -> None:
        stack = ExitStack()

        if skip_missing_metatile is None:
            skip = os.environ.get("GDAL_STACTA_SKIP_MISSING_METATILE")
            match skip:
                case "NO", "no":
                    skip_missing_metatile = False
                case _:
                    skip_missing_metatile = True

        profile["skip_missing_metatile"] = skip_missing_metatile

        if skip_missing_metatile and not any(
            [ext for ext in item.stac_extensions if "raster" in ext]
        ):
            warnings.warn(
                "SKIP_MISSING_METATILE is set to True "
                "but STAC raster extension is not used. "
                "This will likely cause an error.",
                UserWarning,
            )

        if zoom_level is not None:
            for key, matrix_set in item.properties["tiles:tile_matrix_sets"].items():
                try:
                    matrices = matrix_set["tileMatrices"]
                    id = "id"
                except KeyError:
                    matrices = matrix_set["tileMatrix"]
                    id = "identifier"

                matrix_set["tileMatrices"] = [
                    matrix for matrix in matrices if int(matrix[id]) <= zoom_level
                ]

                max_zoom = max(
                    [int(matrix[id]) for matrix in matrix_set["tileMatrices"]]
                )

                if not matrix_set["tileMatrices"] or max_zoom < zoom_level:
                    raise ValueError(
                        "Requested zoom level is not present in tile matrix set."
                    )

                item.properties["tiles:tile_matrix_sets"][key] = matrix_set

        try:
            tmp_dir = stack.enter_context(TemporaryDirectory())
            tmp_path = f"{tmp_dir}/stacta.json"

            item.save_object(dest_href=tmp_path)

            href = f'STACTA:"{tmp_path}":{asset_key}'

            self.links = [item.get_self_href()]

            if not local._env:
                stack.enter_context(Env.from_defaults())
            super().__init__(href, **profile)
            self._env = stack

        except Exception:
            stack.close()
            raise
