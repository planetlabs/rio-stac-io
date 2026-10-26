from __future__ import annotations

import math
import re
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, ParamSpec, Sequence, TypeGuard, TypeVar

import rasterio as rio
from pystac import Item
from pystac.extensions.projection import AssetProjectionExtension
from rasterio import __gdal_version__
from rasterio.errors import GDALVersionError

P = ParamSpec("P")
R = TypeVar("R")

VersionKey = tuple[tuple[int, ...], int, int, float]

_VERSION_PATTERN = re.compile(
    r"v?(?P<release>\d+(?:\.\d+)*)"
    r"(?:[-_.]?(?P<pre>alpha|a|beta|b|preview|pre|rc|c)[-_.]?(?P<pre_n>\d*))?"
    r"(?:[-_.]?dev[-_.]?(?P<dev_n>\d*))?"
    r"(?:[-+].*)?",
    re.IGNORECASE,
)
_PRE_RELEASE_RANK = {"alpha": 0, "a": 0, "beta": 1, "b": 1}
_RC_RANK = 2
_DEV_ONLY_RANK = -1
_FINAL_RANK = 3

if TYPE_CHECKING:
    from geopandas import GeoDataFrame


def parse_version(version: str) -> VersionKey:
    """Parse a version string into a key that sorts like `packaging.version`.

    Trailing zeros in the release are insignificant (``3.10 == 3.10.0``), and
    pre-releases sort before the final release:
    ``3.10.0dev < 3.10.0a1 < 3.10.0b1 < 3.10.0rc1 < 3.10.0``.
    A ``-`` or ``+`` suffix after the version, such as the commit hash in the
    GDAL dev build ``3.11.0dev-5bf4e8ac5f``, is ignored.

    Args:
        version: Version string, e.g. ``rasterio.__gdal_version__``.

    Returns:
        A tuple that compares with ``<``, ``==`` and ``>`` like the version.

    Raises:
        ValueError: If *version* is not a valid version string.
    """
    match = _VERSION_PATTERN.fullmatch(version.strip())
    if not match:
        raise ValueError(f"Invalid version: {version!r}")
    release = tuple(int(part) for part in match["release"].split("."))
    while len(release) > 1 and release[-1] == 0:
        release = release[:-1]
    pre, dev_n = match["pre"], match["dev_n"]
    if pre:
        stage = _PRE_RELEASE_RANK.get(pre.lower(), _RC_RANK)
    elif dev_n is not None:
        stage = _DEV_ONLY_RANK
    else:
        stage = _FINAL_RANK
    dev = math.inf if dev_n is None else int(dev_n or 0)
    return release, stage, int(match["pre_n"] or 0), dev


def gdal_version_blocked(runtime_version: str, exclude: Sequence[str]) -> bool:
    runtime = parse_version(runtime_version)
    return any(runtime == parse_version(spec) for spec in exclude)


def require_gdal_version(
    gdal_version: str,
    *,
    exclude: Sequence[str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    excluded = tuple(exclude or ())

    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            runtime_str = __gdal_version__
            runtime = parse_version(runtime_str)

            if runtime < parse_version(gdal_version):
                raise GDALVersionError(
                    f"Selected Driver requires GDAL Version {gdal_version} or higher."
                )

            if excluded and gdal_version_blocked(runtime_str, excluded):
                raise GDALVersionError(
                    f"Selected Driver is not supported on GDAL {runtime_str} "
                    f"(excluded: {', '.join(excluded)})."
                )

            return function(*args, **kwargs)

        return wrapper

    return decorator


def is_geodataframe(obj: object) -> TypeGuard[GeoDataFrame]:
    """True if *obj* is a :class:`geopandas.GeoDataFrame` (or a subclass of it).

    The check uses the class MRO and the defining module, so
    *geopandas* is never imported unless some other code path has already
    loaded it. That keeps *geopandas* optional for users who only use
    :mod:`pystac` / :mod:`pystac_client` inputs.
    """
    for cls in type(obj).__mro__:
        if (
            cls.__name__ == "GeoDataFrame"
            and (getattr(cls, "__module__", "") or "") == "geopandas.geodataframe"
        ):
            return True
    return False


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
            asset.transform = list(src.transform)[:6]
            asset.shape = [src.height, src.width]
            asset.code = src.crs.to_string()
    return item
