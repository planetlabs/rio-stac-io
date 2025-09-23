# rio-stac-io

rio-stac-io is a [rasterio](https://github.com/rasterio/rasterio) extension to open STAC Items and ItemCollections using native GDAL drivers including [STACIT](https://gdal.org/en/stable/drivers/raster/stacit.html), [STACTA](https://gdal.org/en/stable/drivers/raster/stacta.html) and [GTI](https://gdal.org/en/stable/drivers/raster/gti.html). The library is build on top of rasterio and pystac.

## Installation

```
pip install rio-stac-io
```

When using the GTI driver you will need to install `gti` extras. Your GDAL binaries need to be compiled with geoparquet support.

```
pip install rio-stac-io[gti]
```

## Usage

```python

from pystac_client import Client

import rio_stac_io as stacio

client = Client.open(...)
search = client.search(...)

with stacio.open(search, asset_key="data") as src:
    data = src.read()

```

## Development

This repository requires Pixi v0.52.0 or later.

```
git clone
pixi shell -e dev
```
