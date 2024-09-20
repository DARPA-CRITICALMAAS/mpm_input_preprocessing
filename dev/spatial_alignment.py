import numpy as np
import rasterio
import rasterio.crs
import rasterio.coords
import rasterio.windows
from rasterio import warp
from rasterio.enums import Resampling
from typing import Union, Tuple, Optional, Dict


def raster_coregistration(
    source: Tuple[np.ndarray, Dict],
    template: Tuple[np.ndarray, Dict],
    resampling: Optional[Resampling] = None,
) -> Tuple[np.ndarray, Dict]:
    """
    Coregistering a source raster to match the spatial properties of a template raster.

    Args:
        source: A tuple containing the source raster array and its metadata.
            - np.ndarray: The source raster data array.
            - Dict: The source raster metadata.
        template: A tuple containing the template raster array and its metadata.
            - np.ndarray: The template raster data array.
            - Dict: The template raster metadata.
        resampling: The resampling method to use. If None, it defaults to nearest for integer data types
            and bilinear for floating-point data types.

    Returns:
        np.ndarray: The 2-dimensional coregistered raster data array.
        Dict: The updated metadata for the coregistered raster.
    """
    src_array, src_meta = source
    template_array, template_meta = template

    dst_array = np.empty((src_meta["count"], template_meta["height"], template_meta["width"]))
    dst_array.fill(src_meta["nodata"])

    if resampling is None:
        if np.issubdtype(src_array.dtype, np.integer):
            resampling = Resampling.nearest
        elif np.issubdtype(src_array.dtype, np.floating):
            resampling = Resampling.bilinear

    out_array = warp.reproject(
        source=src_array,
        src_crs=src_meta["crs"],
        src_transform=src_meta["transform"],
        src_nodata=src_meta["nodata"],
        destination=dst_array,
        dst_crs=template_meta["crs"],
        dst_transform=template_meta["transform"],
        dst_nodata=src_meta["nodata"],
        resampling=resampling,
    )[0]

    out_meta = template_meta.copy()
    out_meta.update(
        dtype=src_meta["dtype"],
        nodata=src_meta["nodata"],
    )

    return out_array.squeeze(), out_meta
