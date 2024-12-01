from surfer import Brain
from mayavi import mlab
import numpy as np

class DepthElectrode(object):
    def __init__(self, num_contacts, contact_diameter, contact_length,
                 intercontact_spacing, electrode_diameter, total_length,
                 electrode_color, contact_color, model_name):

        self.num_contacts = num_contacts
        self.contact_diameter = contact_diameter
        self.contact_length = contact_length
        self.intercontact_spacing = intercontact_spacing
        self.electrode_diameter = electrode_diameter
        self.total_length = total_length
        self.electrode_color = electrode_color
        self.contact_color = contact_color
        self.model_name = model_name


def add_depth_using_first_contact_and_orientation(brain, num_contacts=4, contact_diameter=1.29, contact_length=1.5,
                                                  intercontact_spacing=10, electrode_diameter=1.27, total_length=100,
                                                  position=(0, 0, -20), orientation=(0, 0, 1),
                                                  electrode_color=(0.3, 0.3, 0.3),
                                                  contact_color=(1, 0, 0), add_label=False):
    """
    Adds a DBS electrode to the PySurfer Brain object at a specified position and orientation with cylindrical contacts.
    
    Parameters:
    - brain: PySurfer Brain object
    - num_contacts: Number of electrode contacts
    - contact_diameter: Diameter of each contact
    - contact_length: Length of each contact
    - intercontact_spacing: Distance between contacts
    - electrode_diameter: Diameter of the electrode shaft
    - total_length: Total length of the electrode shaft
    - position: (x, y, z) base coordinates of the first contact on the electrode
    - orientation: (dx, dy, dz) vector that defines the orientation of the electrode
    """
    # Normalize the orientation vector to get the direction
    orientation = np.array(orientation) / np.linalg.norm(orientation)
    x0, y0, z0 = position  # Base position of the first contact

    # Calculate shaft positions along the orientation vector based on total length
    shaft_positions = np.linspace(0, total_length, 100)[:, np.newaxis] * orientation + np.array([x0, y0, z0])

    # Plot the electrode shaft in the same Mayavi figure as the brain
    mlab.plot3d(shaft_positions[:, 0], shaft_positions[:, 1], shaft_positions[:, 2],
                tube_radius=electrode_diameter / 2, color=electrode_color, figure=brain._figures[0][0])

    # Plot each contact as a cylinder positioned with the specified intercontact spacing along the orientation vector
    for i in range(num_contacts):
        contact_base = np.array([x0, y0, z0]) + i * intercontact_spacing * orientation
        contact_tip = contact_base + contact_length * orientation  # End position of the contact cylinder

        # Plot the cylindrical contact
        mlab.plot3d([contact_base[0], contact_tip[0]],
                    [contact_base[1], contact_tip[1]],
                    [contact_base[2], contact_tip[2]],
                    tube_radius=contact_diameter / 2, color=contact_color, figure=brain._figures[0][0])

    # Optionally add labels for each contact
    if add_label:
        for i in range(num_contacts):
            contact_position = np.array([x0, y0, z0]) + i * intercontact_spacing * orientation
            mlab.text3d(contact_position[0] + 0.5, contact_position[1] + 0.5, contact_position[2],
                        f"C{i + 1}", scale=0.3, color=(0, 0, 0), figure=brain._figures[0][0])


def calculate_orientation(contact1, contact2):
    """
    Calculate the orientation vector between two contact points.

    Parameters:
    - contact1: (x1, y1, z1) coordinates of the first contact.
    - contact2: (x2, y2, z2) coordinates of the second contact.

    Returns:
    - orientation: A unit vector (dx, dy, dz) representing the direction from contact1 to contact2.
    """
    # Calculate the vector between the two contacts
    vector = np.array(contact2) - np.array(contact1)

    # Normalize the vector to get the unit orientation vector
    orientation = vector / np.linalg.norm(vector)

    return orientation


if __name__ == "__main__":
    brain = Brain('fsaverage', 'lh', 'pial', background='white',alpha=0.6)
    # Add the DBS electrode with specified orientation and total length

    contacts = [
        (0, 0, -20),
        (0, 10, -15)]

    orientation = calculate_orientation(contacts[0],contacts[1])

    add_depth_using_first_contact_and_orientation(brain, num_contacts=8, contact_diameter=1.29, contact_length=1.5,
                                                  intercontact_spacing=10, electrode_diameter=1.27, total_length=100,
                                                  position=contacts[0], orientation=orientation)

    # Show the combined brain and electrode plot
    mlab.show()
