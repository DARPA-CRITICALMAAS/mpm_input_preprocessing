import rasterio
import numpy as np
from typing import Literal, Dict, Tuple
from mpm_input_preprocessing.common import utils


def _transform_log(
    src_array: np.ndarray,
):
    src_array = np.where(src_array > 0, src_array, np.nan)
    return np.log(src_array)


def _transform_log1p(
    src_array: np.ndarray,
):
    src_array = np.where(src_array < 0, np.nan, src_array)
    return np.log1p(src_array)


def _transform_abs(
    src_array: np.ndarray,
):
    return np.abs(src_array)


def _transform_sqrt(
    src_array: np.ndarray,
):
    src_array = np.where(src_array < 0, np.nan, src_array)
    return np.sqrt(src_array)


def transform(
    src: Tuple[np.ndarray, Dict],
    method: Literal["log", "log1p", "abs", "sqrt"]
) -> Tuple[np.ndarray, Dict]:
    """
    Apply a specified mathematical transformation to a source array.

    Args:
        src: A tuple containing the source array and its metadata.
            - src_array: The source array to be transformed.
            - src_meta: Metadata associated with the source array, including 'nodata' value.
        method: The transformation method to apply.
            - "log": Apply natural logarithm to the array.
            - "log1p": Apply natural logarithm to (1 + array).
            - "abs": Apply absolute value to the array.
            - "sqrt": Apply square root to the array.

    Returns:
        A tuple containing the transformed array and its updated metadata.
            - out_array: The transformed array.
            - out_meta: Updated metadata for the transformed array.
        """
    src_array, src_meta = src
    src_array = np.where(src_array == src_meta["nodata"], np.nan, src_array)

    if method == "log":
        out_array = _transform_log(src_array)
    elif method == "log1p":
        out_array = _transform_log1p(src_array)
    elif method == "abs":
        out_array = _transform_abs(src_array)
    elif method == "sqrt":
        out_array = _transform_sqrt(src_array)
    else:
        raise ValueError(f"Invalid transform method: {method}")

    out_array = np.nan_to_num(out_array, nan=src_meta["nodata"])
    out_array, out_meta = utils.set_minimum_dtype(out_array, src_meta)

    return out_array, out_meta
