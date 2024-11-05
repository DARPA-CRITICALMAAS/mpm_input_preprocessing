import fiona
import os
import zipfile
from pathlib import Path
import geopandas as gpd
from tqdm import tqdm
from typing import Union, List
import httpx
import logging
from urllib.parse import urlparse
import boto3
from logging import Logger
import json
import hashlib
from uuid import uuid4

from .utils_preprocessing import (
    preprocess_raster,
    preprocess_vector,
    process_label_raster,
    vector_features_to_gdf,
)

from ..settings import app_settings

logger: Logger = logging.getLogger(__name__)

auth = {
    "Authorization": app_settings.cdr_bearer_token,
}


def create_aoi_geopkg(cma, dst_dir: Path = Path("./data")) -> Path:
    # Creating the AOI geopackage
    gdf = gpd.GeoDataFrame({"id": [0]}, crs=cma.crs, geometry=[cma.extent])
    try:
        gdf.to_file(dst_dir / Path("aoi.gpkg"), driver="GPKG")
        return dst_dir / Path("aoi.gpkg")
    except fiona.errors.TransactionError:
        gdf.to_file(dst_dir / Path("aoi.shp"))
        return dst_dir / Path("aoi.shp")


def download_reference_layer(cma, dst_dir: Path = Path("./data")) -> Path:
    s3_key = parse_s3_url(cma.download_url)[1]
    dst_path = dst_dir / Path(cma.download_url).name
    download_file(s3_key, dst_path)

    return dst_path


def _uuid():
    return uuid4().hex


def download_evidence_layer(title: str, s3_key: str, dst_dir: Path) -> Path:
    if not title:
        title = _uuid()
    local_file = f"{title}{Path(s3_key).suffix}"
    dst_path = dst_dir / local_file
    download_file(s3_key, dst_path)

    return dst_path


def parse_s3_url(url: str):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.lstrip("/").split("/")
    bucket = path_parts[0]
    s3_key = "/".join(path_parts[1:])

    return bucket, s3_key


def s3_client(endpoint_url=app_settings.cdr_s3_endpoint_url):
    s3 = boto3.client("s3", endpoint_url=endpoint_url, verify=False)
    return s3


def download_file(s3_key, local_file_path):
    s3 = s3_client()
    try:
        s3.download_file(app_settings.cdr_public_bucket, s3_key, local_file_path)
        logger.info(f"File downloaded successfully to {local_file_path}")
    except Exception:
        logger.exception("Error downloading file from S3")


def download_evidence_layers(
    evidence_layers, dst_dir: Path = Path("./data")
) -> List[Path]:
    # sets evidence layers location
    ev_lyrs_path = dst_dir

    for ev_lyr in tqdm(evidence_layers):
        ev_lyr_path = download_evidence_layer(
            title=ev_lyr.get("data_source", {}).get("evidence_layer_raster_prefix"),
            s3_key=parse_s3_url(ev_lyr.get("data_source", {}).get("download_url"))[1],
            dst_dir=ev_lyrs_path,
        )
        # if ev_lyr_path.suffix == ".zip":
        if ev_lyr.get("data_source", {}).get("format", "") == "shp":
            os.makedirs(ev_lyr_path.parent / ev_lyr_path.stem, exist_ok=True)
            with zipfile.ZipFile(ev_lyr_path, "r") as zip_ref:
                zip_ref.extractall(ev_lyr_path.parent / ev_lyr_path.stem)
        ev_lyr["local_file_path"] = ev_lyr_path
        logger.info(ev_lyr)
    return evidence_layers


async def post_results(file_name, file_path, data, file_logger):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            data_ = {"metadata": data}
            files_ = [("input_file", (file_name, open(file_path, "rb")))]

            logging.debug(f"files to be sent {files_}")
            logging.debug(f"data to be sent {data_}")
            r = await client.post(
                app_settings.cdr_endpoint_url
                + "/v1/prospectivity/prospectivity_input_layer",
                files=files_,
                data=data_,
                headers=auth,
            )
            logging.debug(f"Response text from CDR {r.text}")
            r.raise_for_status()
        except Exception:
            file_logger.exception("Failed to send to cdr.")


async def process_vector_layer(
    *,
    tmpdir,
    vector_dir,
    cma,
    feature_layer_objects: List,
    aoi,
    reference_layer_path,
    dilation_size: int = 5,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int,
    event_id: str,
    file_logger,
):
    for feature_layer_info in feature_layer_objects:
        hash_object = hashlib.sha256()

        hash_object.update(
            (json.dumps(sorted(feature_layer_info)) + str(dilation_size)).encode(
                "utf-8"
            )
        )

        hex_dig = (
            hash_object.hexdigest()
            + "_"
            + app_settings.SYSTEM
            + "_"
            + app_settings.SYSTEM_VERSION
        )

        if feature_layer_info.get("label_raster", False):
            # this is a label raster so fill as binary 1/0s in cells
            pev_lyr_path = process_label_raster(
                vector_dir=vector_dir,
                cma=cma,
                feature_layer_info=feature_layer_info,
                aoi=aoi,
                reference_layer_path=reference_layer_path,
                dilation_size=dilation_size,
            )

            payload = json.dumps(
                {
                    "cma_id": cma.cma_id,
                    "title": feature_layer_info.get("title", "NeedToSetTitle"),
                    "system": app_settings.SYSTEM,
                    "system_version": app_settings.SYSTEM_VERSION,
                    "transform_methods": feature_layer_info.get("transform_methods"),
                    "label_raster": feature_layer_info.get("label_raster", False),
                    "raw_data_info": [
                        {"id": x.get("id"), "raw_data_type": x.get("raw_data_type")}
                        for x in feature_layer_info.get("evidence_features", [])
                    ],
                    "extra_geometries": feature_layer_info.get("extra_geometries", []),
                    "event_id": event_id,
                }
            )
            logger.info(f"payload {payload}")
            logger.info("Finished")
            await post_results(
                file_name=f"{hex_dig}.tif",
                file_path=pev_lyr_path,
                data=payload,
                file_logger=file_logger,
            )
        else:
            # this is a vector payload we need to create into a zip and process
            # create a zip of my features.
            gdf = vector_features_to_gdf(feature_layer_info, cma)

            output_folder = os.path.join(tmpdir, "output_shapefile")
            shapefile_path = os.path.join(output_folder, "my_shapefile.shp")
            os.makedirs(output_folder, exist_ok=True)

            gdf.to_file(shapefile_path)

            feature_layer_info["local_file_path"] = Path(output_folder)

            await process_vector_folder(
                layer=feature_layer_info,
                aoi=aoi,
                reference_layer_path=reference_layer_path,
                cma_id=cma.cma_id,
                dst_crs=dst_crs,
                dst_nodata=dst_nodata,
                dst_res_x=dst_res_x,
                dst_res_y=dst_res_y,
                event_id=event_id,
                raw_data_info=[
                    {"id": x.get("id"), "raw_data_type": x.get("raw_data_type")}
                    for x in feature_layer_info.get("evidence_features", [])
                ],
                extra_geometries=feature_layer_info.get("extra_geometries", []),
                file_name=f"{hex_dig}",
                file_logger=file_logger,
            )


async def preprocess_evidence_layers(
    evidence_layers,
    aoi: Path,
    reference_layer_path: Path,
    cma_id: str,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int,
    event_id: str,
    file_logger,
) -> List[Path]:
    for idx, layer in tqdm(enumerate(evidence_layers)):
        try:
            hash_obj = hashlib.md5()
            hash_obj.update(
                json.dumps(
                    sorted([str(x) for x in layer.get("transform_methods", [])])
                ).encode("utf-8")
            )
            hex_digest = hash_obj.hexdigest()

            hash_obj2 = hashlib.md5()

            hash_obj2.update(
                layer.get("data_source", {}).get("data_source_id", "").encode("utf-8")
            )
            hex_digest2 = hash_obj2.hexdigest()
            # default name
            file_name = (
                str(hex_digest)
                + "_"
                + str(hex_digest2)
                + "_"
                + app_settings.SYSTEM
                + "_"
                + app_settings.SYSTEM_VERSION
            )
            if layer.get("title"):
                file_name = layer.get("title", "")

            if layer.get("data_source", {}).get("format", "") == "tif":
                # if Path(layer.get("local_file_path")).suffix == ".tif":
                pev_lyr_path = preprocess_raster(
                    layer=layer.get("local_file_path"),
                    aoi=aoi,
                    reference_layer_path=reference_layer_path,
                    dst_crs=dst_crs,
                    dst_nodata=dst_nodata,
                    dst_res_x=dst_res_x,
                    dst_res_y=dst_res_y,
                    transform_methods=layer.get("transform_methods", []),
                )
                # upload raster to cdr
                payload = json.dumps(
                    {
                        "raw_data_info": [
                            {
                                "id": layer.get("data_source", {}).get(
                                    "data_source_id"
                                ),
                                "raw_data_type": "tif",
                            }
                        ],
                        "extra_geometries": [],
                        "cma_id": cma_id,
                        "title": layer.get("title", "NeedToSetTitle"),
                        "system": app_settings.SYSTEM,
                        "system_version": app_settings.SYSTEM_VERSION,
                        "transform_methods": layer.get("transform_methods", []),
                        "label_raster": layer.get("label_raster", False),
                        "event_id": event_id,
                    }
                )

                await post_results(
                    file_name=f"{file_name}.tif",
                    file_path=pev_lyr_path,
                    data=payload,
                    file_logger=file_logger,
                )
            elif layer.get("data_source", {}).get("format", "") == "shp":
                # elif Path(layer.get("local_file_path")).suffix == ".zip":
                logger.info("file path has a zip")
                await process_vector_folder(
                    layer=layer,
                    aoi=aoi,
                    reference_layer_path=reference_layer_path,
                    cma_id=cma_id,
                    dst_crs=dst_crs,
                    dst_nodata=dst_nodata,
                    dst_res_x=dst_res_x,
                    dst_res_y=dst_res_y,
                    event_id=event_id,
                    raw_data_info=[
                        {
                            "id": layer.get("data_source", {}).get("data_source_id"),
                            "raw_data_type": "vector",
                        }
                    ],
                    extra_geometries=[],
                    file_name=file_name,
                    file_logger=file_logger,
                )
            else:
                raise Exception(f"Didn't process file {layer.get('local_file_path')}")
        except Exception:
            file_logger.exception(f"ERROR processing layer: {layer}")

    return


async def process_vector_folder(
    layer,
    aoi: Path,
    reference_layer_path: Path,
    cma_id: str,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int,
    event_id: str,
    raw_data_info: list,
    extra_geometries: list,
    file_name: str,
    file_logger,
):
    pev_lyr_path = preprocess_vector(
        layer=layer.get("local_file_path"),
        aoi=aoi,
        reference_layer_path=reference_layer_path,
        dst_crs=dst_crs,
        dst_nodata=dst_nodata,
        dst_res_x=dst_res_x,
        dst_res_y=dst_res_y,
        transform_methods=layer.get("transform_methods"),
    )
    payload = json.dumps(
        {
            "raw_data_info": raw_data_info,
            "extra_geometries": extra_geometries,
            "cma_id": cma_id,
            "title": layer.get("title", "NeedToSetTitle"),
            "system": app_settings.SYSTEM,
            "system_version": app_settings.SYSTEM_VERSION,
            "transform_methods": layer.get("transform_methods", []),
            "label_raster": layer.get("label_raster", False),
            "event_id": event_id,
        }
    )

    await post_results(
        file_name=f"{file_name}.tif",
        file_path=pev_lyr_path,
        data=payload,
        file_logger=file_logger,
    )
