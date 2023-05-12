import glob
import os
import shutil
import sys

import SimpleITK as sitk
import dicom2nifti
import matplotlib.pyplot as plt
import nibabel as nib
import nibabel.processing
import qimage2ndarray
import skimage.transform as skTrans
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene
from PyQt5.uic import loadUi

from extractor import Extractor


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # load UI
        loadUi("UI/api.ui", self)

        # connect Frontend with backend
        self.connectSignalsSlots()

        # init scene
        self.scene = QGraphicsScene(self)

        # init nifti data
        self.nifti_data = None

        # init slider value
        self.slider_value = 0

        # init buttons
        self.resize_btn.setEnabled(False)
        self.resample_btn.setEnabled(False)

        # init chechboxes
        self.n4.setChecked(False)
        self.brain_extractor.setChecked(False)

        # init output brain data for brain extractor
        self.brain_data = None

    def connectSignalsSlots(self):
        # init pipes

        # File -> Open DICOM
        self.actionOpen_DICOM.triggered.connect(self.openDicomCall)

        # File -> Export Brain
        self.actionExport_Brain.triggered.connect(self.exportBrainCall)

        # File -> Export all to PNG
        self.actionExport_to_PNG.triggered.connect(self.exportPNGCall)

        # File -> Exit
        self.actionExit.triggered.connect(self.exitCall)

        # Resample button clicked
        self.resample_btn.clicked.connect(self.resample_slice)

        # Resize button clicked
        self.resize_btn.clicked.connect(self.resize_slice)

        # Slider movement
        self.slices.valueChanged[int].connect(self.slide_slides)

        # Checkboxes
        self.n4.toggled.connect(self.N4_correction)
        self.brain_extractor.toggled.connect(self.brain_extraction)

    def openDicomCall(self):
        # get input folder path
        folderpath = QFileDialog.getExistingDirectory(self, 'Select Folder')
        head, tail = os.path.split(folderpath)

        # create nifti folder
        path_to_save_nifti = head + "/NIFTI/" + tail + "/"

        # reset nifti folder
        if not os.path.exists(path_to_save_nifti):
            os.makedirs(path_to_save_nifti)
        else:
            shutil.rmtree(path_to_save_nifti)
            os.makedirs(path_to_save_nifti)

        # convert to nifti
        dicom2nifti.convert_directory(folderpath, path_to_save_nifti)

        # load nifti
        for name_nifti in glob.glob(path_to_save_nifti + "*"):
            self.nifti = nib.load(name_nifti)

        # get data
        self.nifti_data = self.nifti.get_fdata()

        # init slider
        self.slices.setMinimum(0)
        self.slices.setMaximum(self.nifti_data.shape[2] - 1)  # maximum -> number of slices
        self.slices.setTickInterval(1)
        self.slices.setSingleStep(1)

        # get voxel sizes
        sx, sy, sz = self.nifti.header.get_zooms()

        # init voxel api inputs
        self.v_x.setText(str(sx))
        self.v_y.setText(str(sy))
        self.v_z.setText(str(sz))

        # init slice size api inputs
        self.s_width.setText(str(self.nifti_data.shape[1]))
        self.s_heigth.setText(str(self.nifti_data.shape[0]))

        # init displayed slice
        self.displayed_slice = self.nifti_data[:, :, self.slider_value]

        # display slice on frontend
        self.display_slice()

        # set buttons
        self.resize_btn.setEnabled(True)
        self.resample_btn.setEnabled(True)

    def exportBrainCall(self):
        name = QFileDialog.getSaveFileName(self, 'Save Brain file', ".png")

        if self.brain_data is not None:
            plt.imsave(name[0], self.brain_data[:, :, self.slider_value])
        else:
            print("Unable to save brain slice, extraction was not computed yet!")

    def exportPNGCall(self):
        # get input folder path
        folderpath = QFileDialog.getExistingDirectory(self, 'Select Folder for export')

        # create folders
        path_to_save_nifti_images = folderpath + "/NIFTI/"
        path_to_save_brain_images = folderpath + "/Brain/"
        path_to_save_brain_n4_images = folderpath + "/Brain_N4/"
        path_to_save_nifti_n4_images = folderpath + "/NIFTI_N4/"

        folder_list = [path_to_save_nifti_images, path_to_save_brain_images, path_to_save_brain_n4_images,
                       path_to_save_nifti_n4_images]

        for path in folder_list:
            # reset folders
            if not os.path.exists(path):
                os.makedirs(path)
            else:
                shutil.rmtree(path)
                os.makedirs(path)


        if self.nifti_data is not None:
            # save nifti data
            for i in range(len(self.nifti_data)):
                plt.imsave(path_to_save_nifti_images + str(i) + ".png", self.nifti_data[:, :, i])
                plt.imsave(path_to_save_nifti_n4_images + str(i) + ".png", self.N4_correction_func(self.nifti_data[:, :, i]))

        if self.brain_data is not None:
            # save Brain data
            for i in range(len(self.brain_data)):
                plt.imsave(path_to_save_brain_images + str(i) + ".png", self.brain_data[:, :, i])
                plt.imsave(path_to_save_brain_n4_images + str(i) + ".png", self.N4_correction_func(self.brain_data[:, :, i]))



    def exitCall(self):
        sys.exit("Exiting API")

    def N4_correction(self):
        # Function that computes N4 correction if checkbox is checked
        if self.n4.isChecked():
            # if checkbox is checked
            _ = self.N4_correction_func(self.displayed_slice)
        else:
            # reset slice
            if self.brain_extractor.isChecked():
                self.displayed_slice = self.brain_data[:, :, self.slider_value]
            else:
                self.displayed_slice = self.nifti_data[:, :, self.slider_value]

        # display
        self.display_slice()

    def N4_correction_func(self, image):
        # Sub-Function that computes N4 correction
        # convert to sitk image
        image_for_correction = sitk.GetImageFromArray(image)

        # compute mask
        maskImage = sitk.OtsuThreshold(image_for_correction, 0, 1, 200)

        # corrector init
        corrector = sitk.N4BiasFieldCorrectionImageFilter()

        # compute corrected image
        corrected_image = corrector.Execute(image_for_correction, maskImage)

        # compute log bias field
        log_bias_field = corrector.GetLogBiasFieldAsImage(image_for_correction)

        # compute corrected image with the same resolution as input image
        corrected_image_full_resolution = image_for_correction / sitk.Cast(sitk.Exp(log_bias_field), sitk.sitkFloat64)

        # update slice to display
        self.displayed_slice = sitk.GetArrayFromImage(corrected_image_full_resolution)
        return sitk.GetArrayFromImage(corrected_image_full_resolution)

    def brain_extraction(self):
        # Function that does brain extraction
        # If checkbox is checked and brain extraction is not computed yet
        if self.brain_extractor.isChecked() and self.brain_data is None:
            # init extractor
            ext = Extractor()

            #  compute probability matrix
            prob = ext.run(self.nifti_data)

            # select data with probability > 50$
            mask = prob > 0.5

            # mask input data with selected data based on probability
            self.brain_data = self.nifti_data * mask

            # reset slice
            self.displayed_slice = self.brain_data[:, :, self.slider_value]

        if not self.brain_extractor.isChecked():
            # reset to non extracted data
            self.displayed_slice = self.nifti_data[:, :, self.slider_value]

        if self.brain_extractor.isChecked() and self.brain_data is not None:
            self.displayed_slice = self.brain_data[:, :, self.slider_value]

        # display
        self.display_slice()

    def resample_slice(self):
        # Function that resamples input data based on voxel size API inputs
        self.nifti = nibabel.processing.resample_to_output(self.nifti, [float(self.v_x.text()), float(self.v_y.text()),
                                                                        float(self.v_z.text())])

        # reset slider
        self.nifti_data = self.nifti.get_fdata()
        self.slices.setMaximum(self.nifti_data.shape[2] - 1)
        self.slider_value = 0
        self.slices.setValue(self.slider_value)

        # reset slice
        self.displayed_slice = self.nifti_data[:, :, self.slider_value]

        # display
        self.display_slice()

        if self.brain_data is not None:
            self.brain_data = None

        if self.brain_extractor.isChecked():
            self.brain_extractor.setChecked(False)

    def resize_slice(self):
        # Function that resizes input data based on size API inputs
        if self.brain_extractor.isChecked() and self.brain_data is not None:
            self.brain_data = skTrans.resize(self.brain_data,
                                             (
                                                 int(self.s_heigth.text()), int(self.s_width.text()),
                                                 self.nifti_data.shape[2]),
                                             order=1, preserve_range=True)
            # reset slice
            self.displayed_slice = self.brain_data[:, :, self.slider_value]
        else:
            self.nifti_data = skTrans.resize(self.nifti_data,
                                             (
                                                 int(self.s_heigth.text()), int(self.s_width.text()),
                                                 self.nifti_data.shape[2]),
                                             order=1, preserve_range=True)
            # reset slice
            self.displayed_slice = self.nifti_data[:, :, self.slider_value]

        # display
        self.display_slice()

    def display_slice(self):
        # Function that displays image in API
        self.scene.clear()
        self.scene.addPixmap(QPixmap.fromImage(qimage2ndarray.array2qimage(self.displayed_slice)))
        self.graphicsView.setScene(self.scene)

    def slide_slides(self, value):
        # Function that gets slider value from its position and selects slice based on this value
        self.slider_value = value

        # get a slice based on slider value
        self.displayed_slice = self.nifti_data[:, :, value]

        # if the brain extractor checkbox is checked
        if self.brain_extractor.isChecked() and self.brain_data is not None:
            # load extracted data
            self.displayed_slice = self.brain_data[:, :, self.slider_value]

        # if n4 checkbox is checked
        if self.n4.isChecked():
            # compute N4 correction
            _ = self.N4_correction_func(self.displayed_slice)

        # display
        self.display_slice()

    def wheelEvent(self, event):
        # Wheel event modifier
        # When ctrl + wheel up / wheel down -> displayed image zoom up / zoom down

        # if ctrl is pressed
        if event.modifiers() and QtCore.Qt.ControlModifier:
            # get a wheel direction
            x = event.angleDelta().y() / 120
            if x > 0:
                # zoom In
                self.graphicsView.scale(1.2, 1.2)
            elif x < 0:
                # zoom Out
                self.graphicsView.scale(.8, .8)
        else:
            # No modification of this function
            super().wheelEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
