import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.enums import MergeAlg
from numbers import Number
from typing import Optional, Tuple
from mpm_input_preprocessing.common import utils
from mpm_input_preprocessing.common.utils import get_geometry_type


def create_binary_raster(
    src: gpd.GeoDataFrame,
    template: Tuple[np.ndarray, dict],
    custom_nodata: Optional[Number] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Create a binary raster from a GeoDataFrame using a template raster.

    Function can be used for both creating binary coverages (areas) and binary points (labels).

    It automatically determines whether
        a: the CRS needs to be reprojected (and does if so)
        b: the geometry type

    For points and lines: Features will be set to 1 and areas within the coverage of the template will be set to 0.
    For polygons: Features will be set to 1 and all other areas in the resulting raster will be nodata.

    Args:
        src: The source GeoDataFrame containing geometries to be rasterized.
        template: A tuple containing the template array and its metadata.
            - template_array: The array representing the template raster.
            - template_meta: The metadata dictionary for the template raster.
        custom_nodata: An optional custom nodata value to use in the output raster.
            If not provided, the nodata value from the template metadata will be used.

    Returns:
        A tuple containing the output binary raster array and its metadata.
            - out_array: The array representing the binary raster.
            - out_meta: The metadata dictionary for the binary raster.
    """
    template_array, template_meta = template
    geometry_type = get_geometry_type(src)
    src = src.to_crs(crs=template_meta["crs"], inplace=False)

    nodata = template_meta["nodata"] if custom_nodata is None else custom_nodata
    nodata = utils.convert_float_to_int_value(nodata)
    fill_value = nodata if geometry_type == "polygon" else 0

    out_array = features.rasterize(
        shapes=src.geometry,
        out_shape=(template_meta["height"], template_meta["width"]),
        fill=fill_value,
        transform=template_meta["transform"],
        all_touched=False,
        merge_alg=getattr(MergeAlg, "replace"),
        default_value=1,
    )

    out_array = np.where(template_array == nodata, nodata, out_array)

    out_meta = template_meta.copy()
    out_meta.update(
        nodata=nodata,
        count=1,
    )

    out_array, out_meta = utils.set_minimum_dtype(out_array, out_meta)
    return out_array, out_meta
