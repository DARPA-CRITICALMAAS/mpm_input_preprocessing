import urllib.request
import io
import ssl
import rasterio
import numpy as np
from typing import Dict


def download_file_from_cdr(download_url: str):
    try:
        response = urllib.request.urlopen(download_url)
    except:
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(download_url, context=context)

    return io.BytesIO(response.read())


def save_raster(
    raster_array: np.ndarray,
    raster_profile: Dict,
    output_path: str,
    **kwargs
):
    # Update profile with any additional kwargs
    raster_profile = raster_profile.copy()
    raster_profile.update(kwargs)

    # Save the raster as a COG
    with rasterio.open(output_path, 'w', **raster_profile) as dst:
        for i in range(0, raster_profile["count"]):
            dst.write(raster_array[i], i + 1)
        dst.close()
