"""
EgammaMonitoring configuration helper for expert data quality validation.
"""

from typing import Optional
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
    OutputFile: str = "expert_monitoring.root",
    Directory: str = "Expert-Monitoring",
    InputEventInfoKey: str = "Events",
    InputClusterKey: str = "Clusters",
    InputElectronKey: str = "Electrons",
    InputRingsKey: str = "Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns an EgammaMonitoringMaker instance for expert data quality monitoring.

    :param name: Instance name of the monitoring algorithm.
    :param OutputFile: Path to destination expert monitoring ROOT file.
    :param Directory: Base directory name inside the ROOT file.
    :param InputEventInfoKey: StoreGate key for xAOD::EventInfo.
    :param InputClusterKey: StoreGate key for xAOD::CaloClusterContainer.
    :param InputElectronKey: StoreGate key for xAOD::ElectronContainer.
    :param InputRingsKey: StoreGate key for xAOD::CaloRingsContainer.
    :param OutputLevel: Logging level verbosity.
    :return: Configurable algorithm instance.
    """
    cls = getattr(ROOT, "EgammaMonitoringMaker", getattr(ROOT.Gaugi, "EgammaMonitoringMaker", None))
    return Configurable(
        cls,
        name,
        OutputFile=OutputFile,
        Directory=Directory,
        InputEventInfoKey=InputEventInfoKey,
        InputClusterKey=InputClusterKey,
        InputElectronKey=InputElectronKey,
        InputRingsKey=InputRingsKey,
        OutputLevel=OutputLevel,
    )


# Aliases for convenience and backward compatibility
EgammaMonitoringCfg = EgammaMonitoringMakerCfg
EgammaMonitoring = EgammaMonitoringMakerCfg
EgammaMonitoringMaker = EgammaMonitoringMakerCfg
