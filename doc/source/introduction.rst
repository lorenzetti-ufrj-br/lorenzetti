Introduction
============

.. image:: https://zenodo.org/badge/370090835.svg
   :target: https://zenodo.org/badge/latestdoi/370090835
   :alt: DOI

.. image:: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/pages.yml/badge.svg
   :target: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/pages.yml
   :alt: pages status

.. image:: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/reco_sequence.yml/badge.svg
   :target: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/reco_sequence.yml
   :alt: reco status

.. image:: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/anomaly_sequence.yml/badge.svg
   :target: https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/anomaly_sequence.yml
   :alt: anomaly status

.. image:: https://github.com/lps-ufrj-br/maestro-lightning/actions/workflows/flow.yml/badge.svg
   :target: https://github.com/lps-ufrj-br/maestro-lighning/actions/workflows/flow.yml
   :alt: maestro status

Lorenzetti is a **dedicated HEP framework** conceptualized to streamline the Research & Development (R&D) of **calorimetry signal processing**, **reconstruction**, and **triggering algorithms**. While modern LHC experiments rely on massive, monolithic software stacks, Lorenzetti provides a **lightweight, modular, and stand-alone** environment that grants researchers direct access to high-fidelity simulation data. Built upon the robust **Geant4** toolkit, Lorenzetti simulates the complete physics of particle showers within complex detector geometries. However, unlike general-purpose simulators, it focuses deeply on the **readout chain**: transforming raw energy deposits into realistic electronic pulses, digitizing them, and reconstructing the original particle properties.

This framework addresses a critical gap in the community: **Access to quality data**. Experiment-specific data is often restricted or difficult to generate for outsiders. Lorenzetti democratizes this by establishing a standard reference for:

*   **Algorithm Development**: Fast prototyping of filters (Optimal Filtering, Wiener), clustering algorithms, and jet reconstruction.
*   **Machine Learning**: Generating massive, labelled datasets ideal for training Neural Networks (e.g., for *anomaly detection*, *pileup mitigation*, or *super-resolution*).
*   **Trigger Studies**: Simulating hardware-level constraints to test fast decision-making logic.

Advanced Pileup Simulation via Overlay
--------------------------------------

One of Lorenzetti's most defining features is its ability to realistically simulate **high-luminosity environments** through a sophisticated **Overlay Strategy**. High Energy Physics experiments often face the challenge of **Pileup**—multiple proton-proton collisions occurring simultaneously. Lorenzetti accurately models this by overlaying background "Minimum Bias" events onto the signal event of interest.

Crucially, it handles both **In-Time Pileup** (simultaneous collisions) and **Out-of-Time Pileup** (signals from previous or subsequent bunch crossings that distort the current measurement). This is achieved by convolving the energy deposits with the detector's realistic **electronic pulse shapes** over a configurable time window. This setup provides a perfect playground for developing cutting-edge **Pileup Mitigation algorithms** (e.g., using timing information or deep learning) to recover clean signals from high-noise backgrounds, mimicking the harsh conditions of the **HL-LHC**.

Described fully in `Computer Physics Communications (2023) <https://doi.org/10.1016/j.cpc.2023.108671>`_, Lorenzetti serves as a "virtual testbeam," enabling the scientific community to validate novel ideas independently of major collaborations.

Citations
---------

Please cite the following paper if you use the software:

    **Lorenzetti Showers: A general-purpose framework for supporting signal reconstruction and triggering with calorimeters**
    *Computer Physics Communications*, Volume 286, 2023, 108671.
    DOI: `10.1016/j.cpc.2023.108671 <https://doi.org/10.1016/j.cpc.2023.108671>`_

Directory Structure
-------------------

Here is an overview of the repository structure:

.. code-block:: text

    📂 lorenzetti/
    ├── 📂 core/             # Core libraries, utilities, and common tools.
    ├── 📂 events/           # Event data models (EDM) and ROOT I/O handling definitions.
    ├── 📂 generator/        # Physics event generator interfaces (e.g., Pythia8).
    ├── 📂 geometry/         # Detector geometry construction and definitions using Geant4.
    ├── 📂 reconstruction/   # Algorithms for signal processing and object reconstruction.
    ├── 📂 docs/             # Documentation, guides, and Jupyter notebook tutorials.
    ├── 📂 examples/         # Scripts and configuration examples for large-scale productions.
    ├── 📂 ci_tests/         # Continuous Integration checks and validation workflows.
    ├── 📄 CMakeLists.txt    # Main CMake configuration file.
    ├── 📄 Makefile          # Shortcut commands for building and testing.

Installation
------------

The recommended way to use Lorenzetti is via pre-built container images (**Docker** or **Singularity**), which come with all dependencies pre-installed.

Singularity (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    singularity pull docker://lorenzetti/lorenzetti:latest
    singularity run lorenzetti_latest.sif

Manual Build
~~~~~~~~~~~~

For development, you can clone and build the source inside the container:

.. code-block:: bash

    git clone https://github.com/lorenzetti-ufrj-br/lorenzetti.git && cd lorenzetti
    make
    source build/lzt_setup.sh

Validation
----------

Lorenzetti is rigorously tested using Github Actions. The validation workflow includes:

1.  **Event Generation**: ``gen_zee.py``, ``gen_jets.py``, ``gen_minbias.py``
2.  **Simulation**: ``simu_trf.py`` (Hit generation)
3.  **Merging**: ``merge_trf.py`` (Pileup mixing)
4.  **Digitalization**: ``digit_trf.py`` (Electronic signal simulation)
5.  **Reconstruction**: ``reco_trf.py`` (Object reconstruction)
6.  **Analysis**: ``ntuple_trf.py`` (Root Ntuple dumping)

Detector Construction (Version 1)
---------------------------------

The standard detector in Lorenzetti aims to mimic the properties of modern high-granularity calorimeters used in LHC experiments (such as ATLAS). It is constructed as a **cylindrical 4π detector** with two main systems:

.. figure:: _static/images/cut_view.png
   :alt: Lorenzetti Detector Geometry (Simplified)
   :align: center
   :width: 80%

   **Figure 1**: Lorenzetti Detector Geometry showing ECAL and HCAL layers (Simplified).

.. list-table::
   :widths: 33 33
   :align: center

   * - .. figure:: _static/images/front_view.png
          :alt: Detector Front View
          :align: center
          :width: 100%

          **Front View**
     - .. figure:: _static/images/lateral_view.png
          :alt: Detector Lateral View
          :align: center
          :width: 100%

          **Lateral View**
 

Electromagnetic Calorimeter (ECAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A sampling calorimeter designed to measure electrons and photons with high precision.

*   **Material**: **Lead** (Pb) absorber plates interleaved with **Liquid Argon** (LAr) as the active medium.
*   **Structure**:
    *   **Pre-Sampler**: A thin layer to correct for energy loss upstream.
    *   **Layer 1 (Strips)**: Finely segmented (Δη ≈ 0.003) for π⁰/γ separation.
    *   **Layer 2 (Middle)**: The thickest layer (55 radiation lengths) containing most of the shower energy.
    *   **Layer 3 (Back)**: Estimates energy leakage into the hadronic calorimeter.

Hadronic Calorimeter (HCAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Located outside the ECAL, this sampling calorimeter measures jets and missing energy.

*   **Material**: **Iron** (Fe) absorber plates with **Plastic Scintillator** tiles.
*   **Structure**: Divided into 3 longitudinal layers with coarser granularity (Δη × Δφ ≈ 0.1 × 0.1).

Detector Layers & Granularity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - System
     - Layer
     - Name
     - Material
     - Granularity (Δη × Δφ)
   * - **ECAL (Barrel)**
     - 0
     - Pre-Sampler
     - LAr / Pb
     - 0.025 × 0.1
   * -
     - 1
     - Front (Strips)
     - LAr / Pb
     - 0.003125 × 0.1
   * -
     - 2
     - Middle
     - LAr / Pb
     - 0.025 × 0.025
   * -
     - 3
     - Back
     - LAr / Pb
     - 0.050 × 0.025
   * - **TileCal (Barrel)**
     - 1
     - Front
     - Scint. / Fe
     - 0.1 × 0.1
   * -
     - 2
     - Middle
     - Scint. / Fe
     - 0.1 × 0.1
   * -
     - 3
     - Back
     - Scint. / Fe
     - 0.2 × 0.1
   * - **EMEC (EndCap)**
     - 0
     - Pre-Sampler
     - LAr / Pb
     - 0.025 × 0.1
   * -
     - 1
     - Front
     - LAr / Pb
     - varies (0.003-0.006) × 0.1
   * -
     - 2
     - Middle
     - LAr / Pb
     - 0.025 × 0.025 / 0.1 × 0.1
   * -
     - 3
     - Back
     - LAr / Pb
     - 0.050 × 0.025 / 0.1 × 0.1
   * - **HEC (EndCap)**
     - 1-3
     - All Layers
     - LAr / Cu
     - 0.1 × 0.1 / 0.2 × 0.2

The geometry is highly customizable via Python scripts, allowing users to modify layer depths, material composition, and segmentation without recompiling the C++ core.

Contribution
------------

We welcome everyone to contribute! 🌍 Whether it's fixing bugs, adding new generators, or improving documentation.

1.  Fork the repository.
2.  Create your feature branch (``git checkout -b feature/AmazingFeature``).
3.  Commit your changes.
4.  Open a Pull Request.

Please ensure your code passes existing tests.

License
-------

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
See the LICENSE file for details.
