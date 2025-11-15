
## Geant4 Simulation
The Geant4 simulation step is essential for accurately modeling the passage of particles through matter. It simulates the interactions of particles with the detector materials, allowing us to understand how particles lose energy, scatter, and produce secondary particles. This step is crucial for obtaining realistic hit information that will be used in subsequent analysis stages.

To run the Geant4 simulation, we typically use the `simu_trf.py` script, which takes the output from the event generation step as input. The script can be configured to enable various features, such as magnetic fields, which are important for simulating charged particle trajectories accurately.

An example command to run the Geant4 simulation is as follows:


## Event Generation Process
The event generation process is a critical first step in our simulation pipeline. It involves creating simulated particle interactions that mimic real-world physics events. This process is typically carried out using specialized scripts, such as `gen_zee.py`, which are designed to generate events based on specific parameters and configurations.

During event generation, we define various parameters, including the number of events to generate, the output file format, and the characteristics of the particles involved. The script utilizes a random number generator to simulate the inherent uncertainties in particle interactions, ensuring that the generated events are representative of actual experimental conditions.

The generated events can then be used for further analysis, including shower propagation, digitalization, and event reconstruction. This allows researchers to study the properties of particles and their interactions in a controlled environment, facilitating a deeper understanding of high-energy physics phenomena.

# Reconstruction

This document provides a comprehensive overview of the reconstruction process in our simulation pipeline. It outlines the key steps involved, from event generation to event reconstruction, and highlights the tools and scripts used at each stage. The goal is to ensure a clear understanding of the workflow and facilitate the implementation of the simulation framework. The simulation pipeline has four main steps:

* Event generation
* Shower propagation
* Digitalization
* Event reconstruction


## Event generation:


Let's create a Z boson decay into an electron-positron pair using the `gen_zee.py` command. 🎉 This process is crucial for simulating the interactions that occur in high-energy physics experiments. By generating these events, we can study the properties of the Z boson and its decay channels in detail. 

To initiate the event generation, we specify parameters such as the average pileup, event number, and output file name. This allows us to customize the simulation according to our experimental needs.


```bash
Usage: gen_zee.py [--run-number RUN_NUMBER] [--output-level OUTPUT_LEVEL]
                  [--eta-max ETA_MAX] [--force-forward-electron]
                  [--zero-vertex-particles] [--zee-file ZEE_FILE] [-e EVENT_NUMBERS] -o
                  OUTPUT_FILE [-s SEED] [--nov NUMBER_OF_EVENTS]
                  [--events-per-job EVENTS_PER_JOB] [-nt NUMBER_OF_THREADS] [-m]
                  [--overwrite] [--job-file JOB_FILE]

Options:
  --run-number RUN_NUMBER
                        The run number.
  --output-level OUTPUT_LEVEL
                        The output level messenger.
  --eta-max ETA_MAX     The eta max used in generator.
  --force-forward-electron
                        Force at least one electron into forward region.
  --zero-vertex-particles
                        Fix the z vertex position in simulation to zero for all selected
                        particles. It is applied only at G4 step, not in generation.
  --zee-file ZEE_FILE   The pythia zee file configuration.
  -e, --event-numbers EVENT_NUMBERS
                        The event number list separated by ','. e.g. --event-numbers
                        '0,1,2,3'
  -o, --output-file OUTPUT_FILE
                        The output file.
  -s, --seed SEED       The pythia seed (zero is the clock system)
  --nov, --number-of-events NUMBER_OF_EVENTS
                        The total number of events to run.
  --events-per-job EVENTS_PER_JOB
                        The number of events per job
  -nt, --number-of-threads NUMBER_OF_THREADS
                        The number of threads
  -m, --merge           Merge all files.
  --overwrite           Rerun all jobs.
  --job-file JOB_FILE   The JSON file used to configure this job automatically by
                        overwritting some arguments.
```


Now, lets create a command to run 100 events, 10 events per job using 10 threads. In the end, we will merge all files using `--merge` command.
Let's run our event generation! 🎉

To generate 100 events, with 10 events per job using 10 threads, and merge all files at the end, we can use the following command:


This command creates minimum bias files using the initial seed provided by the user. Each bunch crossing will be filled with pileup equal to the number specified by the `--pileup-per-bunch-crossing` parameter, ensuring that `--eta-max` ($\eta_{max}\leq2.5$). In total, 100 events will be generated, with 10 events per job, utilizing only one thread.


This command will generate jet files, producing a total of 100 events, with 10 events per job, utilizing 10 threads. The initial seed is set to 512, and the run number corresponds to the current date provided by the user.

The job configuration can be specified using the `--job-file` parameter, allowing the user to provide a JSON file that overrides the default parameters for the job execution.

gen_zee.py -o Zee.EVT.root --nov 100 --events-per-job 10 -nt 10 --merge


```
gen_zee.py -o Zee.EVT.root --nov 10 --events-per-job 1 -nt 5
```

It is also possible to use different simulators (`gun`) to generate the inputs for the framework. For this, it is required to produce HepMC-compatible files after the simulation. These files may be used as inputs for the `event filters` stage. See details below on the `generator/scripts/hepmc`.


## Simulation

This is an examplete how to propagate the particles through the `Geant4` module (considering the file produced on the first example step):

```
simu_trf.py -i EVT.root -o HIT.root --enableMagneticField
```

##  Digitalization

The digitalization process may be configured to use different energy estimation methods such as Optimal Filter (OF) and Constrained Optimal Filter (COF). It is also possible to simulate the crosstalk effect between adjacent calorimeter cells. More details on how to use such features, check the Customization section. In the digitalization step, it is used second step output to feed `digit_trf.py` script. For instance: 

```
digit_trf.py -i HIT.root -o ESD.root
```

Some customization concerning about CrossTalk simulation and energy estimation methods changes:

- ```--simulateCrossTalk```: this simulates the crosstalk efect on the calorimeter cells
- ```HadEnergyEstimationCOF```: this change the energy estimation method on the hadronic calorimeter. Setting this as ```True``` enables the ConstraneidOptimalFilter to be used in place of the regular OptimalFilter on Hadronic layers.

An example for full customized digitalization step:

```
digit_trf.py -i HIT.root -o ESD.root --simulateCrossTalk -c "from CaloCellBuilder import CaloFlags as flags; flags.HadEnergyEstimationCOF=True"
```

It is now also possible to inject anomalies associated with detector defects in this simulation step.
We distinguish 2 types of anomalies: anomalies related to inactive (dead) detector modules or increased noise in cells associated with a physics signal.
For this, the file `reconstruction/io/RootStreamBuilder/python/RootStreamFlags.py` should be modified (select the type of anomaly and concerned cells etc.) and the ```doDefects``` should be used when running `digit_trf.py`.
For example:
 
```
digit_trf.py -i HIT.root -o ESD.root --doDefects --noiseFactor 20
```
multiplies the standard deviation of the default noise in cells with physics signal by 20 (```noiseFactor``` is not needed for dead detector modules).


### Event Reconstruction

Use the third step output to feed `reco_trf.py` script. For instance:

```
reco_trf.py -i ESD.root -o AOD.root
```

A set of examples files for each step can be found at the ```project drive``` folder [here](https://drive.google.com/drive/folders/1z3h6kP0VTVNml4sIQ8sB6eZtwXnrAdtG?usp=share_link). These small examples are for `Zee` decay.




It is possible to configure some algorithms inside of the simulation using the pre-exec parameter. Here let's configure the `KeepCells` parameter from `NtupleHitMaker` algorithm to hold a list of cells by hash number. This strategy can be used in the anamalyes simulation.