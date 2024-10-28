import os
import rasterio
import numpy as np
import geopandas as gpd
import logging
from logging import Logger
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler
from scipy.ndimage import distance_transform_edt
from pathlib import Path
from rasterio.warp import reproject
from rasterio.fill import fillnodata
from rasterio.mask import mask
from rasterio.features import rasterize
from typing import List, Optional, Union, Literal
from shapely.geometry import shape

from cdr_schemas.prospectivity_input import ScalingType, TransformMethod, Impute

logger: Logger = logging.getLogger(__name__)


def vector_features_to_gdf(feature_layer_info, cma):
    geometry = [
        shape(feature.get("geom"))
        for feature in feature_layer_info.get("evidence_features", [])
    ]
    logger.info(geometry)
    logger.info("wowowoowoowo")
    extras = [
        shape(feature) for feature in feature_layer_info.get("extra_geometries", [])
    ]
    gdf = gpd.GeoDataFrame(
        {"feature_epsg_4326": geometry + extras},
        geometry="feature_epsg_4326",
        crs="EPSG:4326",
    )
    logger.info(gdf.head())
    gdf = gdf.to_crs(cma.crs)
    return gdf


def process_label_raster(
    *,
    vector_dir: Path,
    cma,
    feature_layer_info,
    aoi,
    reference_layer_path: Path,
    dilation_size: int = 5,
):
    warped_shp_file = vector_dir / "_warped.shp"
    rasterized_file = vector_dir / "_rasterized.tif"
    clipped_file = vector_dir / "_clipped.tif"
    aligned_file = vector_dir / "_aligned.tif"
    dilated_file = vector_dir / "_processed.tif"

    gdf = vector_features_to_gdf(feature_layer_info, cma)

    aoi_gdf = gpd.read_file(aoi)
    clipped_gdf = gpd.clip(gdf, aoi_gdf, keep_geom_type=True)
    logger.info(f"clipped gdf {clipped_gdf.head()}")
    clipped_gdf.to_file(warped_shp_file)
    vector_to_raster(
        src_vector_path=warped_shp_file,
        dst_raster_path=rasterized_file,
        dst_res_x=cma.resolution[0],
        dst_res_y=cma.resolution[1],
        fill_value=0.0,
        aoi_path=aoi,
    )
    logger.info("AVTGERSLKDSFJSLKDFJ")
    clip_raster(
        src_raster_path=rasterized_file, dst_raster_path=clipped_file, aoi_path=aoi
    )
    align_rasters(
        src_raster_path=clipped_file,
        dst_raster_path=aligned_file,
        reference_raster_path=reference_layer_path,
        resampling=rasterio.warp.Resampling.nearest,
    )
    dilate_raster(
        src_raster_path=aligned_file,
        dst_raster_path=dilated_file,
        dilation_size=dilation_size,
        label_raster=True,
    )

    ### Find out the number of rasterized deposits ###
    # Load the raster data
    with rasterio.open(dilated_file) as src:
        raster_data = src.read(1)

    num_of_deposits = np.count_nonzero(raster_data == 1)
    logger.info(f"num_of_deposits:{num_of_deposits}")

    return dilated_file


def preprocess_raster(
    *,
    layer: Path,
    aoi: Path,
    reference_layer_path: Path,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: float,
    dst_res_y: float,
    transform_methods: List,
    default_crs: str = "EPSG:4326",
    default_nodata: float = np.nan,
    warp_resampling_method=rasterio.warp.Resampling.bilinear,
    imputation_size: int = 100,
    imputation_smoothing_iterations: int = 0,
    align_resampling_method=rasterio.warp.Resampling.bilinear,
    dilation_window_size: int = 5,
    dilation_smoothing_iterations: int = 0,
    tukey_fences_multiplier: float = 1.5,
    scaling_type: Literal["standard", "minmax", "maxabs"] = "standard",
    scale_min_value: float = 0.0,
    scale_max_value: float = 1.0,
) -> Path:
    """
    Preprocess a raster layer by formatting, warping, imputing, clipping, aligning, dilating, removing outliers, and scaling.

    Parameters:
    - layer (str): Path to the input raster file.
    - aoi (str): Path to the shapefile defining the region of interest.
    - reference_layer_path (str): Path to the reference raster file.
    - dst_crs (str): The destination coordinate reference system.
    - dst_nodata (float): NoData value for the output raster.
    - dst_res_x, dst_res_y (float): Resolution of the output raster.
    - transform_methods (List): List of preprocessing methods to apply.
    - default_crs (str): The default CRS to use if the raster does not have a CRS (default is 'EPSG:4326').
    - default_nodata (float): The default NoData value to use if the raster does not have a NoData value (default is np.nan).
    - warp_resampling_method (rasterio.warp.Resampling): Resampling method to use for warping.
    - imputation_size (int): Maximum search distance for interpolation (default is 100).
    - imputation_smoothing_iterations (int): Number of smoothing iterations for imputation (default is 0).
    - align_resampling_method (rasterio.warp.Resampling): Resampling method to use for aligning.
    - dilation_window_size (int): Size of the dilation window (default is 5).
    - dilation_smoothing_iterations (int): Number of smoothing iterations for dilation (default is 0).
    - tukey_fences_multiplier (float): The Tukey fences multiplier for outlier removal (default is 1.5).
    - scaling_type (str): The type of scaling to apply. Options are 'standard', 'minmax', and 'maxabs' (default is 'standard').
    - scale_min_value (float): Minimum value for scaling, only used if scaling_type is 'minmax' (default is 0.0).
    - scale_max_value (float): Maximum value for scaling, only used if scaling_type is 'minmax' (default is 1.0).
    """
    # get UI specified preprocessing methods
    transform_methods_dict = {
        "transform": None,
        "impute_method": None,
        "impute_window_size": None,
        "scaling": scaling_type,
    }
    logger.info(transform_methods)
    for method in transform_methods:
        if method in [x.value for x in TransformMethod]:
            transform_methods_dict["transform"] = method
        elif method in [x.value for x in ScalingType]:
            transform_methods_dict["scaling"] = method
        elif isinstance(method, dict):
            transform_methods_dict["impute_method"] = method.get("impute_method")
            transform_methods_dict["impute_window_size"] = method.get("window_size")
        else:
            raise ValueError("Unknown method")

    formatted_file = layer.parent / (layer.stem + "_formatted" + layer.suffix)
    warped_file = layer.parent / (layer.stem + "_warped" + layer.suffix)
    imputed_file = layer.parent / (layer.stem + "_imputed" + layer.suffix)
    clipped_file = layer.parent / (layer.stem + "_clipped" + layer.suffix)
    aligned_file = layer.parent / (layer.stem + "_aligned" + layer.suffix)
    olr_file = layer.parent / (layer.stem + "_olr" + layer.suffix)
    scaled_file = layer.parent / (layer.stem + "_scaled" + layer.suffix)
    if transform_methods_dict["transform"]:
        transform_file = layer.parent / (layer.stem + "_transformed" + layer.suffix)
    dilated_file = layer.parent / (layer.stem + "_processed" + layer.suffix)

    format_nodata_crs(
        src_raster_path=layer,
        dst_raster_path=formatted_file,
        default_crs=default_crs,
        default_nodata=default_nodata,
    )
    warp_raster(
        src_raster_path=formatted_file,
        dst_raster_path=warped_file,
        dst_crs=dst_crs,
        dst_nodata=dst_nodata,
        dst_res_x=dst_res_x,
        dst_res_y=dst_res_y,
        resampling=warp_resampling_method,
    )
    dilate_raster(  # impute
        src_raster_path=warped_file,
        dst_raster_path=imputed_file,
        dilation_size=imputation_size,
        smoothing_iterations=imputation_smoothing_iterations,
        label_raster=False,
    )
    clip_raster(
        src_raster_path=imputed_file, dst_raster_path=clipped_file, aoi_path=str(aoi)
    )
    align_rasters(
        src_raster_path=clipped_file,
        dst_raster_path=aligned_file,
        reference_raster_path=reference_layer_path,
        resampling=align_resampling_method,
    )
    remove_outliers_tukey_raster(
        src_raster_path=aligned_file,
        dst_raster_path=olr_file,
        k=tukey_fences_multiplier,
    )
    scale_raster(
        src_raster_path=olr_file,
        dst_raster_path=scaled_file,
        scaling_type=transform_methods_dict["scaling"],
        min_value=scale_min_value,
        max_value=scale_max_value,
    )
    if transform_methods_dict["transform"]:
        transform_raster(
            src_raster_path=scaled_file,
            dst_raster_path=transform_file,
            method=transform_methods_dict["transform"],
        )
        dilate_raster(  # dilate
            src_raster_path=transform_file,
            dst_raster_path=dilated_file,
            dilation_size=dilation_window_size,
            smoothing_iterations=dilation_smoothing_iterations,
            label_raster=False,
        )
    else:
        dilate_raster(  # dilate
            src_raster_path=scaled_file,
            dst_raster_path=dilated_file,
            dilation_size=dilation_window_size,
            smoothing_iterations=dilation_smoothing_iterations,
            label_raster=False,
        )
    return dilated_file


def preprocess_vector(
    *,
    layer: Path,
    aoi: Path,
    reference_layer_path: Path,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: float,
    dst_res_y: float,
    transform_methods: List,
    burn_value: float = 1.0,
    fill_value: float = np.nan,
    align_resampling_method=rasterio.warp.Resampling.bilinear,
    dilation_window_size: int = 5,
    dilation_smoothing_iterations: int = 0,
    tukey_fences_multiplier: float = 1.5,
    scaling_type: Literal["standard", "minmax", "maxabs"] = "standard",
    scale_min_value: float = 0.0,
    scale_max_value: float = 1.0,
) -> Path:
    """
    Preprocess a raster layer by warping, rasterezing, calculating proximity raster, clipping, aligning, dilating, removing outliers, and scaling.

    Parameters:
    - layer (str): Path to the input raster file.
    - aoi (str): Path to the shapefile defining the region of interest.
    - reference_layer_path (str): Path to the reference raster file.
    - dst_crs (str): The destination coordinate reference system.
    - dst_nodata (float): NoData value for the output raster.
    - dst_res_x, dst_res_y (float): Resolution of the output raster.
    - transform_methods (List): List of preprocessing methods to apply.
    - burn_value (float): Value to burn in the raster (default is 1.0).
    - fill_value (float): Value to fill the raster with (default is np.nan).
    - align_resampling_method (rasterio.warp.Resampling): Resampling method to use for aligning.
    - dilation_window_size (int): Size of the dilation window (default is 5).
    - dilation_smoothing_iterations (int): Number of smoothing iterations for dilation (default is 0).
    - tukey_fences_multiplier (float): The Tukey fences multiplier for outlier removal (default is 1.5).
    - scaling_type (str): The type of scaling to apply. Options are 'standard', 'minmax', and 'maxabs' (default is 'standard').
    - scale_min_value (float): Minimum value for scaling, only used if scaling_type is 'minmax' (default is 0.0).
    - scale_max_value (float): Maximum value for scaling, only used if scaling_type is 'minmax' (default is 1.0).
    """
    # get UI specified preprocessing methods
    transform_methods_dict = {
        "transform": None,
        "impute_method": None,
        "impute_window_size": None,
        "scaling": scaling_type,
    }
    for method in transform_methods:
        if isinstance(method, TransformMethod):
            transform_methods_dict["transform"] = method.value
        elif isinstance(method, Impute):
            transform_methods_dict["impute_method"] = method.impute_method.value
            transform_methods_dict["impute_window_size"] = method.window_size
        elif isinstance(method, ScalingType):
            transform_methods_dict["scaling"] = method.value
        else:
            raise ValueError("Unknown method")

    # gets vector file path
    shp_file = find_shapefiles(layer.parent / layer.stem)
    if len(shp_file) > 1 or len(shp_file) == 0:
        raise Exception(f"Cannot process vector file {layer}.")
    shp_file = Path(shp_file[0])
    # prepares preprocessing file names
    warped_shp_file = (
        layer.parent / layer.stem / (shp_file.stem + "_warped" + shp_file.suffix)
    )
    rasterized_file = layer.parent / (layer.stem + "_rasterized.tif")
    proximity_file = layer.parent / (layer.stem + "_proximity" + rasterized_file.suffix)
    clipped_file = layer.parent / (layer.stem + "_clipped" + rasterized_file.suffix)
    aligned_file = layer.parent / (layer.stem + "_aligned" + rasterized_file.suffix)
    olr_file = layer.parent / (layer.stem + "_olr" + rasterized_file.suffix)
    scaled_file = layer.parent / (layer.stem + "_scaled" + rasterized_file.suffix)
    if transform_methods_dict["transform"]:
        transform_file = layer.parent / (
            layer.stem + "_transformed" + rasterized_file.suffix
        )
    dilated_file = layer.parent / (layer.stem + "_processed" + rasterized_file.suffix)

    warp_vector(
        src_vector_path=shp_file,
        dst_vector_path=warped_shp_file,
        dst_crs=dst_crs,
    )
    vector_to_raster(
        src_vector_path=warped_shp_file,
        dst_raster_path=rasterized_file,
        dst_res_x=dst_res_x,
        dst_res_y=dst_res_y,
        burn_value=burn_value,
        fill_value=fill_value,
        dst_nodata=dst_nodata,
        aoi_path=aoi,
    )
    proximity_raster(
        src_raster_path=rasterized_file,
        dst_raster_path=proximity_file,
        src_burn_value=burn_value,
    )
    clip_raster(
        src_raster_path=proximity_file, dst_raster_path=clipped_file, aoi_path=str(aoi)
    )
    align_rasters(
        src_raster_path=clipped_file,
        dst_raster_path=aligned_file,
        reference_raster_path=reference_layer_path,
        resampling=align_resampling_method,
    )
    remove_outliers_tukey_raster(
        src_raster_path=aligned_file,
        dst_raster_path=olr_file,
        k=tukey_fences_multiplier,
    )
    scale_raster(
        src_raster_path=olr_file,
        dst_raster_path=scaled_file,
        scaling_type=transform_methods_dict["scaling"],
        min_value=scale_min_value,
        max_value=scale_max_value,
    )
    if transform_methods_dict["transform"]:
        transform_raster(
            src_raster_path=scaled_file,
            dst_raster_path=transform_file,
            method=transform_methods_dict["transform"],
        )
        dilate_raster(  # dilate
            src_raster_path=transform_file,
            dst_raster_path=dilated_file,
            dilation_size=dilation_window_size,
            smoothing_iterations=dilation_smoothing_iterations,
            label_raster=False,
        )
    else:
        dilate_raster(  # dilate
            src_raster_path=scaled_file,
            dst_raster_path=dilated_file,
            dilation_size=dilation_window_size,
            smoothing_iterations=dilation_smoothing_iterations,
            label_raster=False,
        )
    return dilated_file


### Processing Functions
def format_nodata_crs(
    src_raster_path,
    dst_raster_path,
    default_crs: str = "EPSG:4326",
    default_nodata: float = np.nan,
) -> None:
    """
    Load a raster, update NoData values to NaN, and save the modified raster.

    Parameters:
    - input_raster_path (str): Path to the input raster file.
    - output_raster_path (str): Path to save the output raster with NoData updated to NaN.
    - default_crs (str): The default CRS to use if the raster does not have a CRS (default is 'EPSG:4326').
    - default_nodata (float): The default NoData value to use if the raster does not have a NoData value (default is np.nan).
    """
    with rasterio.open(src_raster_path) as src:
        raster_data = src.read(1)
        nodata_value = src.nodata
        CRS = src.crs if src.crs is not None else default_crs
        # if nodata_value is not None:
        #     raster_data = np.where(raster_data == nodata_value, default_nodata, raster_data)
        # else:
        #     raise Exception(f"Raster no data value is None: {src_raster_path}")
        raster_data = np.where(raster_data == nodata_value, default_nodata, raster_data)

        metadata = src.meta
        metadata.update(dtype=rasterio.float32, nodata=default_nodata, crs=CRS)

    # Save the modified raster to the output path
    with rasterio.open(dst_raster_path, "w", **metadata) as dst:
        dst.write(raster_data.astype(rasterio.float32), 1)


def warp_raster(
    src_raster_path,
    dst_raster_path,
    dst_crs: str = "ESRI:102008",
    dst_nodata: float = np.nan,
    dst_res_x: float = 500.0,
    dst_res_y: float = 500.0,
    resampling=rasterio.warp.Resampling.bilinear,
) -> None:
    """
    Reproject a raster to a new CRS using rasterio.warp.reproject.

    Parameters:
    - src_raster_path (str): Path to the input raster file.
    - dst_raster_path (str): Path to save the reprojected raster file.
    - dst_crs (str or dict): The destination coordinate reference system.
    - dst_nodata (float or int): NoData value for the output raster.
    - dst_res_x, dst_res_y (float): Resolution of the output raster.
    - resampling (rasterio.warp.Resampling): Resampling method to use.
    """
    with rasterio.open(src_raster_path) as src:
        # Calculate transform and dimensions for output raster
        transform, width, height = rasterio.warp.calculate_default_transform(
            src.crs,
            dst_crs,
            src.width,
            src.height,
            *src.bounds,
            resolution=(dst_res_x, dst_res_y) if dst_res_x and dst_res_y else None,
        )

        # Update metadata for the output raster
        metadata = src.meta.copy()
        metadata.update(
            {
                "crs": dst_crs,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": dst_nodata,
                "dtype": src.dtypes[0],
            }
        )

        # Reproject and write to the output file
        with rasterio.open(dst_raster_path, "w", **metadata) as dst:
            for i in range(1, src.count + 1):
                rasterio.warp.reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling,
                    dst_nodata=dst_nodata,
                )


def dilate_raster(
    src_raster_path,
    dst_raster_path,
    dilation_size: int = 100,
    smoothing_iterations: int = 0,
    label_raster: bool = False,
) -> None:
    """
    Fill NoData values in a raster using rasterio's fillnodata function.

    Parameters:
    - src_raster_path (str): Path to the input raster file.
    - dst_raster_path (str): Path to save the filled raster.
    - dilation_size (int): Maximum search distance for interpolation (default is 100).
    - smoothing_iterations (int): Number of smoothing iterations (default is 0).
    - label_raster (bool): Whether or not the input raster file is a label raster (default is False).
    """
    with rasterio.open(src_raster_path) as src:
        data = src.read(1, masked=True)  # Read the first band
        if label_raster:
            label_msk = np.isnan(data)
        filled_data = fillnodata(
            data,
            max_search_distance=dilation_size,
            smoothing_iterations=smoothing_iterations,
        )
        if label_raster:
            filled_data[label_msk & ~np.isnan(filled_data)] = 0.0

        # Copy metadata and write the filled raster
        profile = src.profile

    with rasterio.open(dst_raster_path, "w", **profile) as dst:
        dst.write(filled_data, 1)


def clip_raster(
    src_raster_path,
    dst_raster_path,
    aoi_path,
) -> None:
    """
    Clip a raster to a region of interest using a shapefile.

    Parameters:
    - input_raster (str): Path to the input raster file.
    - shapefile (str): Path to the shapefile defining the region of interest.
    - output_raster (str): Path to save the clipped raster.
    """
    # Read the shapefile
    shapes = gpd.read_file(aoi_path)
    # shapes['geometry'] = shapes['geometry'].simplify(tolerance=0.1)

    # Open the raster file
    with rasterio.open(src_raster_path) as src:
        # Clip the raster with the shapes from the shapefile
        out_image, out_transform = mask(
            src, shapes.geometry, crop=True, all_touched=True
        )
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

    # Save the clipped raster
    with rasterio.open(dst_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)


def align_rasters(
    src_raster_path,
    dst_raster_path,
    reference_raster_path,
    resampling=rasterio.warp.Resampling.bilinear,
) -> None:
    """
    Aligns a target raster to a reference raster using rasterio.

    Parameters:
    - src_raster_path (str): Path to the target raster file to be aligned.
    - dst_raster_path (str): Path to save the aligned output raster file.
    - reference_raster_path (str): Path to the reference raster file.
    - resampling (rasterio.warp.Resampling): Resampling method to use (default is bilinear).
    """
    # Open the reference raster
    with rasterio.open(reference_raster_path) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height

    # Open the target raster
    with rasterio.open(src_raster_path) as target:
        # Set up the metadata for the aligned output raster
        aligned_meta = target.meta.copy()
        aligned_meta.update(
            {
                "crs": ref_crs,
                "transform": ref_transform,
                "width": ref_width,
                "height": ref_height,
            }
        )

        # Perform the alignment by reprojecting the target raster
        with rasterio.open(dst_raster_path, "w", **aligned_meta) as aligned_raster:
            for i in range(1, target.count + 1):  # Loop through each band
                reproject(
                    source=rasterio.band(target, i),
                    destination=rasterio.band(aligned_raster, i),
                    src_transform=target.transform,
                    src_crs=target.crs,
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    resampling=resampling,
                )


def remove_outliers_tukey_raster(
    src_raster_path, dst_raster_path, k: float = 1.5
) -> None:
    """
    Remove outliers from a raster image using the Tukey fences method.

    Parameters:
    - input_raster_path (str): Path to the input raster file.
    - output_raster_path (str): Path to save the output raster with outliers removed.
    - k (float): The Tukey fences multiplier (default is 1.5).
    """
    # Open the input raster file
    with rasterio.open(src_raster_path) as src:
        raster_data = src.read(1)

        Q1 = np.percentile(raster_data, 25)
        Q3 = np.percentile(raster_data, 75)
        IQR = Q3 - Q1
        lower_fence = Q1 - k * IQR
        upper_fence = Q3 + k * IQR
        p5 = np.percentile(raster_data, 5)
        p95 = np.percentile(raster_data, 95)
        raster_data = np.where(raster_data < lower_fence, p5, raster_data)
        raster_data = np.where(raster_data > upper_fence, p95, raster_data)

        metadata = src.meta
        metadata.update(dtype=rasterio.float32)

    with rasterio.open(dst_raster_path, "w", **metadata) as dst:
        dst.write(raster_data.astype(rasterio.float32), 1)


def scale_raster(
    src_raster_path,
    dst_raster_path,
    scaling_type: Literal["standard", "minmax", "maxabs"] = "standard",
    min_value: float = 0.0,
    max_value: float = 1.0,
) -> None:
    """
    Standard scale a raster image using scikit-learn's StandardScaler.

    Parameters:
    - src_raster_path (str): Path to the input raster file.
    - dst_raster_path (str): Path to save the output scaled raster file.
    - scaling_type (str): The type of scaling to apply. Options are 'standard', 'minmax', and 'maxabs' (default is 'standard').
    - min_value (float): Minimum value for scaling, only used if scaling_type is 'minmax' (default is 0.0).
    - max_value (float): Maximum value for scaling, only used if scaling_type is 'minmax' (default is 1.0).
    """
    with rasterio.open(src_raster_path) as src:
        raster_data = src.read(1)

        flat_data = raster_data.flatten().reshape(-1, 1)
        if scaling_type == "standard":
            scaler = StandardScaler()
        elif scaling_type == "minmax":
            assert min_value < max_value, "min_value must be less than max_value."
            scaler = MinMaxScaler(feature_range=(min_value, max_value))
        elif scaling_type == "maxabs":
            scaler = MaxAbsScaler()
        else:
            Exception(f"Unknown scaling type {scaling_type}.")
        scaled_data = scaler.fit_transform(flat_data)
        scaled_raster_data = scaled_data.reshape(raster_data.shape)

        metadata = src.meta
        metadata.update(dtype=rasterio.float32)

    with rasterio.open(dst_raster_path, "w", **metadata) as dst:
        dst.write(scaled_raster_data.astype(rasterio.float32), 1)


def warp_vector(
    src_vector_path,
    dst_vector_path,
    dst_crs: str = "ESRI:102008",
) -> None:
    """
    Reproject a vector file to a different CRS.

    Parameters:
    - input_vector (str): Path to the input vector file.
    - output_vector (str): Path to save the reprojected vector file.
    - crs (str or dict): The target CRS (e.g., 'EPSG:4326' or {'init': 'epsg:4326'}).
    """
    # Read the vector file
    gdf = gpd.read_file(src_vector_path)

    # Reproject to the target CRS
    gdf = gdf.to_crs(dst_crs)

    # Save the reprojected vector
    gdf.to_file(dst_vector_path, driver="ESRI Shapefile")


def vector_to_raster(
    src_vector_path,
    dst_raster_path,
    dst_res_x: float = 500.0,
    dst_res_y: float = 500.0,
    burn_value: float = 1.0,
    fill_value: float = None,
    dst_nodata: float = np.nan,
    aoi_path: Optional[Union[Path, None]] = None,
) -> None:
    """
    Rasterize a vector file to a raster with specific resolution.

    Parameters:
    - vector_path (str): Path to the input vector file.
    - output_raster (str): Path to save the output raster file.
    - x_res (float): Desired x resolution of the output raster.
    - y_res (float): Desired y resolution of the output raster.
    - burn_value (float): Value to burn in the raster (default is 1.0).
    - fill_value (float): Value to fill the raster with (default is None).
    - dst_nodata (float): NoData value for the output raster (default is np.nan).
    """
    # Read the vector file
    gdf = gpd.read_file(src_vector_path)
    logger.info(f"lines df {gdf.head()}")

    if aoi_path:
        aoi_gdf = gpd.read_file(aoi_path)
        intersecting_lines = gdf[gdf.intersects(aoi_gdf.unary_union)]
        if not intersecting_lines.empty:
            logger.info(f"Intersecting lines:\n{intersecting_lines}")
        else:
            logger.info("No intersecting lines found.")
    # Get bounds and calculate transform
    minx, miny, maxx, maxy = aoi_gdf.total_bounds if aoi_path else gdf.total_bounds
    logger.info(dst_res_x)
    logger.info(maxx)
    logger.info(minx)
    width = int((maxx - minx) / dst_res_x)
    logger.info(width)
    height = int((maxy - miny) / dst_res_y)
    logger.info(height)
    transform = rasterio.transform.from_bounds(minx, miny, maxx, maxy, width, height)
    logger.info(f"trans {transform}")
    logger.info(f"fill_value{fill_value}")
    # Rasterize the geometries
    shapes = ((geom, burn_value) for geom in gdf.geometry)
    logger.info(f"shapes {shapes}")
    raster = rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=fill_value,
    )

    # Write to output raster
    with rasterio.open(
        dst_raster_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        crs=gdf.crs,
        transform=transform,
        nodata=dst_nodata,
    ) as dst:
        dst.write(raster, 1)


def proximity_raster(
    src_raster_path,
    dst_raster_path,
    src_burn_value: float = 1.0,
) -> None:
    """
    Compute pixel proximity raster to values from existing raster.

    Parameters:
    - src_raster_path (str): Path to the input raster file.
    - dst_raster_path (str): Path to save the output raster file.
    - src_burn_value (float): Value from source raster to compute proximities (default is 1).
    """
    # Open the source raster
    with rasterio.open(src_raster_path) as src:
        # Read the first band
        data = src.read(1)

        # Create a mask of where the burn value exists
        burn_value_mask = data == src_burn_value

        # Calculate the proximity using the distance transform
        proximity = distance_transform_edt(~burn_value_mask, sampling=src.res)

        # Update metadata for the output raster
        dst_meta = src.meta.copy()
        dst_meta.update({"dtype": "float32"})

        # Write the proximity raster to the destination path
        with rasterio.open(dst_raster_path, "w", **dst_meta) as dst:
            dst.write(proximity.astype(np.float32), 1)


def find_shapefiles(directory) -> List[Path]:
    """
    Get file paths to all .shp files within a directory and its subfolders.

    Parameters:
    - directory (str): The path to the directory to search.

    Returns:
    - List of file paths to .shp files.
    """
    shapefiles = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".shp"):
                shapefiles.append(os.path.join(root, file))
    return shapefiles


def transform_raster(
    src_raster_path, dst_raster_path, method: str = Literal["log", "abs", "sqrt"]
) -> None:
    """
    Apply a transformation function to a raster image.

    Parameters:
    - src_raster_path (str): Path to the input raster file.
    - dst_raster_path (str): Path to save the output raster file.
    - method (str): The transformation function to apply.
    """
    with rasterio.open(src_raster_path) as src:
        metadata = src.meta
        metadata.update(dtype=rasterio.float32)

        raster_data = src.read(1)
        raster_data = np.where(raster_data == metadata["nodata"], np.nan, raster_data)

        if method == "log":
            transformed_data = np.log(np.where(raster_data > 0, raster_data, np.nan))
        elif method == "abs":
            transformed_data = np.abs(raster_data)
        elif method == "sqrt":
            transformed_data = np.sqrt(np.where(raster_data >= 0, raster_data, np.nan))
        else:
            raise Exception(f"Unknown transform function {method}.")

        transformed_data = np.where(
            np.isnan(transformed_data), metadata["nodata"], transformed_data
        )

    with rasterio.open(dst_raster_path, "w", **metadata) as dst:
        dst.write(transformed_data.astype(rasterio.float32), 1)
