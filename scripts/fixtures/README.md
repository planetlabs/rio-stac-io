# GTI CRS regression fixture

**Branch `gdal-gti-crs-repro-fixture` only — do not merge into `main`.**

`gti_crs_repro_items.parquet` is a STAC GeoParquet index with two public [Copernicus DEM 30m](https://registry.opendata.aws/copernicus-dem/) COG paths (`/vsis3/...`). Use the **same file** for all GDAL versions.

## Reproduce (no Python)

```bash
export AWS_NO_SIGN_REQUEST=YES

curl -fsSL -o items.parquet \
  "https://raw.githubusercontent.com/planetlabs/rio-stac-io/gdal-gti-crs-repro-fixture/scripts/fixtures/gti_crs_repro_items.parquet"

gdalinfo GTI:items.parquet -oo LOCATION_FIELD=assets.data.href
```

| GDAL | Expected |
|------|----------|
| ≤ 3.12.1 | `Coordinate System is:` present |
| ≥ 3.12.2 | No coordinate system block on the GTI dataset |

## Update this fixture

From a dev branch that has `scripts/gdal_gti_crs_repro.py`:

```bash
git checkout gdal-gti-crs-repro-fixture
export AWS_NO_SIGN_REQUEST=YES
python scripts/gdal_gti_crs_repro.py --write-fixture scripts/fixtures/gti_crs_repro_items.parquet
git add scripts/fixtures/gti_crs_repro_items.parquet
git commit -m "Update GTI CRS repro fixture"
git push origin gdal-gti-crs-repro-fixture
```
