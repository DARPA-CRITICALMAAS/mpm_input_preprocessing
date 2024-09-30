# Beak preparation tools for CDR integration

### Requirements

```bash
python >= 3.10
poetry
```

### Install

```bash
poetry install
```

### Test (Python) with sample input
```python
from mpm_input_preprocessing.common import preprocessing
preprocessing.test()
```

## Quick start
Tools are stored within the `common` module. The implemented submodules are:
- `utils_vector_processing`
- `utils_raster_processing`
- `utils_transform`
- `utils_impute`
- `utils_helper`

The internal organization/function naming is as following:
- 2 underscores `__` indicate that a function is only used within the same submodule, e.g. `__transform_log()`
- 1 underscore `_` indicates that a function is shared between different submodules, e.g. `_update_nodata()`
- Functions with no underscore are **public** and intended to be called from the `preprocessing` module, e.g. `impute()`

### Hypothetical workflow 
for the `preprocessing`, assumed data are already downloaded.<br>
Note that the **activation** of functions will depend on the **CDR call response**, and is **not** transformed into code yet.

### For raster data
1. Open a raster and template file with `rasterio.open()`
2. Read the `DatasetReader` objects with the implemented `read_raster` function from `utils_helper`
3. Do imputation using the `impute()` function from `utils_impute`
4. Do scaling or transformation using the `transform()` function from `utils_transform` 
5. Save results with the integrated `save_raster()` function from `utils_helper` 

Forwarding of intermediate results is always accomplished by passing an `np.array` and updated metadata `dictionary` to the next step.

**Note**: If the raster has multiple bands, read the raster in a loop with increasing band number and put things together at the end.

### For vector data
1. Open a vector file (e.g., .shp or geopackage) with `geopandas.read()`
2. Open the template raster with `rasterio.open()`
3. Read the `DatasetReader` object with the implemented `read_raster` function from `utils_helper`
4. Pass the source data and template into `prepare_geodataframe` for reprojection and quering
5. Rasterize the `geodataframe` with one of the available `rasterize` options from `utils_vector_processing`
6. Do imputation using the `impute()` function from `utils_impute`
7. Do scaling or transformation using the `transform()` function from `utils_transform` 
8. Save results with the integrated `save_raster()` function from `utils_helper` 

## Public functions
### Utils_raster_preprocessing
Functions for processing raster data, including coregistration.
- `coregistration`: Spatially aligns a source raster to a template raster

### Utils_vector_processing
Functions for processing vector data, including rasterization.
- `prepare_geodataframe`: Prepare a GeoDataFrame for rasterization (e.g. querying, CRS reprojection)
- `rasterize_binary`: Convert features into a binary raster (e.g., template raster, labels)
- `rasterize_encode_categorical`: Rasterize a categorical column from a GeoDataFrame into multiple binary rasters
- `rasterize_continuous`: Rasterize continuous values from a specified column in a GeoDataFrame

### Utils_transform
Functions for value transformation and scaling.
- `transform`: Transformation of an array with a given method.
Supported methods are:
- `log`: transform to **log(values)**
- `log1p`: transform to **log(values + 1)**, especially useful for geochemistry to avoid `nan` with 0  
- `abs`: calculates the **absolute** values of the input array
- `sqrt`: calculates the **square root** of the array's values
- `minmax`: scales values into range **[0, 1]**
- `maxabs`: scales values based on max(abs()) into boundaries **[-1, 1]**
- `standard`: scales values to **zero** mean and **unit** variance

The function also
- Casts the array to the minimum required data type
- Updates the nodata value appropriately

### Utils_impute
Functions for imputing **missing values**
- `impute`: imputation of an array with a given method
Supported methods are:
- `min`: replaces `NaN` values with the **minimum** value
- `max`: replaces `NaN` values with the **maximum** value
- `mean`: replaces `NaN` values with the **mean** value
- `median`: replaces `NaN` values with the **median** value
- `zero`: replaces `NaN` values with **zero**
- `custom`: replaces `NaN` values with a user-specified **custom** value

The function also 
- Updates the nodata value
- Casts the array to the minimum required data type
- Optionally masks the array with a template

### Utils_outlier
Functions for basic outlier detection.
- `clip_outliers`: detect and clip outliers based on the source array.
Supported methods:
- `iqr`

The function also
- Casts the array to the minimum required data type
- Updates the nodata value appropriately

# CDR schema and content
## Schema
Implemented methods, which are **not yet available** in 
the [**CDR schema**](https://github.com/DARPA-CRITICALMAAS/cdr_schemas/blob/main/cdr_schemas/prospectivity_input.py) 
and might need to be added in future releases in order to get triggered based on the JSON/CDR response: 

Transform
- `log1p`

Impute
- `min`
- `max`
- `zero`
- `custom`

Outliers
- `iqr`: method for outlier detection

The outlier removal should be something that users can add as preprocessing method for specific data sets.
From the ML standpoint, it is useful to cut outliers, however, e.g. in geochemistry, we may want to have all values
preserved since we`re looking for high values and anomalies (which should not be clipped).

# Outlook
## Functions
Further functions for integration to have a clean preprocessing workflow.<br>

Mandatory:
- `proximity`: calculate distance to features based on features in a `geodataframe`

Optional, open to discussion
- `snap_to_origin`: to snap results of the `rasterization` to a certain xy-origin if no template is provided
- `slope`: derivative to be calculated from input, whether vector or raster
- `others`: if anything ...


## Data/content
All data to be processed **must** be either raster (.tif) or vector data (.shp, .gpkg).<br>
**It is not an option to unpack zipped files since these can contain basically anything**.

For **.shp**, the simple file + a specific attribute (column) is enough to start preprocessing.<br>
For **.gpkg**, there must be an **additional** parameter to pick the correct layer, since geopackages can
contain multiple layers. Alternatively, only put in .gpkg files with one layer, which makes the selection
of a specific layer obsolete.

Both points are currently not sufficient in the data/json file.

## Libraries
Further packages to be added to the project requirements/environment
- `GDAL`, needed for `proximity`
- `OSGEO`, needed for `proximity`

Beak will put these in and test in Docker setup before integrating the functionality.


# HMI/Plugin
Functionalities and options that should be available for users selection and propagated to the JSON file/schema to be 
used as "activation" for certain preprocessing functions:
- Imputation methods from `utils_impute`
- Transformation methods from `utils_transform`
- Outlier handling from `utils_outlier`
- GPKG layer (not the file but specific layer inside)
- What to do with specific columns in a vector file (rasterize to binary, categorical encoding, continuous)
- Option for other actions after creation of derivatives such as `proximity` (like `transform()`) or uploaded (SME) data

I did not check before what`s alreay available, so this is just a list of what is needed to cover most cases.
Put in/out/open discussion on points that are not clear etc.
