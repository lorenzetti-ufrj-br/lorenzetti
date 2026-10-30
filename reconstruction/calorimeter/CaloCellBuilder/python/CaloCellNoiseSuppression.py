__all__ = [
    "CaloCellNoiseSuppression",
    "CaloCellNoiseSuppressionCfg",
    "CaloCellNoiseSupression",
    "CaloCellNoiseSupressionCfg",
    "CaloCellFilter",
    "CaloCellFilterCfg",
]

import ROOT
from GaugiKernel import Configurable, LoggingLevel


def CaloCellNoiseSuppressionCfg(
    name: str = "CaloCellNoiseSuppression",
    InputCellsKey: str = "Cells_original",
    OutputCellsKey: str = "Cells",
    SigmaThreshold: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    r"""
    Creates a CaloCellNoiseSuppression algorithm that filters reconstructed calorimeter cells
    based on their electronic noise sigma threshold ($E > \text{threshold} \times \sigma$).

    Args:
        name: Algorithm name.
        InputCellsKey: Key of the input unfiltered CaloCellContainer.
        OutputCellsKey: Key of the output filtered CaloCellContainer.
        SigmaThreshold: Multiplier threshold for noise cut (default: 2.0).
        OutputLevel: Logging verbosity level.
    """
    return Configurable(
        ROOT.CaloCellNoiseSuppression,
        name,
        InputCellsKey=InputCellsKey,
        OutputCellsKey=OutputCellsKey,
        SigmaThreshold=SigmaThreshold,
        OutputLevel=OutputLevel,
    )


# Aliases
CaloCellNoiseSuppression = CaloCellNoiseSuppressionCfg
CaloCellNoiseSupressionCfg = CaloCellNoiseSuppressionCfg
CaloCellNoiseSupression = CaloCellNoiseSuppressionCfg
CaloCellFilterCfg = CaloCellNoiseSuppressionCfg
CaloCellFilter = CaloCellNoiseSuppressionCfg
