from contextlib import ExitStack
from tempfile import TemporaryDirectory
from typing import Any

import rasterio as rio
from pystac import Item
from rasterio.env import Env

from rio_stac_io.utils import require_gdal_version


@require_gdal_version("3.8.2")
def open_stacta(
    item: Item, asset_key: str, zoom_level: int | None = None, **profile: Any
) -> rio.DatasetReader:
    stack = ExitStack()

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

            max_zoom = max([int(matrix[id]) for matrix in matrix_set["tileMatrices"]])

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

        stack.enter_context(Env(GDAL_STACTA_SKIP_MISSING_METATILE=True))
        dataset = rio.open(href, **profile)
    except Exception:
        stack.close()
        raise

    dataset._env = stack
    print(dataset)
    return dataset
