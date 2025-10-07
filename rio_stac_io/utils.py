from functools import wraps
from typing import Any, Callable

import rasterio as rio
from packaging.version import parse
from pystac import Item
from pystac.extensions.projection import AssetProjectionExtension
from rasterio import __gdal_version__
from rasterio.errors import GDALVersionError


def require_gdal_version(gdal_version: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            runtime = parse(__gdal_version__)
            required = parse(gdal_version)

            if not runtime >= required:
                raise GDALVersionError(
                    f"Selected Driver requires GDAL Version {gdal_version} or higher."
                )

            return function(*args, **kwargs)

        return wrapper

    return decorator


def vsi_href(href: str) -> str:
    if href.startswith("http"):
        href = f"/vsicurl/{href}"
    elif href.startswith("s3://"):
        href = href.replace("s3://", "/vsis3/")
    elif href.startswith("gs://"):
        href = href.replace("gs://", "/vsigs/")
    return href


def has_projection_metadata(properties: dict[str, Any]) -> bool:
    """Check if all required projection metadata is present
    GDAL requires the following fields:
    1. proj:code or proj:wkt2 or proj:projjson (one of them filled with non-null values)
    2. Any of the following:
        proj:transform and proj:shape
        proj:transform and proj:bbox
        proj:bbox and proj:shape
    """
    crs_info = ["proj:code", "proj:wkt2", "proj:projjson", "proj:epsg"]
    proj_info = [
        ("proj:transform", "proj:shape"),
        ("proj:transform", "proj:bbox"),
        ("proj:bbox", "proj:shape"),
    ]
    if not any(key in properties for key in crs_info) and not any(
        all(key in properties for key in pair) for pair in proj_info
    ):
        return False
    return True


def infer_projection_metadata(item: Item, asset_key: str) -> Item:
    """Infer projection metadata in the asset's extra_fields if missing"""

    if not has_projection_metadata(
        item.assets[asset_key].extra_fields
    ) and not has_projection_metadata(item.properties):
        with rio.open(item.assets[asset_key].href) as src:
            asset = AssetProjectionExtension.ext(
                item.assets[asset_key], add_if_missing=True
            )
            asset.bbox = list(src.bounds)
            asset.transform = list(src.transform)
            asset.shape = [src.height, src.width]
            asset.code = src.crs.to_string()
    return item
