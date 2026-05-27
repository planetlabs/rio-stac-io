# rio-stac-io

![From Metadata to Pixels](https://github.com/planetlabs/rio-stac-io/raw/main/docs/img/rio-stac-io.png "rio-stac-io")

rio-stac-io is a [rasterio](https://github.com/rasterio/rasterio) extension to open STAC Items, ItemCollections, client search results, and **STAC-compliant** [GeoDataFrame](https://geopandas.org/) tables (e.g. from [STAC GeoParquet](https://github.com/stac-utils/stac-geoparquet)) using native GDAL drivers including [STACIT](https://gdal.org/en/stable/drivers/raster/stacit.html), [STACTA](https://gdal.org/en/stable/drivers/raster/stacta.html) and [GTI](https://gdal.org/en/stable/drivers/raster/gti.html). The library is build on top of rasterio and pystac. Full notes and a GeoParquet example are in the [documentation](https://planetlabs.github.io/rio-stac-io).

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

`GeoDataFrame` input requires `pip install rio-stac-io[gti]`; rows must follow a STAC item layout (as in stac-geoparquet). The library tries **GTI** first, then **STACIT** if GTI is not usable; the `use_gti` argument is **ignored** for this input type. Example: read a GeoParquet file, filter rows, then open the asset key:

```python
import geopandas as gpd
import rio_stac_io as stacio

gdf = gpd.read_parquet("items.parquet")
gdf = gdf[gdf["collection"] == "s2"]

with stacio.open(gdf, asset_key="cog") as src:
    data = src.read()
```

## Development

This repository requires [Pixi](https://pixi.sh/latest/) v0.67.2 or later.

```
git clone git@github.com:planetlabs/rio-stac-io.git
cd rio-stac-io
pixi shell -e dev
```

Multiple Pixi environments pin different `libgdal` versions (e.g. `dev`, `dev-gdal310`, `dev-gdal312`, `dev-gdal313`, `dev-gdal311-noparquet`; see `pyproject.toml` for the full list). Rasterio is installed from source (`[tool.pixi.pypi-options] no-binary = ["rasterio"]`) so it links against the conda GDAL in that environment.

### Troubleshooting: rasterio linked to the wrong GDAL

Switching between any two GDAL environments locally (for example moving between any of the `dev-gdal*` variants) can leave Pixi's PyPI/build cache holding a rasterio build compiled against a different `libgdal`. Symptoms include odd GTI or CRS failures, or `rasterio.__gdal_version__` not matching `gdalinfo --version` in the same shell.

Check:

```
pixi run -e <env> verify-gdal
```

If that fails, clear the cached build and reinstall the environment (not usually needed on CI—runners are isolated per job):

```
pixi clean cache --pypi --build -y
rm -rf .pixi/envs/<env>
pixi install -e <env>
pixi run -e <env> verify-gdal
```

Replace `<env>` with the environment you use (`dev`, `dev-gdal310`, `dev-gdal312`, `dev-gdal313`, `dev-gdal311-noparquet`, …).
