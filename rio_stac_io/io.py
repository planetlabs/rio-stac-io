from typing import Annotated, Any, Literal, overload

import pystac
import pystac_client
import rasterio as rio
from pystac import Item, ItemCollection
from pystac_client import ItemSearch

from rio_stac_io.drivers.gti import GTIDatasetReader
from rio_stac_io.drivers.stacit import STACITDatasetReader
from rio_stac_io.drivers.stacta import STACTADatasetReader


@overload
def open(
    items: Annotated[
        pystac.ItemCollection | pystac_client.ItemSearch,
        "STAC Items must implement the Projection STAC extension",
    ],
    mode: Literal["r"] = "r",
    *,
    asset_key: str,
    use_gti: Literal[False] = False,
    merge_collections: bool = False,
    infer_projection: bool = False,
    max_items: int = 1000,
    collection: str | None = None,
    crs: str | None = None,
    resolution: Literal["AVERAGE", "HIGHEST", "​LOWEST"] = "AVERAGE",
    overlap_strategy: Literal[
        "REMOVE_IF_NO_NODATA", "USE_ALL", "USE_MOST_RECENT"
    ] = "REMOVE_IF_NO_NODATA",
) -> STACITDatasetReader:
    """
    STACIT

    The [GDAL StacIT driver](https://gdal.org/en/stable/drivers/raster/stacit.html)
    accepts pystac ItemCollections or ItemSearch as input and
    will return a rasterio Dataset, similar to a VRT.
    This driver is used by default when using a ItemCollection or ItemSearch as input.

    STAC Items must use the [STAC Projection extension](https://github.com/stac-extensions/projection),
    providing metadata about CRS used, projected bounds and Affine transformation.
    Items without this metadata will be ignored.

    By default, STACIT will split items from different STAC collections
    or with different projections into subdatasets.
    You can force the driver to return a single dataset
    by either filtering by CRS or Collections or telling it
    to merge all collections setting `merge_collections=True`.

    If you need to merge items using different projection
    consider using the GTI driver instead.

    While the StacIT driver only fully supports STAC v1.1.0
    Items starting with GDAL 3.10.2, `rio-stac-io` will assure
    backwards compatibility also for earlier GDAL versions.

    Parameters
    ----------
    items : pystac.ItemCollection or pystac_client.ItemSearch
        Input STAC Items. Items must implement the Projection STAC extension.
    mode : Literal["r"], default "r"
        Read-only mode.
    asset_key : str
        Asset to open.
    use_gti : Literal[False], default False
        Must be set to False to use the STACIT driver.
    merge_collections : bool, default False
        Combine items from multiple collections into a single dataset.
    infer_projection : bool, default False
        Infer projection metadata if missing.
        This will call the file header of each asset to extract the projection metadata.
    max_items : int, default 1000
        Maximum number of items fetched. 0 means unlimited.
    collection : str or None, optional
        Name of collection to filter items.
    crs : str or None, optional
        Name of CRS to filter items.
    resolution : Literal["AVERAGE", "HIGHEST", "LOWEST"], default "AVERAGE"
        Strategy to use to determine dataset resolution.
    overlap_strategy : Literal["REMOVE_IF_NO_NODATA", "USE_ALL", "USE_MOST_RECENT"],
        default "REMOVE_IF_NO_NODATA"
        Strategy to use when the ItemCollections contains overlapping items.

    Returns
    -------
    rio.DatasetReader
        A rasterio DatasetReader object.
    """  # noqa: E501
    ...


@overload
def open(
    items: Annotated[
        pystac.ItemCollection | pystac_client.ItemSearch,
        "STAC Items must implement the Projection STAC extension",
    ],
    mode: Literal["r"] = "r",
    *,
    asset_key: str,
    use_gti: Literal[True] = True,
    sort_field: str | None = None,
    sort_field_asc: bool = True,
    filter: str | None = None,
    resx: float | None = None,
    resy: float | None = None,
    srs: str | None = None,
    minx: float | None = None,
    miny: float | None = None,
    maxx: float | None = None,
    maxy: float | None = None,
) -> GTIDatasetReader:
    """
    GTI

    Similar to STACIT, the [GDAL GTI driver](https://gdal.org/en/stable/drivers/raster/gti.html)
    accepts pystac ItemCollections or ItemSearch as input and will return a rasterio Dataset,
    similar to a VRT.

    The GTI driver requires GDAL version 3.10 or later
    and GDAL must be built with (geo)parquet support.
    In addition, rio-stac-io needs to be installed together with the `gti` extras.

    Because of the extra dependencies, this driver is not the default and users
    must opt into it by setting `use_gti=True`.

    Unlike STACIT, GTI will always combine input items into a single rasterio Dataset.
    Items in different projections will be reprojected into the projection of the first item.
    The user can also set a different output projection by setting the `srs` argument.

    Parameters
    ----------
    items : pystac.ItemCollection or pystac_client.ItemSearch
        Input STAC Items. Items must implement the Projection STAC extension.
    mode : Literal["r"], default "r"
        Read-only mode.
    asset_key : str
        Asset to open.
    use_gti : Literal[True], default True
        Must be set to True in order to use this driver.
    sort_field : str or None, optional
        Name of a field to use to control the order in which tiles are composited,
        when they overlap (z-order).
        That field may be of type String, Integer, Integer64, Date or DateTime.
        By default, the higher the value in that field,
        the last the corresponding tile will be rendered in the virtual mosaic (unless
        SORT_FIELD_ASC=NO is set).
    sort_field_asc : bool, default True
        Whether the values in SORT_FIELD should be sorted in ascending or descending order.
    filter : str or None, optional
        Value of a SQL WHERE clause, used to select a subset of the features of the index.
    resx : float or None, optional
        Resolution along X axis in SRS units / pixel.
    resy : float or None, optional
        Resolution along Y axis in SRS units / pixel.
    srs : str or None, optional
        Override/sets the Spatial Reference System.
    minx : float or None, optional
        Minimum X value for the virtual mosaic extent.
    miny : float or None, optional
        Minimum Y value for the virtual mosaic extent.
    maxx : float or None, optional
        Maximum X value for the virtual mosaic extent.
    maxy : float or None, optional
        Maximum Y value for the virtual mosaic extent.

    Returns
    -------
    rio.DatasetReader
        A rasterio DatasetReader object.
    """  # noqa: E501
    ...


@overload
def open(  # type: ignore[overload-cannot-match]  # passes on macos but not linux ¯\_(ツ)_/¯
    items: Annotated[pystac.Item, "regular STAC Item"],
    mode: Literal["r"] = "r",
    *,
    asset_key: str,
) -> rio.DatasetReader:
    """
    STAC Item

    A regular STAC Item can be opened directly with rasterio.

    Parameters
    ----------
    items : pystac.Item
        Input STAC Item. Must implement the Tiled Asset STAC extension.
    mode : Literal["r"], default "r"
        Read-only mode.
    asset_key : str
        Asset to open.

    Returns
    -------
    rio.DatasetReader
        A rasterio DatasetReader object.
    """
    ...


@overload
def open(  # type: ignore[overload-cannot-match]  # passes on macos but not linux ¯\_(ツ)_/¯
    items: Annotated[pystac.Item, "uses tiled-assets STAC extension"],
    mode: Literal["r"] = "r",
    *,
    asset_key: str,
    zoom_level: int | None = None,
    whole_metatile: bool = True,
    skip_missing_metatile: bool = True,
) -> STACTADatasetReader:
    """
    STACTA

    The [GDAL StacTA driver](https://gdal.org/en/stable/drivers/raster/stacta.html)
    accepts a single STAC item that implements the
    [tiled-assets STAC extension](https://github.com/stac-extensions/tiled-assets/tree/main).
    The driver is designed to open gridded data that are stored following the TMS specifications
    (i.e., Z/X/Y file path). All data will be loaded lazily.

    When using GDAL versions prior to v3.8.x, the driver expects all tiles of the Tile matrix to be present.
    Later versions will try to use the [STAC Raster extension](https://github.com/stac-extensions/raster/tree/main)
    metadata (if present) to infer datatype and no data value.
    When using sparse tiles you must set `skip_missing_metatile=True`.

    Parameters
    ----------
    items : pystac.Item
        Input STAC Item. Must implement the Tiled Asset STAC extension.
    mode : Literal["r"], default "r"
        Read-only mode.
    asset_key : str
        Asset to open.
    zoom_level : int or None, optional
        Specific zoom level to open. Will default to the max zoom level specified in the tile matrix set.
    whole_metatile : bool, default True
        If set to True, metatiles will be entirely downloaded (into memory).
        Otherwise, by default, if metatiles are bigger than a threshold,
        they will be accessed in a piece-wise way.
    skip_missing_metatile : bool, default True
        If set to True, metatiles that are missing will be skipped without error,
        and the corresponding area in the dataset will be filled with the nodata value or zero if there is no nodata value.
        This setting will require the implementation of the STAC Raster Extension.
        This setting can also be set with the GDAL_STACTA_SKIP_MISSING_METATILE configuration option.

    Returns
    -------
    rio.DatasetReader
        A rasterio DatasetReader object.
    """  # noqa: E501
    ...


def open(
    items: Item | ItemCollection | ItemSearch,
    mode: Literal["r"] = "r",
    *,
    asset_key: str,
    use_gti: bool = False,
    merge_collections: bool = False,
    infer_projection: bool = False,
    zoom_level: int | None = None,
    **kwargs: Any,
) -> rio.DatasetReader:
    """rio-stac-io accepts any pystac Item, ItemCollection or ItemSearch
    and returns a rasterio DatasetReader.
    Input items will be merged into a single layer,
    similar to a VRT and served as a single rasterio Dataset.
    If you need to read time series,
    consider using [ODC STAC](https://github.com/opendatacube/odc-stac)
    that will return an multi-dimensional XArray object instead.

    ```python

    from pystac_client import Client

    import rio_stac_io as stacio

    client = Client.open(...)
    search = client.search(...)

    with stacio.open(search, asset_key="data") as src:
        data = src.read()

    ```

    # Drivers

    rio-stac-io will determine which driver to use based on your input data.
    By default, it will use the STACIT driver for all
    ItemCollection and ItemSearch inputs.
    If you set `use_gti=True`, it will use the GTI driver instead.
    When provided with a single Item as input, it will use the
    STACTA driver if the item uses the tiled-asset STAC extension
    and rasterio when using a regular item.

    See overloaded function signatures for details.

    """

    if mode != "r":
        raise ValueError(
            f"This is a read-only dataset. Mode `{mode}` is not supported."
        )

    if isinstance(items, Item):
        if any([ext for ext in items.stac_extensions if "tiled-assets" in ext]):
            return STACTADatasetReader(
                items, asset_key, zoom_level=zoom_level, **kwargs
            )
        else:
            return rio.open(items.assets[asset_key].href)

    elif isinstance(items, (ItemCollection, ItemSearch)):
        if use_gti:
            return GTIDatasetReader(items, asset_key, **kwargs)

        else:
            return STACITDatasetReader(
                items,
                asset_key,
                merge_collections=merge_collections,
                infer_projection=infer_projection,
                **kwargs,
            )

    else:
        return rio.open(items, **kwargs)
