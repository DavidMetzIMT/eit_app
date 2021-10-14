# eit_app: Electrical Impedance Tomography (EIT) application
# ![eit_app](docs/icons/EIT.png)

Thank you for the interest in `eit_app`!

`eit_app` is **a python-based, open-source framework for Electrical Impedance Tomography (EIT) reconstruction.**

using a Sciospec EIT32-device from the compagny Sciospec

## 1. Introduction

### 1.1 Dependencies

reconstruction is based on `pyEIT` 

NOT DONE YET!!!

| Packages       | Optional   | Note                                     |
| -------------- | ---------- | ---------------------------------------- |
| **numpy**      |            | tested with `numpy-1.19.1`               |
| **scipy**      |            | tested with `scipy-1.5.0`                |
| **matplotlib** |            | tested with `matplotlib-3.3.2`           |
| **pandas**     | *Optional* | tested with `pandas-1.1.3`               |
| **vispy**      | *Optional* | failed with `vispy` in python 3.8        |
| **xarray**     | *Optional* | for large data analysis                  |
| **distmesh**   | *Optional* | A build-in module is provided in `pyEIT` |

### 1.2 Features
 - [x] Serial communication with `Sciospec EIT32-device`
 - [x] Setting/reading measurements setups of the `Sciospec EIT32-device`
 - [x] Impedance Measurements aquisition (continious mode) with `Sciospec EIT32-device`
 - [x] Saving of measurements
 - [x] Replay of saved measurements
 - [x] Liveview plots of measurements values
 - [x] Liveview plots of 2D reconstruction using `pyEIT` reconstruction algorithms:Gauss-Newton solver (JAC), Back-projection (BP), 2D GREIT
 - [x] Liveview plots of 2D reconstruction using Neuronal Network
 - [ ] Liveview plots of 3D reconstruction 
 - [x] Liveview of chamber from usb camera and saving of image for measuremnets 
 - [ ] Complete electrode model (CEM) support (not in `pyEIT` implemented yet)
	
## 2. Installation

`eit_app` is purely python based, it can be installed and run without any difficulty. NOT TESTED YET!!!

### 2.1 Install global

NOT TESTED YET!!!

$ python setup.py build
$ python setup.py install


### 2.2 Install 

## 3. Run the app



**Note:** the following images may be outdated due to that the parameters of a EIT algorithm may be changed in different versions of `pyEIT`. And it is there in the code, so just run the demo.

### 3.1 examples of apps


### 3.2 (3D) forward and inverse computing


## 4. Contribute to `eit_app`.



## 5. Cite our work.


**If you find `eit_app` useful, please cite our work!**


