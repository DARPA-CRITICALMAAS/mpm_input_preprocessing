import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.enums import MergeAlg
from numbers import Number
from typing import Optional, Tuple, List
from mpm_input_preprocessing.common import utils


def _rasterize_features(
    src: Tuple[gpd.array.GeometryArray, np.ndarray],
    template: Tuple[np.ndarray, dict],
    custom_fill_value: Optional[Number] = None,
    custom_nodata_value: Optional[Number] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Rasterize geometries into a raster array based on a given template.

    Args:
        src: A tuple containing geometries and values.
            - GeometryArray: An array of geometries to be rasterized.
            - np.ndarray: An array of values corresponding to the geometries.
        template: A tuple containing the template raster array and its metadata.
            - np.ndarray: The template raster data array.
            - Dict: The template raster metadata.
        custom_fill_value: A custom fill value for pixels without geometries.
        custom_nodata_value: A custom nodata value for the raster.

    Returns:
        A tuple containing:
            - out_array: The rasterized array.
            - out_meta: The metadata dictionary for the rasterized array.
    """
    src_geometries, src_values = src
    template_array, template_meta = template

    nodata = custom_nodata_value if custom_nodata_value is not None else template_meta["nodata"]
    nodata = utils.convert_float_to_int_value(nodata)

    fill_value = custom_fill_value if custom_fill_value is not None else nodata
    fill_value = utils.convert_float_to_int_value(fill_value)

    out_array = features.rasterize(
        shapes=list(zip(src_geometries, src_values)),
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


def create_binary_raster(
    src: gpd.GeoDataFrame,
    template: Tuple[np.ndarray, dict],
    custom_fill_value: Optional[Number] = None,
    custom_nodata_value: Optional[Number] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Convert features into a binary raster.

    Use cases:
        - Template (coverage) creation: use custom_fill_value of None.
        - Encoding categorical features: use custom_fill_value of 0.
        - Label creation: use custom_fill_value of 0.

    Args:
        src: The input GeoDataFrame containing geometries to rasterize.
        template: A tuple containing the template array and its metadata.
        custom_fill_value: Custom fill value for the raster. Defaults to None.
        custom_nodata_value: Custom nodata value for the raster. Defaults to None.

    Returns:
        Tuple[np.ndarray, dict]: A tuple containing the rasterized array and its metadata.

    Raises:
        AssertionError: If CRS mismatch between source and template.
    """
    _, template_meta = template
    assert src.crs == template_meta["crs"], "CRS mismatch between source and template."

    geometries = src.geometry.values
    values = np.ones_like(geometries, dtype=np.int8)

    out_array, out_meta = _rasterize_features(
        src=(geometries, values),
        template=template,
        custom_fill_value=custom_fill_value,
        custom_nodata_value=custom_nodata_value,
    )

    return out_array, out_meta


def rasterize_encode_categorical(
    src: gpd.GeoDataFrame,
    template: Tuple[np.ndarray, dict],
    column_to_raster: str,
    custom_nodata_value: Optional[Number] = None,
) -> List[Tuple[str, np.ndarray, dict]]:
    """
    Rasterize a categorical column from a GeoDataFrame into multiple binary rasters.

    Takes a GeoDataFrame and a specified column containing categorical data,
    and rasterizes each unique value in that column into a separate binary raster indicating
    presence (1) or absence (0) of that value in the original geometries.

    Args:
        src: The input GeoDataFrame containing geometries and categorical data.
        template: A tuple containing the template array and its metadata.
        column_to_raster: The name of the column in the GeoDataFrame to rasterize.
        custom_nodata_value: Custom nodata value for the raster. Defaults to None.

    Returns:
        out_encodings: A list of tuples, each containing:
            - The name of the raster (str) in the format "column_name_value".
            - The rasterized array (np.ndarray).
            - The metadata dictionary (dict) for the raster.
    """
    out_encodings = []
    unique_values = src[column_to_raster].dropna().unique()

    for value in unique_values:
        geometries = src[src[column_to_raster] == value].geometry
        geometries = gpd.GeoDataFrame(geometries, crs=src.crs)

        out_name = column_to_raster + "_" + str(value)
        out_raster, out_meta = create_binary_raster(
            src=geometries,
            template=template,
            custom_fill_value=0,
            custom_nodata_value=custom_nodata_value,
        )

        result = (out_name, out_raster, out_meta)
        out_encodings.append(result)

    return out_encodings
