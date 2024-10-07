import fiona
import requests
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


from .utils_preprocessing import preprocess_raster, preprocess_vector

logger: Logger = logging.getLogger(__name__)



from ..settings import app_settings

auth = {
    "Authorization": app_settings.cdr_bearer_token,
}



def create_aoi_geopkg(
    cma,
    dst_dir: Path = Path("./data")
) -> Path:
    # Creating the AOI geopackage
    gdf = gpd.GeoDataFrame(
        {'id': [0]},
        crs = cma.crs,
        geometry = [cma.extent]
    )
    try:
        gdf.to_file(dst_dir / Path(f"aoi.gpkg"), driver="GPKG")
        return dst_dir / Path(f"aoi.gpkg")
    except fiona.errors.TransactionError:
        gdf.to_file(dst_dir / Path(f"aoi.shp"))
        return dst_dir / Path(f"aoi.shp")


def download_reference_layer(
    cma,
    dst_dir: Path = Path("./data")
) -> Path:
    s3_key=parse_s3_url(cma.download_url)[1]
    
    dst_path = dst_dir / Path(cma.download_url).name
    logger.info(f'path {dst_path}')
    download_file(s3_key, dst_path)

    return dst_path


def download_evidence_layer(
    title: str,
    s3_key: str,
    dst_dir: Path
) -> Path:
    local_file = f"{title}{Path(s3_key).suffix}"
    dst_path = dst_dir / local_file
    download_file(s3_key, dst_path)
    
    return dst_path


def parse_s3_url(url: str):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.lstrip('/').split('/')
    bucket = path_parts[0]
    s3_key = '/'.join(path_parts[1:])
    
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
        logger.exception(f"Error downloading file from S3")


def download_evidence_layers(
    evidence_layers,
    dst_dir: Path = Path("./data")
) -> List[Path]:
    # sets evidence layers location
    ev_lyrs_path = dst_dir

    # downloads evidence layers
    # ev_lyrs_paths = []
    for ev_lyr in tqdm(evidence_layers):
        logging.info(f"ev_laer, {ev_lyr}")
        ev_lyr_path = download_evidence_layer(
            title=ev_lyr.get("data_source",{}).get("evidence_layer_raster_prefix"),
            s3_key=parse_s3_url(ev_lyr.get("data_source",{}).get("download_url"))[1],
            dst_dir=ev_lyrs_path
        )
        if ev_lyr_path.suffix == '.zip':
            os.makedirs(ev_lyr_path.parent / ev_lyr_path.stem, exist_ok=True)
            with zipfile.ZipFile(ev_lyr_path, 'r') as zip_ref:
                zip_ref.extractall(ev_lyr_path.parent / ev_lyr_path.stem)
        # ev_lyrs_paths.append(ev_lyr_path)
        ev_lyr['local_file_path']=ev_lyr_path
    return evidence_layers


async def post_results(file_name, file_path, data):
    async with httpx.AsyncClient(timeout=None) as client:
        data_ = {
            "metadata": data  # Marking the part as JSON
        }
        files_ = [("input_file", (file_name, open(file_path, "rb")))]

        logging.debug(f'files to be sent {files_}')
        logging.debug(f'data to be sent {data_}')
        r = await client.post(app_settings.cdr_endpoint_url +"/v1/prospectivity/prospectivity_input_layer", files=files_, data=data_, headers=auth)
        logging.debug(f'Response text from CDR {r.text}')
        r.raise_for_status()
          
        

async def preprocess_evidence_layers(
    evidence_layers,
    aoi: Path,
    reference_layer_path: Path,
    cma_id: str,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int,
    file_logger
) -> List[Path]:
    pev_lyr_paths = []
    for idx, layer in tqdm(enumerate(evidence_layers)):
        try:
            hash_object = hashlib.sha256()
            
            hash_object.update(
                layer.get("data_source",{}).get(
                    "data_source_id"
                    ).encode('utf-8')
                )
            hex_dig = hash_object.hexdigest() + "_" + app_settings.SYSTEM + "_" + app_settings.SYSTEM_VERSION


            if Path(layer.get("local_file_path")).suffix == ".tif":
                pev_lyr_path = preprocess_raster(
                    layer=layer.get("local_file_path"),
                    aoi=aoi,
                    reference_layer_path=reference_layer_path,
                    dst_crs=dst_crs,
                    dst_nodata=dst_nodata,
                    dst_res_x=dst_res_x,
                    dst_res_y=dst_res_y,
                    transform_methods=evidence_layers[idx].get("transform_methods")
                )
                # upload raster to cdr
                payload=json.dumps({
                    "data_source_id":layer.get("data_source",{}).get("data_source_id"),
                    "cma_id":cma_id,
                    "title":"test",
                    "system": app_settings.SYSTEM,
                    "system_version": app_settings.SYSTEM_VERSION,
                    "transform_methods": layer.get("transform_methods")
                })
                
                await post_results(file_name=f"{hex_dig}.tif", file_path=pev_lyr_path, data=payload)

                
            elif Path(layer.get("local_file_path")).suffix == ".zip":
                logging.info("HERE")
                pev_lyr_path = preprocess_vector(
                    layer=layer.get("local_file_path"),
                    aoi=aoi,
                    reference_layer_path=reference_layer_path,
                    dst_crs=dst_crs,
                    dst_nodata=dst_nodata,
                    dst_res_x=dst_res_x,
                    dst_res_y=dst_res_y,
                    transform_methods=evidence_layers[idx].get("transform_methods")
                )
                payload=json.dumps({
                    "data_source_id":layer.get("data_source",{}).get("data_source_id"),
                    "cma_id":cma_id,
                    "title":"test",
                    "system": app_settings.SYSTEM,
                    "system_version": app_settings.SYSTEM_VERSION,
                    "transform_methods": layer.get("transform_methods")
                })
                
                await post_results(file_name=f"{hex_dig}.tif", file_path=pev_lyr_path, data=payload)

                    
            pev_lyr_paths.append(pev_lyr_path)
        except Exception:
            file_logger.exception(f"ERROR processing layer: {layer}")

    
    return pev_lyr_paths
