![rio-stac-io](img/rio-stac-io.png)

*From Metadata to Pixels*

## About

rio-stac-io is a [rasterio](https://github.com/rasterio/rasterio) extension to open STAC Items and ItemCollections using native GDAL drivers including [STACIT](https://gdal.org/en/stable/drivers/raster/stacit.html), [STACTA](https://gdal.org/en/stable/drivers/raster/stacta.html) and [GTI](https://gdal.org/en/stable/drivers/raster/gti.html). The library is build on top of rasterio and pystac.

## Installation and System requirements

You can install rio-stac-io using pip:

```
pip install rio-stac-io
```

When using the GTI driver you will need to install the `gti` extras. Your GDAL binaries also need to be compiled with geoparquet support.

```
pip install rio-stac-io[gti]
```

Please note that GDAL STAC support changes between different versions. For best support we recommend building rasterio against GDAL 3.10.2 and higher.

## Usage

:::rio_stac_io.io
    options:
      separate_signature: true
      overloads_only: true
      line_length: 60
      show_root_toc_entry: false
      show_source: false

#### STACIT

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

#### GTI

Similar to STACIT, the [GDAL GTI driver](https://gdal.org/en/stable/drivers/raster/gti.html)
accepts pystac ItemCollections or ItemSearch as input and will return a rasterio Dataset,
similar to a VRT.

The GTI driver requires GDAL version 3.10 or later and GDAL must be built with (geo)parquet support.
In addition, rio-stac-io needs to be installed together with the `gti` extras.

Because of the extra dependencies, this driver is not the default and users
must opt into it by setting `use_gti=True`.

Unlike STACIT, GTI will always combine input items into a single rasterio Dataset.
Items in different projections will be reprojected into the projection of the first item.
The user can also set a different output projection by setting the `srs` argument.

#### STACTA

The [GDAL StacTA driver](https://gdal.org/en/stable/drivers/raster/stacta.html)
accepts a single STAC item that implements the
[tiled-assets STAC extension](https://github.com/stac-extensions/tiled-assets/tree/main).
The driver is designed to open gridded data that are stored following the TMS specifications
(i.e., Z/X/Y file path). All data will be loaded lazily.

When using GDAL versions prior to v3.8.x, the driver expects all tiles of the Tile matrix to be present.
Later versions will try to use the [STAC Raster extension](https://github.com/stac-extensions/raster/tree/main)
metadata (if present) to infer datatype and no data value. When using sparse tiles you must set `skip_missing_metatile=True`.


#### STAC Item

A regular STAC Item can be opened directly with rasterio.
