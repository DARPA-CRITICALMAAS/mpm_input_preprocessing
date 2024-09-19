import numpy as np
import rasterio
import rasterio.crs
import rasterio.coords
import rasterio.windows
from rasterio import warp
from rasterio.enums import Resampling
from typing import Union, Tuple, Optional



def raster_coregistration(
    src_raster: rasterio.io.DatasetReader,
    template_raster: rasterio.io.DatasetReader,
    resampling: Optional[Resampling] = None,
) -> Tuple[np.ndarray, dict]:

    dst_crs = template_raster.crs
    dst_width = template_raster.width
    dst_height = template_raster.height
    dst_transform = template_raster.transform

    dst_array = np.empty((template_raster.count, dst_height, dst_width))
    dst_array.fill(template_raster.nodata)

    src_array = src_raster.read()

    if resampling is None:
        if np.issubdtype(src_array.dtype, np.integer):
            resampling = Resampling.nearest
        elif np.issubdtype(src_array.dtype, np.floating):
            resampling = Resampling.bilinear

    out_array = warp.reproject(
        source=src_array,
        src_crs=src_raster.crs,
        src_transform=src_raster.transform,
        src_nodata=src_raster.nodata,
        destination=dst_array,
        dst_crs=dst_crs,
        dst_transform=dst_transform,
        dst_nodata=template_raster.nodata,
        resampling=resampling,
    )[0]

    template_array = template_raster.read()
    out_array = np.where(
        template_array == template_raster.nodata, template_raster.nodata, out_array
    )

    out_meta = template_raster.meta.copy()
    return out_array, out_meta
