# eit_app: Electrical Impedance Tomography (EIT) application

Thank you for the interest in `eit_app`!

`eit_app` is **a python-based, open-source framework for Electrical Impedance Tomography (EIT) reconstruction.**
Available https://github.com/DavidMetzIMT/eit_app

## 1. Introduction

### 1.1 Dependencies

| Packages        | Optional   | Note                                     | Links |
| --------------  | ---------- | ---------------------------------------- |-------|
| **numpy**       |            | tested with `numpy-1.21.2`               | |
| **dataclasses** |            | tested with `dataclasses-0.8`            | |
| **matplotlib**  |            | tested with `matplotlib-3.3.2`           | |
| **PyQt5**       |            | tested with `PyQt5-5.15.6`               | |
| **pyserial**    |            | tested with `pyserial-3.5`               | |
| **eit_model**   |            | tested with `eit_model` >> `pyEIT`, `eit_ai`            | [eit_model](https://github.com/DavidMetzIMT/eit_model), [pyEIT](https://github.com/liubenyuan/pyEIT), [eit_ai](https://github.com/DavidMetzIMT/eit_ai)|
| **eit_ai**      |            | tested with `eit_ai`  >> `keras`, `pytorch` |[eit_ai](https://github.com/DavidMetzIMT/eit_ai) |
| **glob_utils**  |            | tested with `glob_utils`               | [glob_utils](https://github.com/DavidMetzIMT/glob_utils)|


### 1.2 Features
 - [x] Serial communication with `a Sciospec EIT32-device from the compagny Sciospec`
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

`eit_app` is purely python based, it can be installed and run without any difficulty.

## 3. Use the app

### 3.1 Run the app

```python
cd path/to/eit_app
python eit_app/main.py
```

When open the app at first time, some global directories will be asked.

The GUI has three columns. The left is measurement configurations. The middle column shows the image reconstruction and the voltage plots. The right column shows the camera figure and export configuration.

### 3.2 Choose EIT model

The first step is to choose the EIT model, by loading a mat-file. In this file the design of the cahmber with the electrode and the injection and measurmenet patterning is defined. Such file are “infos2py.mat”-file created by [`App_EIDORS_ModelSim`](https://github.com/DavidMetzIMT/App_EIDORS_ModelSim)). 

<img src="./doc/images/app_eit_model.PNG" alt="" width="500"/><br>
*Selection of EIT-Model*

Notes:
- TODO have save the Eit_model as json?? for less matalb depedencies

### 3.3 Connect the device

“Get setup” can get the default configuration or configuration used for previous measurement. 

“chip type” is used to map the  actual electrode arrangement to simulated electrode arrangement.

In “Excitation Pattern”, **Model** shows the injection pattern loaded from **EIT model**, **Chip** shows the actual injection pattern.

When any parameter is changed, “Set setup” should be clicked.

<img src="./doc/images/app_device_com.PNG" alt="" width="500"/><br>
*Selection of EIT-Model*
![Untitled](eit_app%20readme%20bfdf62226b5847879cca84c6f95ec008/Untitled%201.png)

Notes:
- **Attenton**: by loading measurements the chip has to be reselected...! (TODO save it with measurmenents)

### 3.4 Data acquisition and replay

<img src="./doc/images/app_aquisition.PNG" alt="" width="500"/><br>
*Aquisition of measurements*

During the data acquisition, all the information can be found. "Frame infos" shows the current frame information like Frequency, Amplitude, excitation etc. If the camera is connected and starts capture, the snapshot of each frame will be saved.

When replay the measurement, if the camera state is still measuring, the image will be overwritten.  
The reconstruction image and Voltage plots will be computed every frame. In “Imaging type ” can choose the imaging type and different measurement frequency. Different voltage plot (real, imaginary, magnitude, phase) can be selected as well.

<img src="./doc/images/app_imaging.PNG" alt="" width="500"/><br>
*Seletion of imaging configurations*

“Activate calibration” allows to calibrate the  voltages.

### 3.5 Reconstruction

Both 2D and 3D image reconstruction can be made. 

Both pyEIT and Ai solver can be selected for EIT reconstruction. Any solver should select corresponded EIT model. pyEIT reconstruction can run during the data acquisition. 

For showing the 3D image, “mode generation 2D” should be unclicked. Click “Open pyvista viewer” in **Plot settings** first, then adjust the parameters of pyEIT.

 ****

<img src="./doc/images/app_rec_3D.PNG" alt="" width="500"/><br>
*Aditional 3D visualisation*

With Ai reconstruction, the model path will be asked. Before loading the model, the EIT model should be selected correctly. "infos2py.mat" file in the training dataset should be used. 

### 3.6 Export frame data

With different combination of selection, different data or images can be exported. For example, Selecting “Frame” and “EIT image” can export all the reconstruction image of each frame automatically.

“Analysis protocol” will export all the necessary information of dataset including measurement information, EIT model, parameters of reconstruction solver. 

<img src="./doc/images/app_export.PNG" alt="" width="500"/><br>
*Selection of export configurations*


## 4. Contribute to `eit_app`.



## 5. Cite our work.


**If you find `eit_app` useful, please cite our work!**


