import fiona
import requests
import os
import zipfile

from pathlib import Path
import geopandas as gpd
from tqdm import tqdm
from typing import Union, List
import numpy as np

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
    ev_lyrs_paths = []
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
        ev_lyrs_paths.append(ev_lyr_path)
    return ev_lyrs_paths


def preprocess_evidence_layers(
    layers: Path,
    aoi: Path,
    reference_layer_path: Path,
    dst_crs: str,
    dst_nodata: Union[None, float],
    dst_res_x: int,
    dst_res_y: int
) -> List[Path]:
    pev_lyr_paths = []
    for layer in tqdm(layers):
        if layer.suffix == ".tif":
            pev_lyr_path = preprocess_raster(
                layer,
                aoi,
                reference_layer_path,
                dst_crs,
                dst_nodata,
                dst_res_x,
                dst_res_y
            )
        elif layer.suffix == ".zip":
            pev_lyr_path = preprocess_vector(
                layer,
                aoi,
                reference_layer_path,
                dst_crs,
                dst_nodata,
                dst_res_x,
                dst_res_y
            )
        pev_lyr_paths.append(pev_lyr_path)
    return pev_lyr_paths
