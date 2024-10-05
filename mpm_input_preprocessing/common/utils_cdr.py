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
from ..settings import app_settings
auth = {
    "Authorization": app_settings.cdr_bearer_token,
}
from mpm_input_preprocessing.common.utils_preprocessing import preprocess_raster, preprocess_vector


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
    response = requests.get(cma.download_url)
    response.raise_for_status()
    dst_path = dst_dir / Path(cma.download_url).name
    with open(dst_path, 'wb') as f:
        f.write(response.content)
    return dst_path


def download_evidence_layer(
    title: str,
    url: str,
    dst_dir: Path
) -> Path:
    local_file = f"{title}{Path(url).suffix}"
    response = requests.get(url)
    response.raise_for_status()
    dst_path = dst_dir / local_file
    with open(dst_path, 'wb') as f:
        f.write(response.content)
    return dst_path


def download_evidence_layers(
    evidence_layers,
    dst_dir: Path = Path("./data")
) -> List[Path]:
    # sets evidence layers location
    ev_lyrs_path = dst_dir

    # downloads evidence layers
    # ev_lyrs_paths = []
    for ev_lyr in tqdm(evidence_layers):
        ev_lyr_path = download_evidence_layer(
            title=ev_lyr.data_source.evidence_layer_raster_prefix,
            url=ev_lyr.data_source.download_url,
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
        files_ = [("files", (file_name, open(file_path, "rb")))]
        try:
        
            logging.debug(f'files to be sent {files_}')
            logging.debug(f'data to be sent {data_}')
            r = await client.post(app_settings.cdr_endpoint_url +"/v1/prospectivity/prospectivity_input_layer", files=files_, data=data_, headers=auth)
            logging.debug(f'Response text from CDR {r.text}')
            r.raise_for_status()
          
        except Exception as e:
            logging.error(e)

def preprocess_evidence_layers(
    evidence_layers,
    aoi: Path,
    reference_layer_path: Path,
    cma_id: str,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int,
) -> List[Path]:
    pev_lyr_paths = []
    for idx, layer in tqdm(enumerate(evidence_layers)):
        if layer.local_file_path.suffix == ".tif":
            pev_lyr_path = preprocess_raster(
                layer.local_file_path,
                aoi,
                reference_layer_path,
                dst_crs,
                dst_nodata,
                dst_res_x,
                dst_res_y,
                transform_methods=evidence_layers[idx].transform_methods
            )
            # upload raster to cdr
            payload={
                "data_source_id":layer.get("data_source_id"),
                "cma_id":cma_id,
                "title":"test",
                "system": app_settings.SYSTEM,
                "system_version": app_settings.SYSTEM_VERSION,
                "transform_methods": layer.get("transform_methods")
            }
            post_results(file_name="test.tif", file_path=layer.local_file_path, data=payload)

            
        elif layer.suffix == ".zip":
            pev_lyr_path = preprocess_vector(
                layer.local_file_path,
                aoi,
                reference_layer_path,
                dst_crs,
                dst_nodata,
                dst_res_x,
                dst_res_y,
                transform_methods=evidence_layers[idx].transform_methods
            )
                
        pev_lyr_paths.append(pev_lyr_path)
    
    return pev_lyr_paths
