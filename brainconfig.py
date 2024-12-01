import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLineEdit, QLabel, QWidget, QComboBox, \
    QHBoxLayout, QFileDialog, QMessageBox, QSlider, QListWidget, QTableWidget, QHeaderView, QSizePolicy, \
    QTableWidgetItem, QColorDialog, QFrame, QFileDialog, QRadioButton, QCheckBox, QDialog
from PyQt5.QtCore import Qt
from pyface.qt import QtGui, QtCore
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi import mlab
import os
from collections import defaultdict
from copy import deepcopy
from PyQt5.QtGui import QPalette
from pynetstim.coordinates import FreesurferCoords
import pandas as pd
from utils import get_elec_name, parse_elec_file
from aesthetics import *
from read_files import *

################################################################################
# The QWidget containing the visualization and UI controls
class BrainConfigWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotconfig = None

        layout = QVBoxLayout(self)

        # Input fields for the subject, surface, hemisphere, and cortex options

        upper_layout = QHBoxLayout()
        # Subject
        self.subject_id = QLineEdit(self)
        upper_layout.addWidget(QLabel("Subject ID:"))
        upper_layout.addWidget(self.subject_id)

        # Freesurfer Dir
        upper_layout.addWidget(QLabel("Project Dir:"))
        self.projectdir_line = QLineEdit(self)
        upper_layout.addWidget(self.projectdir_line)
        projectdir_choose_pushbtn = QPushButton("Choose", self)
        projectdir_choose_pushbtn.clicked.connect(self.projectdir_choose_pushbtn_slot)
        upper_layout.addWidget(projectdir_choose_pushbtn)

        brain_layout = QHBoxLayout()
        # Surface
        self.surf_combo = QComboBox(self)
        self.surf_combo.addItems(["pial", "white", "inflated", "smoothwm"])
        brain_layout.addWidget(QLabel("Surface:"))
        brain_layout.addWidget(self.surf_combo)

        # Hemisphere
        self.hemi_combo = QComboBox(self)
        self.hemi_combo.addItems(["lh", "rh", "both"])
        brain_layout.addWidget(QLabel("Hemisphere:"))
        brain_layout.addWidget(self.hemi_combo)

        # Alpha (transparency) with a slider
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(100)
        brain_layout.addWidget(QLabel(f"Brain Opacity:"))
        brain_layout.addWidget(self.alpha_slider)

        brain2_layout = QHBoxLayout()
        # Cortex
        self.cortex_combo = QComboBox(self)
        self.cortex_combo.addItems(["Classic", "High Contrast", "Low Contrast", "Bone"])
        brain2_layout.addWidget(QLabel("Cortex:"))
        brain2_layout.addWidget(self.cortex_combo)

        # Background
        self.background_combo = QComboBox(self)
        self.background_combo.addItems(["white", "black"])
        brain2_layout.addWidget(QLabel("Background:"))
        brain2_layout.addWidget(self.background_combo)

        brain2_layout.setStretch(0, 0)
        brain2_layout.setStretch(1, 1)
        brain2_layout.setStretch(2, 0)
        brain2_layout.setStretch(3, 1)

        # Aesthetics
        aes_layout = QVBoxLayout()
        self.tablewidget = BrainAestheticWidget(self)
        aes_layout.addWidget(QLabel("Aesthetics:"))
        aes_layout.addWidget(self.tablewidget)

        # layout
        layout.addLayout(upper_layout)
        layout.addLayout(brain_layout)
        layout.addLayout(brain2_layout)
        layout.addLayout(aes_layout)
        # layout.addLayout(body_layout)

    def projectdir_choose_pushbtn_slot(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_():
            projectdir = dialog.selectedFiles()[0]
            self.projectdir_line.setText(projectdir)

    def get_config(self):
        self.plotconfig = {
            "subject_id": self.subject_id.text(),
            "project_dir": self.projectdir_line.text(),
            "surf": self.surf_combo.currentText(),
            "hemi": self.hemi_combo.currentText(),
            "cortex": self.cortex_combo.currentText(),
            "background": self.background_combo.currentText(),
            "alpha": self.alpha_slider.value(),
            "aesthetics": self.tablewidget.read_table_data(),
        }

        return self.plotconfig


class BrainConfigMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(400, 50, 600, 800)

        layout = QVBoxLayout()
        # Set the main layout
        self.brainconfig_widget = BrainConfigWidget(self)
        layout.addWidget(self.brainconfig_widget)
        # self.setCentralWidget(self.brainconfig_widget)
        self.setWindowTitle("Brain Config")

        accept_cancel_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.cancel_btn_slot)
        accept_cancel_layout.addWidget(self.cancel_btn)

        self.accept_btn = QPushButton("Accept", self)
        self.accept_btn.clicked.connect(self.accept_btn_slot)
        accept_cancel_layout.addWidget(self.accept_btn)

        layout.addLayout(accept_cancel_layout)

        # Set a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def accept_btn_slot(self):
        self.plotconfig = self.brainconfig_widget.get_config()
        self.close()

    def cancel_btn_slot(self):
        self.close()


class BrainAestheticWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.brainconfigwidget = parent

        self.subject_id = parent.subject_id.text()
        self.projectdir = parent.projectdir_line.text()

        # Initialize layout and table
        self.layout = QVBoxLayout()

        # Create a table with 2 columns: text input and color picker button
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["object", "name", "hemi", "color", "opacity", "aesthetic", "border", "properties"])

        # Stretch columns to take up full width of the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Ensure table expands and fills the available space
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        add_buttons_layout = QHBoxLayout()
        # Add button to add new label
        self.add_label_btn = QPushButton('Add Label')
        self.add_label_btn.clicked.connect(self.add_new_label)
        add_buttons_layout.addWidget(self.add_label_btn)

        # Add button to add new annot
        self.add_annot_btn = QPushButton('Add Annot')
        self.add_annot_btn.clicked.connect(self.add_new_annot)
        add_buttons_layout.addWidget(self.add_annot_btn)

        # Add button to add new surf
        self.add_surf_btn = QPushButton('Add Surf')
        self.add_surf_btn.clicked.connect(self.add_new_surf)
        add_buttons_layout.addWidget(self.add_surf_btn)

        # Add button to add new morph
        self.add_overlay_btn = QPushButton('Add Overlay')
        self.add_overlay_btn.clicked.connect(self.add_new_overlay)
        add_buttons_layout.addWidget(self.add_overlay_btn)

        # Add button to add new foci
        self.add_foci_btn = QPushButton('Add Foci')
        self.add_foci_btn.clicked.connect(self.add_new_foci)
        add_buttons_layout.addWidget(self.add_foci_btn)

        # Add button to add new Elec
        self.add_elec_btn = QPushButton('Add Elec')
        self.add_elec_btn.clicked.connect(self.add_new_elec)
        add_buttons_layout.addWidget(self.add_elec_btn)

        # Add button to remove a selected row
        self.remove_row_btn = QPushButton('Remove Selected Row')
        self.remove_row_btn.clicked.connect(self.remove_selected_row)

        # Add the table and buttons to the layout
        self.layout.addWidget(self.table)
        self.layout.addLayout(add_buttons_layout)
        self.layout.addWidget(self.remove_row_btn)

        # Set the layout
        self.setLayout(self.layout)

        # Ensure the widget resizes properly with its parent
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def add_new_label(self):
        row_count = self.table.rowCount()
        # label
        options = QFileDialog.Options()
        label_paths, _ = QFileDialog.getOpenFileNames(self, "Select a File", self.projectdir,
                                                      "All Files (*);;Text Files (*.txt)", options=options)
        for label_path in label_paths:
            if label_path:
                self.table.insertRow(row_count)

                # name
                label_name = os.path.basename(label_path)
                labelname_item = QTableWidgetItem(label_name)
                labelname_item.setFlags(labelname_item.flags() & ~Qt.ItemIsEditable)
                hemi = label_name.split('.')[0]
                self.table.setItem(row_count, 1, labelname_item)

                # Hemi
                hemi_item = QTableWidgetItem(hemi)
                hemi_item.setFlags(hemi_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_count, 2, QTableWidgetItem(hemi))

                # Add QPushButton to open color picker
                color = "Pick"
                color_btn = QPushButton('Pick')
                color_btn.clicked.connect(lambda: self.open_color_dialog())
                self.table.setCellWidget(row_count, 3, color_btn)

                # Opacity
                opacity = "1"
                self.table.setItem(row_count, 4, QTableWidgetItem(opacity))

                # Aesthetics
                aes_item = QTableWidgetItem("")
                aes_item.setFlags(aes_item.flags() & ~Qt.ItemIsEditable)
                aes_item.setTextAlignment(Qt.AlignCenter)
                aes_item.setBackground(self.palette().color(QPalette.Window))
                self.table.setItem(row_count, 5, aes_item)

                # Show only Border
                border = False
                showedge_checkbox = QCheckBox(self)
                self.table.setCellWidget(row_count, 6, showedge_checkbox)

                # Object
                labelobj = LabelObj(label_path, label_name, hemi, color, opacity, border)
                object_item = QTableWidgetItem("Label")
                object_item.setData(Qt.UserRole, labelobj)
                self.table.setItem(row_count, 0, object_item)

                # Properties
                properties_btn = QPushButton("View")
                properties_btn.clicked.connect(
                    lambda _, row_count=row_count: self.show_object_properties(row_count))  # Pass row to slot
                self.table.setCellWidget(row_count, 7, properties_btn)

                # Increase row count by 1
                row_count += 1

    def add_new_annot(self):
        row_count = self.table.rowCount()
        # annot
        options = QFileDialog.Options()
        annot_paths, _ = QFileDialog.getOpenFileNames(self, "Select a File", self.projectdir,
                                                      "All Files (*);;Text Files (*.txt)", options=options)
        for annot_path in annot_paths:
            if annot_path:
                self.table.insertRow(row_count)

                # Add QLineEdit for text input
                annot_name = os.path.basename(annot_path)
                annotname_item = QTableWidgetItem(annot_name)
                annotname_item.setFlags(annotname_item.flags() & ~Qt.ItemIsEditable)
                hemi = annot_name.split('.')[0]
                self.table.setItem(row_count, 1, annotname_item)

                # Hemi
                hemi_item = QTableWidgetItem(hemi)
                hemi_item.setFlags(hemi_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_count, 2, QTableWidgetItem(hemi))

                # Color
                color_item = QTableWidgetItem("")
                color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
                color_item.setTextAlignment(Qt.AlignCenter)
                color_item.setBackground(self.palette().color(QPalette.Window))
                self.table.setItem(row_count, 3, color_item)

                # Opacity
                opacity = "1"
                self.table.setItem(row_count, 4, QTableWidgetItem(opacity))

                # Aesthetics
                aes_item = QTableWidgetItem("")
                aes_item.setFlags(aes_item.flags() & ~Qt.ItemIsEditable)
                aes_item.setTextAlignment(Qt.AlignCenter)
                aes_item.setBackground(self.palette().color(QPalette.Window))
                self.table.setItem(row_count, 5, aes_item)

                # Show only Border
                border = False
                showedge_checkbox = QCheckBox(self)
                self.table.setCellWidget(row_count, 6, showedge_checkbox)

                # Object
                annotobj = AnnotObj(annot_path, annot_name, hemi, opacity, border)
                object_item = QTableWidgetItem("Annot")
                object_item.setData(Qt.UserRole, annotobj)
                self.table.setItem(row_count, 0, object_item)

                # Properties
                properties_btn = QPushButton("View")
                properties_btn.clicked.connect(
                    lambda _, row_count=row_count: self.show_object_properties(row_count))  # Pass row to slot
                self.table.setCellWidget(row_count, 7, properties_btn)
                # Increase row count by 1
                row_count += 1

    def add_new_surf(self):
        row_count = self.table.rowCount()
        # annot
        options = QFileDialog.Options()
        surf_paths, _ = QFileDialog.getOpenFileNames(self, "Select a File", self.projectdir,
                                                     "All Files (*);;Text Files (*.txt)", options=options)
        for surf_path in surf_paths:
            if surf_path:
                self.table.insertRow(row_count)

                # name
                surf_name = os.path.basename(surf_path)
                surfname_item = QTableWidgetItem(surf_name)
                surfname_item.setFlags(surfname_item.flags() & ~Qt.ItemIsEditable)
                hemi = surf_name.split('.')[0]
                self.table.setItem(row_count, 1, surfname_item)

                # Hemi
                hemi_item = QTableWidgetItem(hemi)
                hemi_item.setFlags(hemi_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_count, 2, QTableWidgetItem(hemi))

                # Color
                color = "Pick"
                color_btn = QPushButton('Pick')
                color_btn.clicked.connect(lambda: self.open_color_dialog())
                self.table.setCellWidget(row_count, 3, color_btn)

                # Opacity
                opacity = "1"
                self.table.setItem(row_count, 4, QTableWidgetItem(opacity))

                # Aesthetics
                aes_item = QComboBox(self)
                aes_item.addItems(["surface", "wireframe", "points", "mesh", "fancymesh"])
                self.table.setCellWidget(row_count, 5, aes_item)

                # Show only Border
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
                empty_item.setTextAlignment(Qt.AlignCenter)
                empty_item.setBackground(self.palette().color(QPalette.Window))
                self.table.setItem(row_count, 6, empty_item)

                # Object
                surfobj = SurfObj(surf_path, surf_name, hemi, color, aes_item.currentText(), opacity)
                object_item = QTableWidgetItem("Surf")
                object_item.setData(Qt.UserRole, surfobj)
                self.table.setItem(row_count, 0, object_item)

                # Properties
                properties_btn = QPushButton("View")
                properties_btn.clicked.connect(
                    lambda _, row_count=row_count: self.show_object_properties(row_count))  # Pass row to slot
                self.table.setCellWidget(row_count, 7, properties_btn)

                # Increase row count by 1
                row_count += 1


    def add_new_elec(self):
        if self.check_subject_exists():
            options = QFileDialog.Options()
            elec_file, _ = QFileDialog.getOpenFileName(self, "Select a File", self.projectdir,
                                                       "All Files (*);;Text Files (*.txt)", options=options)



    def add_new_overlay(self):
        pass

    def add_new_foci(self):
        if self.check_subject_exists():
            options = QFileDialog.Options()
            foci_file, _ = QFileDialog.getOpenFileName(self, "Select a File", self.projectdir,
                                                       "All Files (*);;Text Files (*.txt)", options=options)

            try:
                foci_df = read_foci_file(foci_file)
                xyz_coords = foci_df[['x', 'y', 'z']].to_numpy()
            except RequiredColumnsNotAvailable:
                QMessageBox.warning(self, "Check Foci File!",
                                    "Make sure the Foci File has three columns that are named x, y, z")
            except FileNotFoundError:
                QMessageBox.warning(self,"File does not exist!")

            subject_id = self.subject_id
            projectdir = self.projectdir

            fscoords = FreesurferCoords(xyz_coords, 'freesurfer', os.path.join(projectdir,subject_id), guess_hemi=True, working_dir=projectdir)
            if 'name' in foci_df.columns:
                fscoords.add_trait('name', foci_df.name.to_list())
            else:
                fscoords.add_trait('name', [""] * fscoords.npoints)

            if 'color' in foci_df.columns:
                fscoords.add_trait('color', foci_df.color.to_list())
            else:
                fscoords.add_trait('color', [""] * fscoords.npoints)

            if 'opacity' in foci_df.columns:
                fscoords.add_trait('opacity', foci_df.opacity.to_list())
            else:
                fscoords.add_trait('opacity', ["1"] * fscoords.npoints)

            if 'hemi' in foci_df.columns:
                fscoords.hemi = foci_df.hemi.to_list()

            if 'scale' in foci_df.columns:
                fscoords.add_trait('scale', foci_df.scale.to_list())
            else:
                fscoords.add_trait('scale', ["1"] * fscoords.npoints)

            if 'map surface' in foci_df.columns:
                fscoords.add_trait('map_surface', foci_df['map surface'].to_list())
            else:
                fscoords.add_trait('map_surface', [""] * fscoords.npoints)

            row_count = self.table.rowCount()
            for fscoord in fscoords:
                x = str(fscoord.ras_coord[0])
                y = str(fscoord.ras_coord[1])
                z = str(fscoord.ras_coord[2])

                self.table.insertRow(row_count)

                # name
                name_item = QTableWidgetItem(fscoord.name)
                self.table.setItem(row_count, 1, name_item)

                # Hemi
                hemi_item = QTableWidgetItem(fscoord.hemi)
                # hemi_item.setFlags(hemi_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_count, 2, hemi_item)

                # Color
                if hasattr(fscoord, 'color') and fscoord.color != "":
                    color = fscoord.color
                    color_btn = QPushButton(color)
                    color_btn.clicked.connect(lambda: self.open_color_dialog())
                    color_btn.setStyleSheet(f"background-color: {color}")
                    color_btn.setText(color)
                    self.table.setCellWidget(row_count, 3, color_btn)
                else:
                    color = "Pick"
                    color_btn = QPushButton("Pick")
                    color_btn.clicked.connect(lambda: self.open_color_dialog())
                    self.table.setCellWidget(row_count, 3, color_btn)

                # Opacity
                self.table.setItem(row_count, 4, QTableWidgetItem(fscoord.opacity))

                # Object
                fociobj = FociObj(x, y, z, fscoord.name, fscoord.hemi, fscoord.map_surface, fscoord.scale,
                                  fscoord.color, fscoord.opacity)
                object_item = QTableWidgetItem("Foci")
                object_item.setData(Qt.UserRole, fociobj)
                self.table.setItem(row_count, 0, object_item)

                # Properties
                properties_btn = QPushButton("View")
                properties_btn.clicked.connect(
                    lambda _, row_count=row_count: self.show_object_properties(row_count))  # Pass row to slot
                self.table.setCellWidget(row_count, 7, properties_btn)

                # Increase row count by 1
                row_count += 1

        else:
            QMessageBox.warning(self, "Check Subject and Freesurfer Directory!",
                                "Please make sure the Subject and Freesurfer directory exists!")

    def open_color_dialog(self):
        button = self.sender()
        index = self.table.indexAt(button.pos())
        if index.isValid():
            row = index.row()
            color = QColorDialog.getColor()
            if color.isValid():
                button.setStyleSheet(f"background-color: {color.name()}")
                button.setText(color.name())  # Display the selected color code on the button
                button.color = color.name()
                item = self.table.item(row, 0)
                obj = item.data(Qt.UserRole)
                obj.color = color.name()


    def remove_selected_row(self):
        # Get the current selected row
        selected_row = self.table.currentRow()
        row_count = self.table.rowCount()

        # Check if any row is selected
        if selected_row >= 0:
            self.table.removeRow(selected_row)

        else:
            # If no row is selected, show an error message
            QMessageBox.warning(self, "No Selection", "Please select a row to remove.")

    def show_object_properties(self, row):
        # Create and show the dialog with object properties
        item = self.table.item(row, 0)
        custom_obj = item.data(Qt.UserRole)
        # update custom_obj properties
        properties = vars(custom_obj)

        custom_obj.name = self.table.item(row, 1).text()
        if hasattr(custom_obj, 'hemi'):
            custom_obj.hemi = self.table.item(row, 2).text()
        if hasattr(custom_obj, 'color'):
            custom_obj.color = self.table.cellWidget(row, 3).text()
        if hasattr(custom_obj, 'opacity'):
            custom_obj.opacity = self.table.item(row, 4).text()
        if hasattr(custom_obj, 'aesthetic'):
            custom_obj.aesthetic = self.table.cellWidget(row, 5).currentText()
        if hasattr(custom_obj, 'border'):
            custom_obj.border = str(self.table.cellWidget(row, 6).isChecked())

        dialog = ObjectPropertiesDialog(custom_obj)
        if dialog.exec_() == QDialog.Accepted:
            # If changes are accepted, update the table display if needed
            self.update_row(custom_obj, row)

    def update_row(self, obj, row):
        # name
        self.table.item(row, 1).setText(obj.name)

        # hemi
        if hasattr(obj, 'hemi'):
            self.table.item(row, 2).setText(obj.hemi)

        # color
        if hasattr(obj, 'color'):
            color = obj.color
            color_btn = self.table.cellWidget(row, 3)
            color_btn.setStyleSheet(f"background-color: {color}")
            color_btn.setText(color)  # Display the selected color code on the button

        # opacity
        if hasattr(obj, 'opacity'):
            self.table.item(row, 4).setText(obj.opacity)

        # Aesthetics
        if hasattr(obj, 'aesthetic'):
            self.table.cellWidget(row, 5).setCurrentText(obj.aesthetic)

        # Only border
        if hasattr(obj, 'border'):
            if obj.border == 'False':
                border = False
            elif obj.border == 'True':
                only_boder = True
            self.table.cellWidget(row, 6).setChecked(border)

    def update_obj_properties(self, row):
        item = self.table.item(row, 0)
        custom_obj = item.data(Qt.UserRole)

        if hasattr(custom_obj, 'hemi'):
            custom_obj.hemi = self.table.item(row, 2).text()
        if hasattr(custom_obj, 'color'):
            custom_obj.color = self.table.cellWidget(row, 3).text()
        if hasattr(custom_obj, 'opacity'):
            custom_obj.opacity = float(self.table.item(row, 4).text())
        if hasattr(custom_obj, 'aesthetic'):
            custom_obj.aesthetic = self.table.cellWidget(row, 5).currentText()
        if hasattr(custom_obj, 'border'):
            custom_obj.border = self.table.cellWidget(row, 6).isChecked()

        return custom_obj

    def read_table_data(self):
        row_data = {}
        row_data['Label'] = []
        row_data['Annot'] = []
        row_data['Surf'] = []
        row_data['Vol'] = []
        row_data['Foci'] = []

        row_count = self.table.rowCount()

        for row in range(row_count):
            obj = self.update_obj_properties(row)

            if isinstance(obj, LabelObj):
                row_data["Label"].append(obj)
            elif isinstance(obj, AnnotObj):
                row_data["Annot"].append(obj)
            elif isinstance(obj, SurfObj):
                row_data["Surf"].append(obj)
            elif isinstance(obj, FociObj):
                row_data["Foci"].append(obj)

        return row_data

    def update_subject_and_projectdir(self):
        self.subject_id = self.brainconfigwidget.subject_id.text()
        self.projectdir = self.brainconfigwidget.projectdir_line.text()

    def check_subject_exists(self):
        self.update_subject_and_projectdir()
        if self.subject_id != "" and self.projectdir != "":

            if os.path.isdir(self.projectdir) and os.path.isdir(os.path.join(self.projectdir, self.subject_id)):
                return True
            else:
                return False

        else:
            return False
            # check if the subject exists in the projectdir


class ObjectPropertiesDialog(QDialog):
    def __init__(self, custom_obj):
        super().__init__()
        self.setWindowTitle("Properties")
        self.custom_obj = custom_obj

        # get properties
        properties = vars(custom_obj)  # Get all attributes of the object

        # Create a table to show and edit object properties
        self.table = QTableWidget(len(properties), 2)  # 3 properties, 2 columns
        self.table.setHorizontalHeaderLabels(["Property", "Value"])

        # Populate the table with object properties

        for row, (prop_name, prop_value) in enumerate(properties.items()):
            # Property name (read-only)
            self.table.setItem(row, 0, QTableWidgetItem(prop_name))
            self.table.item(row, 0).setFlags(Qt.ItemIsEnabled)  # Make the property name read-only

            # Property value (editable)
            self.table.setItem(row, 1, QTableWidgetItem(str(prop_value)))

        # Create buttons for Accept and Close
        accept_button = QPushButton("Accept")
        close_button = QPushButton("Close")

        # Connect buttons to methods
        accept_button.clicked.connect(self.accept_changes)
        close_button.clicked.connect(self.close)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(close_button)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def accept_changes(self):
        # Update the custom object's properties with edited values
        properties = vars(self.custom_obj)
        for row, prop_name in enumerate(properties.keys()):
            new_value = self.table.item(row, 1).text()

            # Update the property of the custom object
            setattr(self.custom_obj, prop_name, new_value)

        # Close the dialog after accepting changes
        self.accept()


class AddVolWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()


#### helpef functions
def create_surf_from_voi(voi_path, subject, subjects_dir, out_path, **kwargs):
    voi_data = nib.load(voi_path).get_fdata()
    verts, faces, norm, val = measure.marching_cubes(voi_data, **kwargs)


    fscoords = FreesurferCoords(verts, subject, subjects_dir, working_dir='.', coord_type='fsvoxel')
    nib.freesurfer.io.write_geometry(out_path, fscoords.coordinates['ras_coord'], faces)


if __name__ == "__main__":
    # Initialize the PyQt application
    app = QApplication(sys.argv)

    # Create and display the main window
    main_window = BrainConfigMainWindow()
    main_window.show()

    # Start the main event loop
    sys.exit(app.exec_())
