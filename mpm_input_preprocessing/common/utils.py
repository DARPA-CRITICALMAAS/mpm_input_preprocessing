import urllib.request
import io
import ssl
import rasterio
import numpy as np
from typing import Dict, Tuple, Union


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
    dtype = rasterio.dtypes.get_minimum_dtype(src_array)

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
    raster_array = np.expand_dims(src_array, axis=0) if src_array.ndim == 2 else src_array
    dtype = rasterio.dtypes.get_minimum_dtype(raster_array)

    raster_meta = src_meta.copy()
    raster_meta.update(dtype=dtype)
    raster_meta.update(kwargs)

    with rasterio.open(output_path, "w", **raster_meta) as dst:
        for i in range(0, raster_meta["count"]):
            dst.write(raster_array[i], i + 1)
        dst.close()
