from functools import wraps
from typing import Any, Callable

from packaging.version import parse
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
