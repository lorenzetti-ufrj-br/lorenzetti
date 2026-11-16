#!/usr/bin/env python3
"""
Script: gen_minbias.py
Purpose: Generates minimum bias events using Pythia8 and the Pileup filter.
Usage:
    gen_minbias.py -o output.root --nov 100 [options]
"""

import os
from typing import List
from typing_extensions import Annotated
import typer

from GaugiKernel import parallel_job, LoggingLevel
from GenKernel import Pythia8Cfg as Pythia8, EventTapeCfg as EventTape
from filters import PileupCfg as Pileup, FixedRegionCfg as FixedRegion


datapath = os.environ.get("LORENZETTI_EVTGEN_DATA_DIR", "")
PILEUP_FILE = f"{datapath}/minbias_config.cmnd"


@parallel_job
def main(
    events: List[int],
    output_file: str,
    seed: int,
    run_number: Annotated[int, typer.Option("--run-number", help="The run number.")] = 0,
    output_level: Annotated[str, typer.Option("--output-level", help="The output level messenger.")] = "INFO",
    eta_max: Annotated[float, typer.Option("--eta-max", help="Maximum Eta.")] = 3.2,
    pileup_per_bunch_crossing: Annotated[float, typer.Option("--pileup-per-bunch-crossing", help="Fixed number of pileup for each bunch crossing.")] = -1.0,
    bc_id_start: Annotated[int, typer.Option("--bc-id-start", help="The bunch crossing id start.")] = -21,
    bc_id_end: Annotated[int, typer.Option("--bc-id-end", help="The bunch crossing id end.")] = 4,
    pileup_file: Annotated[str, typer.Option("--pileup-file", help="The pythia pileup configuration file.")] = PILEUP_FILE,
    pt_min_charged: Annotated[
        float,
        typer.Option(
            "--pt-min-charged",
            help="Minimum pT (GeV) of the charged particles passed to the simulation. "
            "The cut stands in for the solenoid field when the field is not simulated; "
            "use 0 (as ATLAS, which applies no particle cut) when the field is simulated.",
        ),
    ] = 0.7,
    pt_min_neutral: Annotated[
        float,
        typer.Option(
            "--pt-min-neutral",
            help="Minimum pT (GeV) of the neutral particles passed to the simulation. "
            "Use 0 to keep every particle, as ATLAS does.",
        ),
    ] = 0.05,
    sigma_z: Annotated[
        float,
        typer.Option(
            "--sigma-z",
            help="Gaussian spread (RMS, in mm) of the collision vertex along the beam axis.",
        ),
    ] = 56.0,
    sigma_t: Annotated[
        float,
        typer.Option(
            "--sigma-t",
            help="Gaussian spread (RMS, in ps) of the collision time.",
        ),
    ] = 200.0,
):
    """
    Generates minimum bias events using Pythia8 and the Pileup filter.
    """
    outputLevel = LoggingLevel.toC(output_level)

    tape = EventTape("EventTape", OutputFile=output_file, RunNumber=run_number)

    # dummy seed to store all pileup particles
    tape += FixedRegion("Seed", Eta=0.0, Phi=0.0)

    pileup = Pileup(
        "Pileup",
        Pythia8("MBGenerator", File=pileup_file, Seed=seed),
        EtaMax=eta_max,
        Select=2,
        PileupAvg=0.0,
        PileupSigma=0.0,
        PileupPerBunch=pileup_per_bunch_crossing,
        BunchIdStart=bc_id_start,
        BunchIdEnd=bc_id_end,
        OutputLevel=outputLevel,
        DeltaEta=999.0,
        DeltaPhi=999.0,
        PtMinCharged=pt_min_charged,
        PtMinNeutral=pt_min_neutral,
        VertexSigmaZ=sigma_z,
        VertexSigmaT=sigma_t,
    )
    tape += pileup
    tape.run(events)


if __name__ == "__main__":
    main()
