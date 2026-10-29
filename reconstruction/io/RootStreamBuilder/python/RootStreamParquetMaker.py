__all__ = ["RootStreamParquetMaker", "RootStreamParquetMakerCfg"]

import ROOT
from typing import List, Optional, Dict
from GaugiKernel import Configurable


def RootStreamParquetMakerCfg(
    name: str = "RootStreamParquetMaker",
    OutputFile: str = "output.parquet",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputClusterKey: str = "CaloClusters",
    InputRingerKeys: Optional[List[str]] = None,
    InputElectronKey: str = "Electrons",
    Schema: Optional[Dict[str, str]] = None,
    OutputLevel: int = 0,
) -> Configurable:
    """
    Creates a RootStreamParquetMaker algorithm for dumping flat analysis variables into an Apache Parquet file.
    """
    if InputRingerKeys is None:
        InputRingerKeys = ["Rings"]
    elif isinstance(InputRingerKeys, str):
        InputRingerKeys = [InputRingerKeys]

    if Schema is None:
        Schema = {}

    return Configurable(
        ROOT.RootStreamParquetMaker,
        name=name,
        OutputFile=OutputFile,
        InputEventKey=InputEventKey,
        InputTruthKey=InputTruthKey,
        InputSeedsKey=InputSeedsKey,
        InputClusterKey=InputClusterKey,
        InputRingerKeys=InputRingerKeys,
        InputElectronKey=InputElectronKey,
        Schema=Schema,
        OutputLevel=OutputLevel,
    )


RootStreamParquetMaker = RootStreamParquetMakerCfg
