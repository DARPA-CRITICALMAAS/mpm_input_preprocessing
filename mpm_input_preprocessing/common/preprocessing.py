import logging
import os

from logging import Logger
from typing import List
from pathlib import Path
import numpy as np
import tempfile


from mpm_input_preprocessing.common.utils_cdr import (
    create_aoi_geopkg,
    download_reference_layer,
    download_evidence_layers,
    preprocess_evidence_layers,
    send_label_layer
)

logger: Logger = logging.getLogger(__name__)

from cdr_schemas.cdr_responses.prospectivity import CriticalMineralAssessment, CreateProcessDataLayer

from cdr_schemas.prospectivity_input import SaveProcessedDataLayer


async def preprocess(
    cma: CriticalMineralAssessment,
    evidence_layers: List[CreateProcessDataLayer],
    mineral_sites: List[List[int|float]],
    file_logger
):
    # SRI/Beak your code here.
    """
    Iterate over a CMA's evidence_layers and produce preprocessed layers (raw raster + SaveProcessedDataLayer metadata object)
    for each one given the transform_methods supplied.

    Jataware to hook up sending preprocessed layers (raw raster + SaveProcessedDataLayer metadata object) to CDR once above is complete.
    """

    logger.info("Start preprocess...")

    logger.info(cma)

    # create directory where to save the processed layers
    # data_dir = Path("./data") / Path(cma.cma_id)
    # os.makedirs(data_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / Path(cma.cma_id)
        vector_dir = Path("./data") / Path("vector")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(vector_dir, exist_ok=True)

        # create aoi geopackage
        logger.info("Generating AOI geopackage.")
        aoi_geopkg_path = create_aoi_geopkg(cma, data_dir)

        # download reference layer
        logger.info("Downloading reference layer.")
        reference_layer_path = download_reference_layer(cma, data_dir)

        logger.info(evidence_layers)

        # download evidence layers
        logger.info("Downloading evidence layers.")
        dumped_evidence_layers = [ x.model_dump() for x in evidence_layers]
        evidence_layers = download_evidence_layers(dumped_evidence_layers, data_dir)

        # preprocess evidence layers
        logger.info("Preprocessing evidence layers.")
        await preprocess_evidence_layers(
            dumped_evidence_layers,
            aoi_geopkg_path,
            reference_layer_path,
            cma_id=cma.cma_id,
            dst_crs=cma.crs,
            dst_nodata=np.nan,
            dst_res_x=cma.resolution[0],
            dst_res_y=cma.resolution[1],
            file_logger=file_logger
        )
        await send_label_layer(
            vector_dir=vector_dir,
            cma=cma,
            mineral_sites=mineral_sites,
            aoi=aoi_geopkg_path,
            reference_layer_path=reference_layer_path
        )
        


def test():
    sample_cma = {
        "crs": "ESRI:102008",
        "creation_date": "2024-09-11T20:06:52.487891",
        "mineral": "zinc",
        "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/cmas/ESRI:102008_a74810566af8455a0647d0557d65564c6e040f9ed0e7ce1b44e522e21be61dfd__res0_500_res1_500_zinc/template_raster.tif",
        "cma_id": "ESRI:102008_a74810566af8455a0647d0557d65564c6e040f9ed0e7ce1b44e522e21be61dfd__res0_500_res1_500_zinc",
        "extent": {
            "type": "MultiPolygon",
            "coordinates": [
            [
                [
                [
                    385820.15227487474,
                    551116.0685151932
                ],
                [
                    630239.473767589,
                    514633.5949928133
                ],
                [
                    627495.1847320705,
                    509824.4509869735
                ],
                [
                    623574.6273536625,
                    484778.8174083409
                ],
                [
                    624949.8704247484,
                    477391.08662154403
                ],
                [
                    627365.9495871058,
                    472489.3108194322
                ],
                [
                    627824.0254663525,
                    462110.3913917747
                ],
                [
                    622677.5604249394,
                    447839.661691469
                ],
                [
                    623160.9022814049,
                    439544.1440628673
                ],
                [
                    620279.3303525988,
                    430739.84480827855
                ],
                [
                    617761.6600212803,
                    417114.23705875664
                ],
                [
                    618737.9016848177,
                    395637.47689555504
                ],
                [
                    621669.5896090949,
                    388593.49862094293
                ],
                [
                    620207.2431814509,
                    382702.82515033416
                ],
                [
                    624989.4555344766,
                    374608.5109671446
                ],
                [
                    626474.3587129998,
                    364368.49057778023
                ],
                [
                    632430.5439823631,
                    356364.67192025494
                ],
                [
                    631880.7986259492,
                    346342.64276298595
                ],
                [
                    630188.5605891007,
                    339458.01891669154
                ],
                [
                    632831.6574654614,
                    321644.65142988856
                ],
                [
                    633336.5428888433,
                    313231.12275212497
                ],
                [
                    632127.1386545036,
                    299000.046595155
                ],
                [
                    635761.5014368928,
                    288225.1313722309
                ],
                [
                    641098.6342142064,
                    279225.1878048356
                ],
                [
                    646234.1243117277,
                    273448.5958334569
                ],
                [
                    652540.4378519943,
                    253664.2991255202
                ],
                [
                    653568.0652440668,
                    252462.94064781527
                ],
                [
                    654291.1830610099,
                    246821.94069561348
                ],
                [
                    658918.7044988102,
                    237840.47079281346
                ],
                [
                    661434.6794975584,
                    235954.39421718245
                ],
                [
                    662377.4906013302,
                    231306.5386348137
                ],
                [
                    666908.5124389151,
                    227503.51895577565
                ],
                [
                    671027.557959879,
                    229696.76940888073
                ],
                [
                    675584.8065144079,
                    223155.34090609098
                ],
                [
                    683791.5109001069,
                    222818.1206172521
                ],
                [
                    701414.2965003891,
                    230914.38104336258
                ],
                [
                    716262.9715269386,
                    242495.98441677963
                ],
                [
                    725630.2115495239,
                    252333.8541372553
                ],
                [
                    732071.9918769047,
                    262811.98647829547
                ],
                [
                    739723.6455646125,
                    289240.85734315985
                ],
                [
                    746795.5841606745,
                    304182.2716392856
                ],
                [
                    750636.6025004298,
                    321253.0951884065
                ],
                [
                    752242.9323377232,
                    338696.6997526617
                ],
                [
                    752011.5337134255,
                    365143.0817598144
                ],
                [
                    750094.6815507462,
                    379294.0330331748
                ],
                [
                    747891.4604987736,
                    391510.2267887023
                ],
                [
                    744576.6596468556,
                    402470.88012251677
                ],
                [
                    729868.1547156674,
                    431266.7871183187
                ],
                [
                    722353.8758356911,
                    451523.21269017877
                ],
                [
                    717634.4453448927,
                    460330.27680000005
                ],
                [
                    716180.4654622154,
                    466258.737117931
                ],
                [
                    717841.3036133845,
                    472844.092334839
                ],
                [
                    721888.8450199371,
                    481917.37149060686
                ],
                [
                    722113.614800128,
                    490156.37226127094
                ],
                [
                    719294.2747533699,
                    501341.1130435031
                ],
                [
                    1025309.4011937113,
                    455664.73738045926
                ],
                [
                    1030511.0411734096,
                    439997.0395641124
                ],
                [
                    1037456.4481145354,
                    429421.72021573933
                ],
                [
                    1037398.7992120924,
                    423018.20122303534
                ],
                [
                    1035347.6932191579,
                    415016.07606924634
                ],
                [
                    1037643.303896467,
                    400355.07718679996
                ],
                [
                    1036498.9249747223,
                    385312.3556694159
                ],
                [
                    1032234.4106656493,
                    374764.31578488223
                ],
                [
                    1025495.4424025575,
                    370008.2083445385
                ],
                [
                    1021773.0966644386,
                    381285.8948989565
                ],
                [
                    1026197.4709706893,
                    386701.4298776964
                ],
                [
                    1020759.1551843305,
                    387634.4270852236
                ],
                [
                    1014406.890062008,
                    381256.8863714159
                ],
                [
                    1017565.7326294568,
                    378180.3765206401
                ],
                [
                    1018921.968239163,
                    374118.1684428897
                ],
                [
                    1011386.1106087022,
                    370380.05776691984
                ],
                [
                    1012027.9793071079,
                    359605.88992705016
                ],
                [
                    1009526.700383337,
                    347467.79972338077
                ],
                [
                    997280.9659700472,
                    338391.8926270205
                ],
                [
                    996253.0158043833,
                    324488.6115367966
                ],
                [
                    997669.2034737089,
                    314354.9621565251
                ],
                [
                    994232.2327917618,
                    309605.62226111966
                ],
                [
                    992824.56108039,
                    301821.226015413
                ],
                [
                    989545.372679986,
                    295473.3567038454
                ],
                [
                    985401.3801286411,
                    293236.0979292588
                ],
                [
                    984908.7561938209,
                    287805.0191604499
                ],
                [
                    981103.4716604123,
                    284077.71199198504
                ],
                [
                    978278.0429966949,
                    278418.2809212217
                ],
                [
                    980701.5090558366,
                    270648.12609430397
                ],
                [
                    978520.7706044397,
                    269393.20937318355
                ],
                [
                    982603.2878664227,
                    265003.75476625416
                ],
                [
                    988857.1647800038,
                    267071.44734529266
                ],
                [
                    997147.4875414148,
                    261355.26117650722
                ],
                [
                    1010744.1416670362,
                    257382.6755292035
                ],
                [
                    1014375.189410137,
                    253150.3139304287
                ],
                [
                    1022326.5303661748,
                    249324.21954114604
                ],
                [
                    1027132.6555971594,
                    257388.77906936937
                ],
                [
                    1028924.2154838835,
                    258976.6642213797
                ],
                [
                    1038701.01060377,
                    254903.5073861566
                ],
                [
                    1041848.418753268,
                    249430.51857526114
                ],
                [
                    1048427.7740281237,
                    242740.407370248
                ],
                [
                    1055567.4069225758,
                    239312.1576833388
                ],
                [
                    1061301.4534183668,
                    239556.88198883718
                ],
                [
                    1068310.9918822504,
                    245380.98289106463
                ],
                [
                    1075497.1940691632,
                    246926.66219125057
                ],
                [
                    1081554.0729154528,
                    252682.31471813124
                ],
                [
                    1095342.785819002,
                    259831.42228629848
                ],
                [
                    1100146.3791601202,
                    257801.44706082394
                ],
                [
                    1109942.218536164,
                    259774.23279048555
                ],
                [
                    1115657.7985304396,
                    259790.49082086282
                ],
                [
                    1122891.603928722,
                    267092.83010409906
                ],
                [
                    1138869.294790286,
                    289475.87901353964
                ],
                [
                    1145763.579493637,
                    296899.2597126504
                ],
                [
                    1153199.2356258738,
                    301227.09488418035
                ],
                [
                    1162442.2501110025,
                    309015.7425780963
                ],
                [
                    1173580.358942312,
                    314307.87935343635
                ],
                [
                    1180483.1958967473,
                    320293.69968396786
                ],
                [
                    1196418.6336068043,
                    328632.3964944929
                ],
                [
                    1214261.9365024786,
                    340992.41540196346
                ],
                [
                    1226220.349827875,
                    352414.1153960711
                ],
                [
                    1226897.9927100607,
                    356744.11962420505
                ],
                [
                    1230093.6274922986,
                    360070.6358045233
                ],
                [
                    1235514.8835730115,
                    359784.55502035207
                ],
                [
                    1262308.525162006,
                    383774.4200930255
                ],
                [
                    1273809.7830580608,
                    396165.8892702423
                ],
                [
                    1278124.193358692,
                    403568.69150524813
                ],
                [
                    1291559.5509367625,
                    415923.75463405193
                ],
                [
                    1705938.7458075867,
                    354072.7605605307
                ],
                [
                    1601501.1039515166,
                    40767.71105316583
                ],
                [
                    1597146.4236036767,
                    38055.2911295062
                ],
                [
                    1597100.2132088328,
                    31896.97722729454
                ],
                [
                    1593960.3126026592,
                    30059.939908761848
                ],
                [
                    1592969.6732621095,
                    40530.82940665004
                ],
                [
                    1595314.7354497588,
                    53121.872933883475
                ],
                [
                    1601423.659952866,
                    51867.25642564064
                ],
                [
                    1599511.2868578902,
                    60238.55630897193
                ],
                [
                    1597785.1887820524,
                    63270.34035258407
                ],
                [
                    1594593.5583549167,
                    65748.74880783264
                ],
                [
                    1595762.9717785483,
                    74137.98783249514
                ],
                [
                    1596924.3478007645,
                    81184.23140117171
                ],
                [
                    1598885.3702987218,
                    85080.64713496706
                ],
                [
                    1599407.2983798597,
                    89674.8468038586
                ],
                [
                    1602418.5869148981,
                    94695.55530652055
                ],
                [
                    1607398.779029298,
                    98407.2110220187
                ],
                [
                    1609602.0850914204,
                    101324.40048637392
                ],
                [
                    1608219.2395435248,
                    105680.40370082302
                ],
                [
                    1604387.5839277613,
                    104752.02371785662
                ],
                [
                    1598762.9609891358,
                    97901.29107713769
                ],
                [
                    1589374.065248262,
                    83362.05235163606
                ],
                [
                    1586398.657916493,
                    76434.23121411337
                ],
                [
                    1583191.0004498377,
                    73698.71328267467
                ],
                [
                    1581449.097668316,
                    70203.45972926255
                ],
                [
                    1575648.4522868614,
                    68882.35715894977
                ],
                [
                    1574112.4849496977,
                    65323.73712432238
                ],
                [
                    1582965.9238915737,
                    61611.41479384906
                ],
                [
                    1585792.7276166945,
                    51411.794186641106
                ],
                [
                    1588637.7056457675,
                    48305.32954560626
                ],
                [
                    1584940.1219531896,
                    44099.85486305014
                ],
                [
                    1583791.7694850476,
                    40694.30516185519
                ],
                [
                    1585842.2474785387,
                    39269.59828384955
                ],
                [
                    1582673.693145704,
                    27782.109090206694
                ],
                [
                    1585140.7543040463,
                    26799.599433169657
                ],
                [
                    1581600.1147099559,
                    16151.994205194258
                ],
                [
                    1584940.670639341,
                    13007.079966516865
                ],
                [
                    1586212.8648677373,
                    5989.026547475283
                ],
                [
                    1588411.8040631677,
                    1500.7985046464973
                ],
                [
                    1572617.291779045,
                    -45881.54722029288
                ],
                [
                    1568589.70014582,
                    -45128.72987224673
                ],
                [
                    1557758.3897892162,
                    -37922.57668657222
                ],
                [
                    1552155.4917015356,
                    -27259.201987479937
                ],
                [
                    1537941.5432319082,
                    -37924.69707283601
                ],
                [
                    1532726.095152995,
                    -32347.924653314778
                ],
                [
                    1531433.7012725964,
                    -20296.589721809392
                ],
                [
                    1535048.135879239,
                    -12081.59425608515
                ],
                [
                    1539132.0273283827,
                    -9617.484627720922
                ],
                [
                    1538561.2892490316,
                    -7251.528790115188
                ],
                [
                    1529182.0623984442,
                    -9113.508315499961
                ],
                [
                    1526960.4105208826,
                    -18335.978918261044
                ],
                [
                    1526946.2429582907,
                    -29744.51794509038
                ],
                [
                    1529302.7098121517,
                    -39304.792951394105
                ],
                [
                    1534668.3210624394,
                    -44283.48885549766
                ],
                [
                    1551590.0677317188,
                    -37635.247191329756
                ],
                [
                    1554509.007216093,
                    -40751.333137582216
                ],
                [
                    1554698.315685135,
                    -43906.287604785575
                ],
                [
                    1561633.5962830917,
                    -49643.301684096725
                ],
                [
                    1561951.6727227916,
                    -53074.591448677966
                ],
                [
                    1569453.265391051,
                    -55373.38777237288
                ],
                [
                    1341729.6548793449,
                    -738527.0457579886
                ],
                [
                    -158393.8083739585,
                    -654434.1410976681
                ],
                [
                    385820.15227487474,
                    551116.0685151932
                ]
                ],
                [
                [
                    1595154.2195553875,
                    21727.53650875031
                ],
                [
                    1595181.425519379,
                    22836.28847997598
                ],
                [
                    1595576.7072329114,
                    22994.967679834397
                ],
                [
                    1595154.2195553875,
                    21727.53650875031
                ]
                ],
                [
                [
                    1031166.7964330337,
                    271983.8871854057
                ],
                [
                    1031525.6986118446,
                    265955.9838670917
                ],
                [
                    1027637.4510484798,
                    263655.46499786613
                ],
                [
                    1024922.3635830762,
                    271073.3043155595
                ],
                [
                    1027362.2717560324,
                    274887.074963254
                ],
                [
                    1031166.7964330337,
                    271983.8871854057
                ]
                ]
            ]
            ]
        },
        "resolution": [
            500,
            500
        ],
        "description": "Central-Eastern US Mississippi Valley Type Zinc",
        "cogs": []
        }

    evidence_layers = [
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_LAB",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_LAB",
            "format": "tif",
            "description": "Depth to LAB",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/61da068cd34ed7929400b5a2?f=__disk__1d%2F05%2F98%2F1d059897701dcebcf0d5638106c2388db6d5fd2a",
            "type": "continuous",
            "resolution": [
              6768,
              6768
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/66942b902b864644a0f7a0d2c3aeb388.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "seismic",
            "data_source_id": "Geophysics_LAB_res0_67684_res1_67684_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_LAB_HGM",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_LAB_HGM",
            "format": "tif",
            "description": "Depth to LAB",
            "reference_url": "",
            "type": "continuous",
            "resolution": [
              6768,
              6768
            ],
            "derivative_ops": "HGM",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/6c6e4facecd8408b97329213f361ff70.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "seismic",
            "data_source_id": "Geophysics_LAB_HGM_res0_67684_res1_67684_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Moho",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Moho",
            "format": "tif",
            "description": "Depth to Moho",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/61cdf5f9d34ed79293fc8712?f=__disk__49%2F32%2Fa1%2F4932a153bf3ee36b4dbca8b95f74e1fcaa064370",
            "type": "continuous",
            "resolution": [
              16723,
              16723
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/ab9b64e909fc487191f0e754c50d7309.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "seismic",
            "data_source_id": "Geophysics_Moho_res0_1672273_res1_1672273_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_LAB_HGM_Worms",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_LAB_HGM_Worms",
            "format": "shp",
            "description": "Depth to LAB",
            "reference_url": "",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "HGM, Worms",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/ef052315dc2b44978af0ad049604749f.zip",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "seismic",
            "data_source_id": "Geophysics_LAB_HGM_Worms_res0_-1_res1_-1_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Gravity_Bouguer_Up30km_HGM",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Gravity_Bouguer_Up30km_HGM",
            "format": "tif",
            "description": "Gravity Bouguer upward continued (30km)",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9f02d34eb622f692f96c?f=__disk__ec%2F2d%2Fc3%2Fec2dc37896472b4a15e8b254b078355795e7aa75",
            "type": "continuous",
            "resolution": [
              2118,
              2118
            ],
            "derivative_ops": "HGM",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/70ce75cbcce94d879ef45557306584cc.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "gravity",
            "data_source_id": "Geophysics_Gravity_Bouguer_Up30km_HGM_res0_211779_res1_211779_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "State Geologic Map Compilation (SGMC)",
          "data_source": {
            "evidence_layer_raster_prefix": "State Geologic Map Compilation (SGMC)",
            "format": "shp",
            "description": "",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/5888bf4fe4b05ccb964bab9d?f=__disk__a0%2Fff%2F7e%2Fa0ff7e013c776a2f4b408be5b4a3e55ed91176b7",
            "type": "categorical",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/47b2431f8282491b85cc1e3059fadb2c.zip",
            "publication_date": "2017-06-30T00:00:00",
            "category": "geology",
            "subcategory": "lithology, age",
            "data_source_id": "State Geologic Map Compilation (SGMC)_res0_-1_res1_-1_cat_LayerCategoryGEOLOGY",
            "DOI": "",
            "authors": [
              "Horton, J.D."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Gravity_Bouguer_Up30km_HGM_Worms",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Gravity_Bouguer_Up30km_HGM_Worms",
            "format": "shp",
            "description": "Gravity Bouguer upward continued (30km)",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9f02d34eb622f692f96c?f=__disk__ef%2Ffe%2Fcb%2Feffecbe42eee9535979fafc40a74fa4c0841d92a",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "HGM, Worms",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/73108a8cb1164e8fb25c51847f4519ea.zip",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "gravity",
            "data_source_id": "Geophysics_Gravity_Bouguer_Up30km_HGM_Worms_res0_-1_res1_-1_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP",
            "format": "tif",
            "description": "Magnetic RTP",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__d3%2F18%2Fab%2Fd318ab1430ba76afdea6e96505fed52536ec9dec",
            "type": "continuous",
            "resolution": [
              771,
              771
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/4904a9d6d38e4c9388ff8e2b93a652c2.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_res0_7705_res1_7705_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP_HGM",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP_HGM",
            "format": "tif",
            "description": "Magnetic RTP",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__bd%2Fcd%2F37%2Fbdcd3744caea2f37ccb681f2d2a23c947376b7bf",
            "type": "continuous",
            "resolution": [
              771,
              771
            ],
            "derivative_ops": "HGM",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/119cfe3d7b074c0e9a47848f1258b8d6.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_HGM_res0_7705_res1_7705_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Gravity_Isostatic",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Gravity_Isostatic",
            "format": "tif",
            "description": "Isostatic Gravity",
            "reference_url": "",
            "type": "continuous",
            "resolution": [
              3892,
              3892
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/a00d3291f0a149739492d37e14773b68.tif",
            "publication_date": "1900-01-01T00:00:00",
            "category": "geophysics",
            "subcategory": "gravity",
            "data_source_id": "Geophysics_Gravity_Isostatic_res0_389199_res1_389199_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": []
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP_HGM_Worms",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP_HGM_Worms",
            "format": "shp",
            "description": "Magnetic RTP",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__dc%2Fa2%2Fc4%2Fdca2c4a3f6f32b2f63853bbb00748b949c74e95a",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "HGM, Worms",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/bef663ed9ba24c5ba02145499daa541c.zip",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_HGM_Worms_res0_-1_res1_-1_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP_Long-Wavelength_HGM",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP_Long-Wavelength_HGM",
            "format": "tif",
            "description": "Magnetic RTP long-wavelength",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__0e%2F80%2F2b%2F0e802be2923e66bb43bed39c26aedde179168295",
            "type": "continuous",
            "resolution": [
              1787,
              1787
            ],
            "derivative_ops": "HGM",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/3de3861e3d924f54b86e72aaef90b012.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_Long-Wavelength_HGM_res0_178735_res1_178735_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geology_PassiveMargins_Proximity",
          "data_source": {
            "evidence_layer_raster_prefix": "Geology_PassiveMargins_Proximity",
            "format": "shp",
            "description": "Proximity to passive margins",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619550d9d34eb622f69061b7?f=__disk__73%2Fad%2Fcc%2F73adcc1f269200ae41fc4ca5cae1b7899a27d64c",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "Proximity",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/5937b001be42415dafa3f6e96277d273.zip",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geology",
            "subcategory": "",
            "data_source_id": "Geology_PassiveMargins_Proximity_res0_-1_res1_-1_cat_LayerCategoryGEOLOGY",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP_Long-Wavelength",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP_Long-Wavelength",
            "format": "tif",
            "description": "Magnetic RTP long-wavelength",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__62%2Fea%2Fb6%2F62eab67c9dfdc2962156624780bd57397d6beff9",
            "type": "continuous",
            "resolution": [
              1666,
              1666
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/f7fdf09e4d5c4b708e3167869f72f6b8.tif",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_Long-Wavelength_res0_166645_res1_166645_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_Mag_RTP_Long-Wavelength_HGM_Worms",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_Mag_RTP_Long-Wavelength_HGM_Worms",
            "format": "shp",
            "description": "Magnetic RTP long-wavelength ",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/619a9a3ad34eb622f692f961?f=__disk__2a%2F8f%2F2c%2F2a8f2ced08239dcc7895ffa728c8e94093c98e47",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "HGM, Worms",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/71a1fab3400d428890935e99870b3110.zip",
            "publication_date": "2023-08-14T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetics",
            "data_source_id": "Geophysics_Mag_RTP_Long-Wavelength_HGM_Worms_res0_-1_res1_-1_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "McCafferty, A.E.",
              "San Juan, C.A.",
              "Lawley, C.J.M.",
              "Graham, G.E.",
              "Gadd, M.G.",
              "Huston, D.L.",
              "Kelley, K.D.",
              "Paradis, S.",
              "Peter, J.M.",
              "and Czarnota, K."
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geology_Faults_Proximity",
          "data_source": {
            "evidence_layer_raster_prefix": "Geology_Faults_Proximity",
            "format": "shp",
            "description": "Proximity to faults",
            "reference_url": "https://www.sciencebase.gov/catalog/file/get/589097b1e4b072a7ac0cae23?f=__disk__53%2F9e%2Fca%2F539eca35cacf525a58cbb2807a81ddc11a71a3ed",
            "type": "continuous",
            "resolution": [
              -1,
              -1
            ],
            "derivative_ops": "Proximity",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/90164748f169417390286ee3898af0d4.zip",
            "publication_date": "2020-09-02T00:00:00",
            "category": "geology",
            "subcategory": "",
            "data_source_id": "Geology_Faults_Proximity_res0_-1_res1_-1_cat_LayerCategoryGEOLOGY",
            "DOI": "",
            "authors": [
              "U.S. Geological Survey"
            ]
          }
        },
        {
          "transform_methods": [
            "log",
            "minmax"
          ],
          "title": "Geophysics_MT2023_30km",
          "data_source": {
            "evidence_layer_raster_prefix": "Geophysics_MT2023_30km",
            "format": "tif",
            "description": "30km",
            "reference_url": "https://ds.iris.edu/files/products/emc/emc-files/CONUS-MT-2023.r0.0-n4.nc",
            "type": "continuous",
            "resolution": [
              8715,
              8715
            ],
            "derivative_ops": "",
            "download_url": "https://s3.amazonaws.com/public.cdr.land/prospectivity/inputs/63f39e152189477d90c24a2700ba183f.tif",
            "publication_date": "2023-01-01T00:00:00",
            "category": "geophysics",
            "subcategory": "magnetotellurics",
            "data_source_id": "Geophysics_MT2023_30km_res0_87150_res1_87150_cat_LayerCategoryGEOPHYSICS",
            "DOI": "",
            "authors": [
              "Murphy, B.S.",
              "Bedrosian, P.",
              "Kelbert, A."
            ]
          }
        }
    ]

    cma = CriticalMineralAssessment(cma_id=sample_cma["cma_id"],
                                    download_url=sample_cma["download_url"],
                                    crs=sample_cma["crs"],
                                    mineral=sample_cma["mineral"],
                                    extent=sample_cma["extent"],
                                    resolution=sample_cma["resolution"],
                                    description=sample_cma["description"],
                                    creation_date=sample_cma["creation_date"]
                                    )

    evidence_layer_objects = [CreateProcessDataLayer(**x) for x in evidence_layers]

    preprocess(cma, evidence_layer_objects)
