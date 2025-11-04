# rio-stac-io

![From Metadata to Pixels](docs/img/rio-stac-io.png "rio-stac-io")

rio-stac-io is a [rasterio](https://github.com/rasterio/rasterio) extension to open STAC Items and ItemCollections using native GDAL drivers including [STACIT](https://gdal.org/en/stable/drivers/raster/stacit.html), [STACTA](https://gdal.org/en/stable/drivers/raster/stacta.html) and [GTI](https://gdal.org/en/stable/drivers/raster/gti.html). The library is build on top of rasterio and pystac.

## Documentation

https://planetlabs.github.io/rio-stac-io


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

This repository requires [Pixi](https://pixi.sh/latest/) v0.52.0 or later.

```
git clone git@github.com:planetlabs/rio-stac-io.git
cd rio-stac-io
pixi shell -e dev
```
