Notebooks
=========

We provide several Jupyter Notebooks to help you get started with Lorenzetti. These tutorials cover everything from basic usage to advanced simulation scenarios.

.. toctree::
   :maxdepth: 1

   usage
   generation
   simulation
   anomaly


Tutorial Specifications
-----------------------

Usage Guide
~~~~~~~~~~~
**File:** ``usage.ipynb``

This notebook provides a general introduction to using the Lorenzetti framework. It covers loading the libraries, setting up the environment, and the basic data structures used throughout the simulation and reconstruction chains.

Particle Generation
~~~~~~~~~~~~~~~~~~~
**File:** ``generation.ipynb``

Learn how to generate physics events using the built-in generators. This tutorial demonstrates how to configure and run the generation algorithms to create events such as $Z \to e^+e^-$ decays and Jet production, which serve as inputs for the simulation steps.

Simulation
~~~~~~~~~~
**File:** ``simulation.ipynb``

This tutorial simulates the detector response to the generated particles. It guides you through the process of calculating energy deposits (hits) in the calorimeter cells, handling the complex geometry and material interactions defined in the framework.

Anomaly Injection
~~~~~~~~~~~~~~~~~
**File:** ``anomaly.ipynb``

A specialized tutorial for machine learning applications. It explains how to inject controlled anomalies into the simulation process. This is particularly useful for generating training datasets for anomaly detection algorithms, allowing you to model and study non-standard detector behaviors or physics signatures.
