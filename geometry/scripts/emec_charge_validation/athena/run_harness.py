# F41 conserto 29: runs the EnergyCalculator harness in Athena 23.0.14, with the geometry of the reference sample (ATLAS-P2-RUN4-01-01-00)
# and the four calculators of the EMEC wheels configured as in the simulation (LArG4ECConfig.py, no option changed).
# Usage (after asetup and the setup of the build): python run_harness.py steps.txt athena.txt
import sys
from AthenaConfiguration.AllConfigFlags import initConfigFlags
from AthenaConfiguration.MainServicesConfig import MainServicesCfg
from AthenaConfiguration.ComponentFactory import CompFactory
flags = initConfigFlags()
flags.Input.Files = []
flags.Input.isMC = True
flags.GeoModel.AtlasVersion = "ATLAS-P2-RUN4-01-01-00"
flags.IOVDb.GlobalTag = "OFLCOND-MC15c-SDR-14-05"
flags.Exec.MaxEvents = 1
flags.Input.RunNumber = [330000]
flags.Input.TimeStamp = [1]
flags.Input.LumiBlockNumber = [1]
flags.lock()
cfg = MainServicesCfg(flags)
from McEventSelector.McEventSelectorConfig import McEventSelectorCfg
cfg.merge(McEventSelectorCfg(flags))
from AtlasGeoModel.GeoModelConfig import GeoModelCfg
cfg.merge(GeoModelCfg(flags))
from LArG4EC.LArG4ECConfig import (EMECPosInnerWheelCalculatorCfg, EMECPosOuterWheelCalculatorCfg,
                                   EMECNegInnerWheelCalculatorCfg, EMECNegOuterWheelCalculatorCfg)
for f in (EMECPosInnerWheelCalculatorCfg, EMECPosOuterWheelCalculatorCfg, EMECNegInnerWheelCalculatorCfg, EMECNegOuterWheelCalculatorCfg):
    cfg.merge(f(flags))
cfg.addEventAlgo(CompFactory.EmecHarnessAlg("EmecHarnessAlg", InputFile=sys.argv[1], OutputFile=sys.argv[2]))
sys.exit(not cfg.run().isSuccess())
