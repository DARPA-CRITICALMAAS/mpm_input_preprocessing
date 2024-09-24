import urllib.request
import io
import ssl
import rasterio
import numpy as np
import geopandas as gpd
from typing import Dict, Tuple, Union, Optional


def download_file_from_cdr(download_url: str) -> io.BytesIO:
    """
    Download a raster file from the specified URL.

    This function attempts to download a raster file from the given URL.
    If the download fails due to SSL verification issues, it retries the download without SSL verification.

    Args:
        download_url: The URL from which to download the raster file.

    Returns:
        io.BytesIO: A BytesIO object containing that can be used as path-like input.
    """
    try:
        # With SSL
        response = urllib.request.urlopen(download_url)
    except:
        # Remove SSL verification if try fails
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(download_url, context=context)

    return io.BytesIO(response.read())


def read_raster_band(raster: rasterio.io.DatasetReader, band: int = 1, **kwargs) -> Tuple[np.ndarray, Dict]:
    """
    Read a raster file from the given DatasetReader object and returns the raster array and its metadata.

    In preparation for iterating over multiple bands, the kwargs argument can take every valid key-value pair
    that is present in the input raster's metadata dictionary. E.g., if different bands have different
    nodata values or data types, the metadata will be updated for further processing.

    Args:
        raster: The DatasetReader object from which to read the raster.
        band: The band number to read from the raster.
        **kwargs: Additional keyword arguments to update the metadata of the raster.

    Returns:
        Tuple of np.ndarray, Dict: The raster array and its updated metadata.
            - np.ndarray: A 2-dimensional raster array read from the input raster.
            - Dict: The (updated) metadata of the raster read from the input raster.
    """
    out_array = raster.read(band)
    out_meta = raster.meta.copy()

    out_meta.update(
        count=1
    )
    out_meta.update(kwargs)

    return out_array, out_meta


def convert_float_to_int_value(scalar: Union[int, float]) -> Union[int, float]:
    initial_dtype = np.min_scalar_type(scalar)

    if np.issubdtype(initial_dtype, np.floating) and scalar.is_integer():
        scalar = int(scalar)

    return scalar


def set_minimum_dtype(
    src_array: np.ndarray,
    src_meta: Dict
) -> Tuple[np.ndarray, Dict]:
    """
    Determine the minimum data type for the raster array.

    Args:
        src_array: The raster array to determine the minimum data type for.
        src_meta: The metadata dictionary for the raster.

    Returns:
        Tuple of np.ndarray, Dict: The raster array and its metadata.
            - np.ndarray: The raster array with the minimum data type determined.
            - Dict: The updated metadata dictionary with the minimum data type set.
    """
    nodata = src_meta["nodata"]
    nodata = convert_float_to_int_value(nodata)

    dtype_src = rasterio.dtypes.get_minimum_dtype(src_array)
    dtype_nodata = rasterio.dtypes.get_minimum_dtype(nodata)
    dtype = np.promote_types(dtype_src, dtype_nodata)

    out_meta = src_meta.copy()
    out_meta.update(
        dtype=dtype
    )

    return src_array.astype(dtype), out_meta


def save_raster(
    src_array: np.ndarray,
    src_meta: Dict,
    output_path: str,
    **kwargs
):
    """
    Save a raster array to a file with the specified metadata or profile.

    Writes a given raster array to a file at the specified output path, using the provided metadata.
    It ensures that the minimum data type for the raster array is set and updates the metadata with any additional
    keyword arguments provided. The metadata can be replaced by the raster's profile, providing additional parameters
    for tiling and block size in order to optimize storage and processing for COG compatibility.

    Nodata value in the kwargs argument will overwrite the automatically determined nodata value.

    Args:
        src_array: The raster array to be saved.
        src_meta: The metadata dictionary for the raster.
        output_path: The file path where the raster will be saved.
        **kwargs: Additional keyword arguments to update the metadata of the raster.

    Returns:
        None
    """
    raster_array, raster_meta = set_minimum_dtype(src_array, src_meta)
    raster_array = np.expand_dims(raster_array, axis=0) if raster_array.ndim == 2 else raster_array

    raster_meta.update(kwargs)
    with rasterio.open(output_path, "w", **raster_meta) as dst:
        for i in range(0, raster_meta["count"]):
            dst.write(raster_array[i], i + 1)
        dst.close()


def get_geometry_type(src: gpd.GeoDataFrame) -> str:
    """
    Determine the geometry type of a GeoDataFrame.

    Checks the geometry type of all geometries in the provided GeoDataFrame and returns a string
    indicating the type of geometry. It supports 'Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon',
    and 'MultiPolygon'.

    Args:
        src: The GeoDataFrame whose geometry type is to be determined.

    Returns:
        geometry_type: A string indicating the geometry type of the GeoDataFrame.

    Raises:
        ValueError: If the GeoDataFrame contains mixed or unsupported geometry types.
    """
    if src.geometry.geom_type.isin(["Point", "MultiPoint"]).all():
        geometry_type = "point"
    elif src.geometry.geom_type.isin(["LineString", "MultiLineString"]).all():
        geometry_type = "line"
    elif src.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        geometry_type = "polygon"
    else:
        raise ValueError("The GeoDataFrame contains mixed or unsupported geometry types.")

    return geometry_type


def prepare_geodataframe_for_rasterization(
    src: gpd.GeoDataFrame,
    template: Tuple[np.ndarray, dict],
    query: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """
    Prepare a GeoDataFrame for rasterization.

    Ensure that the input GeoDataFrame is not empty, optionally filters it based on a query,
    and reprojects it to the coordinate reference system (CRS) of the provided template raster.

    Args:
        src: The input GeoDataFrame to be prepared for rasterization.
        template: A tuple containing the template array and its metadata.
            - template_array: The array representing the template raster.
            - template_meta: The metadata dictionary for the template raster.
        query: An optional query string to filter the GeoDataFrame.

    Returns:
        gpd.GeoDataFrame: The queried and reprojected GeoDataFrame

    Raises:
        AssertionError: If the input GeoDataFrame is empty.
        AssertionError: If the queried GeoDataFrame is empty.
    """
    _, template_meta = template
    assert not src.empty, "Input GeoDataFrame is empty."

    if query is not None:
        src = src.query(query)
        assert not src.empty, "Query returned empty GeoDataFrame."

    return src.to_crs(crs=template_meta["crs"], inplace=False)
