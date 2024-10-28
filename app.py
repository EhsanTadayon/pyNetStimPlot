import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QMenuBar, QLineEdit, QAction, QWidget, QFileDialog, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt


from pyface.qt import QtGui, QtCore
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from surfer import Brain
from brainconfig import BrainConfigWidget
import nibabel as nib
from mayavi import mlab
from PIL import ImageColor

class PlotWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("pynetstim plot")
        self.resize(1300, 600)  # Set the initial size of the window
        
        main_layout = QHBoxLayout()
        
        #brainconfig
        self.brainconfigwidget = BrainConfigWidget()
        
        #plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        self.plot_frame = QFrame(self)
        self.plot_frame.setFrameShape(QFrame.Box)
        plot_layout.addWidget(self.plot_frame)
        
        # Push Buttons and Combo Box at the bottom
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_button_slot)
        
        # View Combobox
        self.viewcombo_box = QComboBox()
        self.viewcombo_box.addItems(["lateral", "medial", "dorsal", "ventral"])
        
        #  Reset View Button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_button_slot)
        
        # Save Plot Button
        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.save_button_slot)

        # Arrange buttons in a horizontal layout
        plotbtn_layout = QHBoxLayout()

        plotbtn_layout.addWidget(self.reset_button)
        plotbtn_layout.addWidget(self.save_button)
        plotbtn_layout.addStretch()  # Adds space between elements
        plotbtn_layout.addWidget(self.viewcombo_box)
        plotbtn_layout.addWidget(self.plot_button)
        plot_layout.addLayout(plotbtn_layout)
        plot_widget.setLayout(plot_layout)
        
        
        main_layout.addWidget(self.brainconfigwidget)
        main_layout.addWidget(plot_widget)
        
        # Set a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        central_widget.setFixedSize(1300,600)
        self.setCentralWidget(central_widget)
        
        
    
class PlotMain(PlotWindowUI):   
    def __init__(self):
        super().__init__() 
        self._addmayaviwidget()
        
    def _addmayaviwidget(self):
        self.mayavi_widget = MayaviQWidget(self.plot_frame)
        
        
    def plot_button_slot(self):
        plotconfig = self.brainconfigwidget.get_config()
        if plotconfig:
            self.mayavi_widget.update_plotconfig(plotconfig)
            self.mayavi_widget.plot_brain()
        
    def save_button_slot(self):
        """Open a file dialog to save the current brain plot as an image."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Brain Image", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.mayavi_widget.visualization.save_brain_image(file_path)
            QMessageBox.information(self, "Saved", f"Brain image saved to: {file_path}")
        
    def reset_button_slot(self):
        self.mayavi_widget.visualization.reset_view()
        
        
    def open_config_brain(self):
        # Create and display the main window
        if self.brainconfigwidget is None:
            self.brainconfigwidget = BrainConfigMainWindow()
        self.brainconfigwidget.show()
        
    def get_config_brain(self):
        if self.brainconfigwidget:
            self.configbrain = self.brainconfigwidget.get_data()
        
            


############################################################################
#
class BrainVisualization(HasTraits):
    scene = Instance(MlabSceneModel, ())

    def __init__(self):
        super().__init__()
        self.brain = None  # Initialize brain as None
        self.doplot = False
    
    # Define the layout of the traits-based UI
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=500, width=600, show_label=False),
                resizable=True  # Resizable to fit the parent widget
                )
        
    @on_trait_change('scene.activated')  
    def plot_brain(self):
        # Plot the PySurfer brain only when this method is called
        if self.brain is None and self.doplot is True:
            self.brain = Brain(subject_id=self.subject_id, hemi=self.hemi,
             surf=self.surf, figure=self.scene.mayavi_scene, background=self.background,
             subjects_dir=self.subjects_dir, alpha=self.alpha)
              
            #### add aesthetics
            # add label
            for label in self.aesthetics['Label']:
                self.brain.add_label(label=label.path,
                                     color=label.color,
                                     alpha=label.opacity,
                                     hemi=label.hemi,
                                     borders=label.border)
                                     
            
            #### add aesthetics
            # add annot
            
            for annot in self.aesthetics['Annot']:
                self.brain.add_annotation(annot=annot.path,
                                        borders=annot.border,
                                        alpha=annot.opacity, 
                                        hemi=annot.hemi,
                                        )
                                        
            for surf in self.aesthetics['Surf']:
                 surf_geom = nib.freesurfer.io.read_geometry(surf.path)
                 vertices, faces = surf_geom[0],surf_geom[1]
                 color = ImageColor.getcolor(surf.color,"RGB")
                 color = (color[0]/255.0,color[1]/255.0,color[2]/255.0)
                 mlab.triangular_mesh(vertices[:,0],vertices[:,1],vertices[:,2],faces,representation=surf.aesthetic,color=color,opacity=surf.opacity)
                 
                
                                        
                                        
            #### add foci
            # add foci
          #  for 
                
                                     
                                     
            
              
              
    def update_brain_config(self,plotconfig):

        self.subject_id = plotconfig['subject_id']
        self.subjects_dir=plotconfig['subjects_dir']
        self.hemi = plotconfig['hemi']
        self.surf = plotconfig['surf']
        self.cortex = plotconfig['cortex']
        self.alpha = float(plotconfig['alpha'])/100
        self.background = plotconfig['background']
        self.aesthetics = plotconfig['aesthetics']
        
                
    def reset_view(self):
        """Reset the brain view to the default orientation."""
        if self.brain is not None:
            self.brain.show_view('lateral')
            
    def save_brain_image(self, filepath):
            """Save the current brain visualization as an image."""
            if self.brain is not None:
                self.brain.save_image(filepath)
                
    
        


################################################################################
# The QWidget containing the Mayavi visualization (integrating PyQt with Mayavi)
class MayaviQWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotconfig = None
        self.parent = parent
        
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # # Create the Visualization instance with user-provided arguments
        self.visualization = BrainVisualization()
        #
        # # Generate the traits-based UI and embed it in the QWidget
        self.ui = self.visualization.edit_traits(parent=self, kind='subpanel').control
        self.layout.addWidget(self.ui)
        self.ui.setParent(self)
        
        self.layout.setStretchFactor(self.ui, 1)
        
    def update_plotconfig(self, plotconfig):
        self.plotconfig = plotconfig
        
    
 
    def plot_brain(self):
        # Plot if plotconfig is not None
        if self.plotconfig is not None:                 
            clear_layout(self.layout)
            # Create the Visualization instance with user-provided arguments
            self.visualization = BrainVisualization()
            self.visualization.doplot = True
            self.visualization.update_brain_config(self.plotconfig)
            # Generate the traits-based UI and embed it in the QWidget
            self.ui = self.visualization.edit_traits(parent=self, kind='subpanel').control
            self.layout.addWidget(self.ui)
            self.ui.setParent(self)
            self.layout.setStretchFactor(self.ui, 1)
            
            self.visualization.plot_brain()
        else:
            error_message = QMessageBox()
            error_message.setText("No subject is added.")
            error_message.setInformativeText("Please add a subject using add brain under Plot menubar!")
            error_message.setWindowTitle("Error")
            error_message.setStandardButtons(QMessageBox.Ok)
            error_message.exec_()
            
            
    def resizeEvent(self, event):
        """Ensure the Mayavi scene resizes when the QWidget is resized."""
        super().resizeEvent(event)
        if self.visualization.scene is not None:
            # Resize the Mayavi scene to match the widget size
            mayavi_scene = self.visualization.scene.mayavi_scene
            new_width = self.width()
            new_height = self.height()
            mayavi_scene.scene.set_size((new_width, new_height))
            mayavi_scene.render()
            
        
            
def clear_layout(layout):
    """
    Removes all widgets from the given layout.
    
    Parameters:
    layout (QLayout): The layout to clear.
    """
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Schedule the widget for deletion
            else:
                clear_layout(item.layout())  # Recursively clear sub-layouts


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotMain()
    window.show()
    sys.exit(app.exec_())
