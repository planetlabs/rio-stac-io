import datetime as dt
import json
import os
from typing import Generator

import morecantile
import numpy as np
import pytest
import rasterio as rio
from pystac import Item, ItemCollection
from pystac.extensions.raster import RasterExtension
from rasterio.enums import Resampling
from rio_stac.stac import create_stac_item
from shapely import box, to_geojson

import rio_stac_io as stacio


@pytest.fixture(autouse=True)
def aws_access(monkeypatch) -> None:
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "true")


@pytest.fixture()
def stac_item() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:4326",
    }

    data = arr
    x = 0
    y = 0

    with rio.open(
        f"{path}/item.tif",
        "w",
        transform=rio.Affine(1, 0, x, 0, -1, y),
        **profile,
    ) as dst:
        dst.write(data, 1)
        item = create_stac_item(
            dst,
            input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
            asset_name="data",
            with_proj=True,
        )

    item.save_object(dest_href=f"{path}/item.json")
    yield item

    os.remove(f"{path}/item.json")
    os.remove(f"{path}/item.tif")


@pytest.fixture()
def stac_item_collection() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:4326",
    }
    _x = 0
    _y = 0
    items = []
    for i in range(4):
        data = arr + i
        x = _x + (16 * i)
        y = _y + (16 * i)

        with rio.open(
            f"{path}/item_{i}.tif",
            "w",
            transform=rio.Affine(1, 0, x, 0, -1, y),
            **profile,
        ) as dst:
            dst.write(data, 1)
            item = create_stac_item(
                dst,
                input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                asset_name="data",
                with_proj=True,
            )
            items.append(item)

    item_collection = ItemCollection(items=items)
    item_collection.save_object(dest_href=f"{path}/stac.json")

    yield item_collection

    os.remove(f"{path}/stac.json")
    for i in range(4):
        os.remove(f"{path}/item_{i}.tif")


@pytest.fixture()
def stac_item_collection_proj() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:6933",
    }
    _x = 0
    _y = 0
    items = []
    for i in range(4):
        data = arr + i
        x = _x + (160000 * i)
        y = _y + (160000 * i)

        with rio.open(
            f"{path}/item_proj_{i}.tif",
            "w",
            transform=rio.Affine(10000, 0, x, 0, -10000, y),
            **profile,
        ) as dst:
            dst.write(data, 1)
            item = create_stac_item(
                dst,
                input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                asset_name="data",
                with_proj=True,
            )
            items.append(item)

    item_collection = ItemCollection(items=items)
    item_collection.save_object(dest_href=f"{path}/stac_proj.json")

    yield item_collection

    os.remove(f"{path}/stac_proj.json")
    for i in range(4):
        os.remove(f"{path}/item_proj_{i}.tif")


@pytest.fixture()
def stac_item_collection_multi_collection() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:4326",
    }
    _x = 0
    _y = 0
    items = []
    for i in range(4):
        data = arr + i
        x = _x + (16 * i)
        y = _y + (16 * i)

        with rio.open(
            f"{path}/item_multi_col_{i}.tif",
            "w",
            transform=rio.Affine(1, 0, x, 0, -1, y),
            **profile,
        ) as dst:
            dst.write(data, 1)
            item = create_stac_item(
                dst,
                input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                asset_name="data",
                collection=f"col_{i}",
                with_proj=True,
            )
            items.append(item)

    item_collection = ItemCollection(items=items)
    item_collection.save_object(dest_href=f"{path}/stac_multi_col.json")

    yield item_collection

    os.remove(f"{path}/stac_multi_col.json")
    for i in range(4):
        os.remove(f"{path}/item_multi_col_{i}.tif")


@pytest.fixture()
def stac_item_collection_multi_proj() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
    }

    items = []
    for i in range(4):
        profile["crs"] = f"EPSG:567{i + 6}"
        x = (i + 2) * 1000000 + 500000
        y = 6000000

        data = arr + i

        with rio.open(
            f"{path}/item_multi_proj_{i}.tif",
            "w",
            transform=rio.Affine(10000, 0, x, 0, -10000, y),
            **profile,
        ) as dst:
            dst.write(data, 1)
            item = create_stac_item(
                dst,
                input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                asset_name="data",
                with_proj=True,
            )
            items.append(item)

    item_collection = ItemCollection(items=items)
    item_collection.save_object(dest_href=f"{path}/stac_multi_proj.json")

    yield item_collection

    os.remove(f"{path}/stac_multi_proj.json")
    for i in range(4):
        os.remove(f"{path}/item_multi_proj_{i}.tif")


@pytest.fixture()
def stac_item_collection_overlap() -> Generator:
    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 16,
        "height": 16,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:4326",
    }
    _x = 0
    _y = 0
    items = []
    for i in range(2):
        for j in range(2):
            k = int(f"{i}{j}", 2)
            data = arr + k
            x = _x
            y = _y + (16 * j)

            with rio.open(
                f"{path}/item_{k}.tif",
                "w",
                transform=rio.Affine(1, 0, x, 0, -1, y),
                **profile,
            ) as dst:
                dst.write(data, 1)
                item = create_stac_item(
                    dst,
                    input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                    asset_name="data",
                    with_proj=True,
                )
                items.append(item)

    item_collection = ItemCollection(items=items)
    item_collection.save_object(dest_href=f"{path}/stac.json")

    yield item_collection

    os.remove(f"{path}/stac.json")
    for i in range(4):
        os.remove(f"{path}/item_{i}.tif")


def _stacta_item(sparse: bool, raster_ext: bool):
    tms = morecantile.tms.get("WGS1984Quad")
    parent = morecantile.Tile(512, 256, 9)
    children = tms.children(parent)

    path = f"{os.path.dirname(__file__)}/data"

    arr = np.ones((16, 16), dtype="uint8")
    profile = {
        "count": 1,
        "dtype": "uint8",
        "width": 256,
        "height": 256,
        "nodata": 0,
        "driver": "GTIFF",
        "crs": "EPSG:4326",
    }

    items = []
    for i in range(2):
        for j in range(2):
            k = int(f"{i}{j}", 2)
            tile = children[k]
            data = arr + k
            bounds = tms.bounds(tile)
            x = bounds.left
            y = bounds.top
            res = tms.matrix(tile.z).cellSize

            tile_path = f"{path}/{tile.z}/{tile.x}/{tile.y}"
            os.makedirs(tile_path, exist_ok=True)

            with rio.open(
                f"{tile_path}/item.tif",
                "w",
                transform=rio.Affine(res, 0, x, 0, -1 * res, y),
                **profile,
            ) as dst:
                dst.write(data, 1)
            item = create_stac_item(
                f"{tile_path}/item.tif",
                id=f"item_{k}",
                input_datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                asset_name="data",
                with_proj=True,
                with_raster=raster_ext,
            )
            items.append(item)

    item_collection = ItemCollection(items=items)

    bounds = tms.bounds(parent)
    x = bounds.left
    y = bounds.top
    res = tms.matrix(parent.z).cellSize

    tile_path = f"{path}/{parent.z}/{parent.x}/{parent.y}"
    os.makedirs(tile_path, exist_ok=True)

    with stacio.open(item_collection, asset_key="data") as src:
        data = src.read(out_shape=(1, 256, 256), resampling=Resampling.nearest)

        with rio.open(
            f"{tile_path}/item.tif",
            "w",
            transform=rio.Affine(res, 0, x, 0, -1 * res, y),
            **profile,
        ) as dst:
            dst.write(data)

    matrix_set = tms.model_dump(exclude_none=True, mode="json")
    matrix_set["tileMatrices"] = [
        matrix
        for matrix in matrix_set["tileMatrices"]
        if int(matrix["id"]) <= children[0].z and int(matrix["id"]) >= parent.z
    ]

    stacta_item = Item(
        id="stacta",
        datetime=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
        geometry=json.loads(to_geojson(box(*bounds))),
        bbox=[*bounds],
        stac_extensions=[
            "https://stac-extensions.github.io/tiled-assets/v1.0.0/schema.json",
        ],
        properties={
            "tiles:tile_matrix_links": {
                f"{tms.id}": {
                    "url": f"#{tms.id}",
                    "limits": {
                        "9": {
                            "min_tile_col": parent.x,
                            "max_tile_col": parent.x,
                            "min_tile_row": parent.y,
                            "max_tile_row": parent.y,
                        },
                        "10": {
                            "min_tile_col": min([tile.x for tile in children]),
                            "max_tile_col": max([tile.x for tile in children]),
                            "min_tile_row": min([tile.y for tile in children]),
                            "max_tile_row": max([tile.y for tile in children]),
                        },
                    },
                },
            },
            "tiles:tile_matrix_sets": {tms.id: matrix_set},
        },
    )

    asset_template = items[0].assets["data"].to_dict()
    asset_template["href"] = f"{path}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}/item.tif"
    stacta_item.extra_fields = {"asset_templates": {"data": asset_template}}
    if raster_ext:
        stacta_item.ext.add(RasterExtension.name)

    if sparse:
        x = min(tile.x for tile in children)
        y = min(tile.y for tile in children)
        z = min(tile.z for tile in children)
        os.remove(f"{path}/{z}/{x}/{y}/item.tif")
        os.remove(f"{path}/{parent.z}/{parent.x}/{parent.y}/item.tif")

    stacta_item.save_object(dest_href=f"{path}/stacta-{raster_ext}.json")
    yield stacta_item

    os.remove(f"{path}/stacta-{raster_ext}.json")

    if not sparse:
        os.remove(f"{path}/{parent.z}/{parent.x}/{parent.y}/item.tif")

    for tile in children:
        try:
            os.remove(f"{path}/{tile.z}/{tile.x}/{tile.y}/item.tif")
        except FileNotFoundError:
            pass


@pytest.fixture()
def stacta_item():
    yield from _stacta_item(sparse=False, raster_ext=False)


@pytest.fixture()
def stacta_item_raster():
    yield from _stacta_item(sparse=False, raster_ext=True)


@pytest.fixture()
def stacta_item_sparse():
    yield from _stacta_item(sparse=True, raster_ext=False)


@pytest.fixture()
def stacta_item_sparse_raster():
    yield from _stacta_item(sparse=True, raster_ext=True)
