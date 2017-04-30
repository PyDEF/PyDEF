# Python for Defect Energy Formation (PyDEF) 1.1.0

Python for Defect Energy Formation (PyDEF) is a scientific software dedicated to defect formation energy calculation using the DFT software Vienna Ab Initio Simulation Package (VASP).
In its first iteration, PyDEF is able to compute the formation energy of any defect using the output files of DFT calculations. It presents an intuitive user interface which guide the user through the different steps required to compute the formation energy and the position of the transition levels.

## New features with version 1.1.0
- Faster plotting of the DOS;
- Now able to plot spin calculations DOS (important note: PyDEF is not yet able to perform defect formation energy using spin projected calculations);
- New options for the plot of the DOS;
- Now able to consider f orbitals;
- Now able to plot band diagram;
- Various bugs corrections.

## Motivations
This software is an original idea from Dr. Camille Latouche, Dr. Stéphane Jobic and myself (Emmanuel Péan). It is an answer to the complexity of the calculation of defect formation energy once corrected with the many corrections available (potential alignment, Moss-Burstein band-filling effect, Makov-Payne correction and the gap corrections). Thanks to its intuitive user interface, anyone will be able to use without knowing anything about Python.

Please note that I am not a professional coder and that I have been using/learning seriously Python for less than two years, hence the code I wrote may deviate from some conventions or may not be well optimised. A second version of PyDEF will include new functionalities such as defects and charge carriers concentrations calculations, multiple defects analysis and chemical potentials calculations.

## Installation

Compiled versions of PyDEF for Windows (tested on Windows 7), Linux (tested on Linux 16.04 LTS) and Mac OS (tested on Mac OS 10.11.6) are available.
Source code is also available and can be run with Python 2.7 and the following modules: 
- matplotlib 1.5.3. or ulterior;
- numpy 1.11.2 or ulterior.

## Example of results

Examples of results can be viewed on this paper http://www.sciencedirect.com/science/article/pii/S0009261417300015 and in the user guide included with the software.

## Others

Questions, remarks, contributions and advices should be addressed to pydef.dev@gmail.com
