# Neuronalab Api

### Install requirements
```bash
pip3 install -r requirements.txt
```
### Run API
```bashS
python3 main.py
```
### Use Case
This app was developed for MRI image analysis. UI of the app is displayed on ![MRI API](./Images/1.png?raw=true "MRI APP")

### Usage
#### Menu
1. Load DICOM images 
   * File -> Open DICOM or click on icon 1. Then browse to DICOM folder
2. Export single Brain image
   * File ->  Export Brain or click on icon 3. Then choose the path and filename of an image. Image is saved with the current settings (note that brain image can be exported only after Brain extractor checkbox was used)
3. Export all images
   * File Export all to PNG or click on icon 2. Then choose path to save (note that all images that were generated are saved. If user used N4 correction or Brain extraction, all images will be included)
   * The NIFTI files are automatically stored in the root directory from step 1 (input path)

#### UI
![MRI API](./Images/4.png?raw=true "MRI APP")

Working with the app should be easy. The user has on the screen several option for image manipulation
* Bottom part of the app contains "Slices" slide bar used to iterate through all images in dataset
* The image part displays current image with selected options. When holding CTRL key and using mouse wheel -> Zoom In / Out functionality is triggered
* "Voxel Size" menu displays current voxel settings of displayed image. If this setting needs to be changed, user is required to type desired values into "X","Y" and "Z" input boxes and then to click on "Resample" button -> new image with selected voxel sizes is displayed
* "Slice Size" menu displays size of displayed image, to change size, type into "Width" / "Height" input box desired size and click on "Resize" button
* "N4 Correction" checkbox computes and displays N4 correction when checked
* "Brain extractor" checkbox computes and displays brain extracted from images when checked