"""
EgammaMonitoring configuration helper for expert data quality validation.
"""

from typing import List, Optional
import ROOT
from GaugiKernel import Configurable, LoggingLevel

__all__ = [
    "EgammaMonitoringMakerCfg",
    "EgammaMonitoringCfg",
    "EgammaMonitoringMaker",
    "EgammaMonitoring",
]


def EgammaMonitoringMakerCfg(
    name: str = "EgammaMonitoringMaker",
    Directory: str = "Expert-Monitoring",
    InputEventInfoKey: str = "Events",
    InputClusterKey: str = "Clusters",
    InputElectronKey: str = "Electrons",
    InputRingsKey: str = "Rings",
    InputRingsKeys: Optional[List[str]] = None,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns an EgammaMonitoringMaker instance for expert data quality monitoring.

    Histograms are booked into and managed directly by StoreGate and saved via ComponentAccumulator.

    :param name: Instance name of the monitoring algorithm.
    :param Directory: Base directory name inside the ROOT file.
    :param InputEventInfoKey: StoreGate key for xAOD::EventInfo.
    :param InputClusterKey: StoreGate key for xAOD::CaloClusterContainer.
    :param InputElectronKey: StoreGate key for xAOD::ElectronContainer.
    :param InputRingsKey: StoreGate key for primary xAOD::CaloRingsContainer (backward compatible).
    :param InputRingsKeys: Optional list of StoreGate keys for all xAOD::CaloRingsContainer collections to monitor.
                           If None, defaults to all 6 topologies: [Rings, Rings_Asym, Rings_Cross, Rings_Corner, Rings_Strips, Rings_Custom].
    :param OutputLevel: Logging level verbosity.
    :return: Configurable algorithm instance.
    """
    if InputRingsKeys is None:
        if InputRingsKey == "Rings":
            InputRingsKeys = [
                "Rings",
                "Rings_Asym",
                "Rings_Cross",
                "Rings_Corner",
                "Rings_Strips",
                "Rings_Custom",
            ]
        else:
            InputRingsKeys = [InputRingsKey]

    cls = getattr(ROOT, "EgammaMonitoringMaker", getattr(ROOT.Gaugi, "EgammaMonitoringMaker", None))
    return Configurable(
        cls,
        name,
        Directory=Directory,
        InputEventInfoKey=InputEventInfoKey,
        InputClusterKey=InputClusterKey,
        InputElectronKey=InputElectronKey,
        InputRingsKey=InputRingsKey,
        InputRingsKeys=InputRingsKeys,
        OutputLevel=OutputLevel,
    )


# Aliases for convenience and backward compatibility
EgammaMonitoringCfg = EgammaMonitoringMakerCfg
EgammaMonitoring = EgammaMonitoringMakerCfg
EgammaMonitoringMaker = EgammaMonitoringMakerCfg
