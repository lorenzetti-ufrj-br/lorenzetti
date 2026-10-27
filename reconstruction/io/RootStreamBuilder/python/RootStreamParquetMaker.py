__all__ = ["RootStreamParquetMaker", "RootStreamParquetMakerCfg"]

import ROOT
from typing import List, Optional
from GaugiKernel import Configurable


def RootStreamParquetMakerCfg(
    name: str = "RootStreamParquetMaker",
    OutputFile: str = "output.parquet",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputClusterKey: str = "CaloClusters",
    InputRingerKeys: Optional[List[str]] = None,
    InputRingerL0Key: str = "RingsL0",
    InputTruthClusterKey: str = "TruthClusters",
    InputTruthRingerKeys: Optional[List[str]] = None,
    InputTruthElectronKey: str = "TruthElectrons",
    InputElectronKey: str = "Electrons",
    OutputLevel: int = 0,
) -> Configurable:
    """
    Creates a RootStreamParquetMaker algorithm for dumping flat analysis variables into an Apache Parquet file.
    """
    if InputRingerKeys is None:
        InputRingerKeys = ["Rings"]
    elif isinstance(InputRingerKeys, str):
        InputRingerKeys = [InputRingerKeys]

    if InputTruthRingerKeys is None:
        InputTruthRingerKeys = ["TruthRings"]
    elif isinstance(InputTruthRingerKeys, str):
        InputTruthRingerKeys = [InputTruthRingerKeys]

    return Configurable(
        ROOT.RootStreamParquetMaker,
        name=name,
        OutputFile=OutputFile,
        InputEventKey=InputEventKey,
        InputTruthKey=InputTruthKey,
        InputSeedsKey=InputSeedsKey,
        InputClusterKey=InputClusterKey,
        InputRingerKeys=InputRingerKeys,
        InputRingerL0Key=InputRingerL0Key,
        InputTruthClusterKey=InputTruthClusterKey,
        InputTruthRingerKeys=InputTruthRingerKeys,
        InputTruthElectronKey=InputTruthElectronKey,
        InputElectronKey=InputElectronKey,
        OutputLevel=OutputLevel,
    )


RootStreamParquetMaker = RootStreamParquetMakerCfg
