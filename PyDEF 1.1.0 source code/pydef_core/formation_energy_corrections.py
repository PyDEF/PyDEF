"""
    Ensemble of corrections to the defect formation energy
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import numpy as np
import copy
import basic_functions as bf
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def potential_alignment_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius, plotsphere=True, display_atom_name=False):
    """ Compute the potential alignment correction by calculating the average difference of electrostatic potentials of atoms
    far away from the defects and their images. This is done by considering spheres around the defects and their images with the
    same radius. Only the atoms outside these spheres (so at a minimum distance from a defect) are considered.

    :param Host_Cell: Cell object of the host cell calculation
    :param Defect_Cell: Cell object of the defect cell calculation
    :param DefectS: list of Defect objects
    :param spheres_radius: radius of the spheres in angstrom (float)
    :param plotsphere: if True, then represent the spheres and positions of the atoms
    :param display_atom_name: if True, display the name of each atom on the representation
    """

    # Positions of the defects and their images
    [f.get_defect_position(Host_Cell.atoms_positions, Defect_Cell.atoms_positions) for f in DefectS]  # retrieve the defects positions

    defects_position = [np.array(f.coord) for f in DefectS]  # positions of the defects

    defect_images_positions = [np.dot(Host_Cell.cell_parameters, f) for f in
                               [[0, 0, 0], [0, 0, -1], [0, 0, 1], [1, 0, 0],
                                [-1, 0, 0], [0, -1, 0], [0, 1, 0]]]  # relative position of the images of the defects

    defects_positions = [[f + g for g in defect_images_positions]
                         for f in defects_position]  # all positions of the defects and their respective images

    # Removing useless data
    atoms_positions_def = copy.deepcopy(Defect_Cell.atoms_positions)  # positions of the atoms in the defect cell
    V_host = copy.deepcopy(Host_Cell.potentials)  # electrostatic potentials of the atoms of the host cell
    V_def = copy.deepcopy(Defect_Cell.potentials)  # electrostatic potentials of the atoms of the defect cell
    atoms_host = list(copy.deepcopy(Host_Cell.atoms))  # atoms labels of the host cell
    atoms_def = list(copy.deepcopy(Defect_Cell.atoms))  # atoms labels of the defect cell

    for Defect in DefectS:
        if Defect.defect_type == 'Vacancy':
            V_host.pop(Defect.atom[0])  # remove the electrostatic potential of the atom removed from the host cell data
            atoms_host.remove(Defect.atom[0])
        elif Defect.defect_type == 'Interstitial':
            V_def.pop(Defect.atom[0])  # remove the electrostatic potential of the atom added from the defect cell data
            atoms_positions_def.pop(Defect.atom[0])  # remove the position of the corresponding atom so the number of positions and potentials match
            atoms_def.remove(Defect.atom[0])
        elif Defect.defect_type == 'Substitutional':
            V_host.pop(Defect.atom[0])
            V_def.pop(Defect.atom[1])
            atoms_positions_def.pop(Defect.atom[1])
            atoms_host.remove(Defect.atom[0])
            atoms_def.remove(Defect.atom[1])

    # Compute the average electrostatic potential outside the spheres
    V_host_list = [V_host[f] for f in atoms_host]
    V_def_list = [V_def[f] for f in atoms_def]
    atoms_positions_def_list = [atoms_positions_def[f] for f in atoms_def]

    distances = [np.array([bf.distance(f, g) for f in atoms_positions_def_list])
                 for g in np.concatenate(defects_positions)]  # distance of each atom from each defect

    min_distances = [min(f) for f in np.transpose(distances)]  # minimum distance between an atom and any defect or its image

    index_out = [np.where(f > spheres_radius)[0] for f in distances]  # index of the atoms outside the spheres which centers are the defects

    common_index_out = bf.get_common_values(index_out)  # index of the atoms outside all the spheres radius

    E_PA = np.array(V_def_list) - np.array(V_host_list)  # difference of electrostatic energy between the defect and host cells
    E_PA_out = np.mean(E_PA[common_index_out])  # average electrostatic difference between the defect and host cells taking into
                                                # account only the atoms outside the spheres

    if plotsphere is True:
        width, height = bf.get_screen_size()
        fig = plt.figure(figsize=(width, height-2.2))
        ax = fig.add_axes([0.01, 0.1, 0.45, 0.8], projection='3d', aspect='equal')

        # Display the spheres and defects
        [bf.plot_sphere(spheres_radius, f[0], ax, '-') for f in defects_positions]  # spheres around the defects
        [[bf.plot_sphere(spheres_radius, f, ax, '--') for f in q[1:]] for q in defects_positions]  # spheres around the images of the defects
        [[ax.scatter(f[0], f[1], f[2], color='red', s=400, marker='*') for f in q] for q in defects_positions]  # Position of the defects objects and images
        [[ax.text(f[0], f[1], f[2] + 0.2, s='$' + g.name + '$', ha='center', va='bottom', color='red', fontsize=20) for f in q]
         for q, g in zip(defects_positions, DefectS)]

        # Atoms positions
        atoms_positions = np.transpose(atoms_positions_def_list)
        scatterplot = ax.scatter(atoms_positions[0], atoms_positions[1], atoms_positions[2], s=100, c=E_PA, cmap='hot', depthshade=False)
        if display_atom_name is True:
            [ax.text(f[0], f[1], f[2], s=g, ha='center', va='bottom') for f, g in zip(atoms_positions_def_list, atoms_def)]

        # Plot parameters
        ax._axis3don = False

        # X limit is set as the maximum value of the projection of the cristallographic parameters on the x-axe, etc.
        ax.set_xlim(0, np.max(np.transpose(Defect_Cell.cell_parameters)[0]))
        ax.set_ylim(0, np.max(np.transpose(Defect_Cell.cell_parameters)[1]))
        ax.set_zlim(0, np.max(np.transpose(Defect_Cell.cell_parameters)[2]))

        # Colorbar
        temp1 = fig.get_window_extent()
        temp2 = ax.get_window_extent()
        ax_cb = fig.add_axes([temp2.x0 / temp1.x1, temp2.y0 / temp1.y1 - 0.04, (temp2.x1 - temp2.x0) / temp1.x1, 0.03])
        cb = fig.colorbar(scatterplot, cax=ax_cb, orientation='horizontal')
        cb.set_label('$\Delta V\ (eV)$', fontsize=24)
        cb.ax.tick_params(width=1.25, length=2, labelsize=16)

        return [E_PA_out, fig]

    else:
        return [min_distances, E_PA, E_PA_out]


def plot_potential_alignment(Host_Cell, Defect_Cell, DefectS, spheres_radius, title_plot, display_atom_name=False):
    """ Draw 3 plots in a same figure
    1) Graphical representation of the positions of the defects and the atoms, and the spheres around the defects
    2) Average electrostatic energy difference between defect and host cells as a function of the spheres radius
    3) Electrostatic energy difference between defect and host cells between each atom as a function of their minimum distance from a defect

    :param Host_Cell: Cell object of the host cell calculation
    :param Defect_Cell: Cell object of the defect cell calculation
    :param DefectS: list of Defect objects
    :param spheres_radius: radius of the spheres in angstrom (float)
    :param title_plot: title of the plot
    :param display_atom_name: if True, display the name of each atom on the representation
    """

    fig = potential_alignment_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius, True, display_atom_name)[1]  # plot the spheres and ions
    min_distances, E_PA = potential_alignment_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius, False)[0:2]  # minimum distance and potential alignment for each atom
    spheres_radii = np.linspace(0, 1, 100) * np.max(Defect_Cell.cell_parameters)
    E_PA_out = [potential_alignment_correction(Host_Cell, Defect_Cell, DefectS, f, False)[-1] for f in spheres_radii]  # mean potential alignment for each spheres radius

    # Average electrostatic energy difference between defect and host cells as a function of the spheres radius
    ax1 = fig.add_subplot(222)
    ax1.plot(spheres_radii, E_PA_out, 'x')
    ax1.plot([spheres_radius, spheres_radius], [-2, 2], '--')  # plot a line corresponding to the current sphere radii value
    ax1.set_xlabel(r'Spheres radius $R$ ($\AA$)', fontsize=22)
    ax1.set_ylabel(r"$\overline{\Delta V(r>R)}$ ($eV$)", fontsize=22)
    ax1.tick_params(width=1.25, length=2, labelsize=16)

    if np.nanmin(E_PA_out) <= 0:
        ax1.set_ylim(bottom=np.round(np.nanmin(E_PA_out) * 1.1, 2))
    else:
        ax1.set_ylim(bottom=np.round(np.nanmin(E_PA_out) * 0.9, 2))

    if np.nanmax(E_PA_out) <= 0:
        ax1.set_ylim(top=np.round(np.nanmax(E_PA_out) * 0.9, 2))
    else:
        ax1.set_ylim(top=np.round(np.nanmax(E_PA_out) * 1.1, 2))

    # Electrostatic energy difference between defect and host cells between each atom as a function of their minimum distance from a defect
    ax2 = fig.add_subplot(224)
    ax2.plot(min_distances, E_PA, 'x')
    ax2.set_xlabel(r'Distance to the closest defect ($\AA$)', fontsize=22)
    ax2.set_ylabel(r"$\Delta V(r)$ ($eV$)", fontsize=22)
    ax2.set_xlim(np.min(min_distances)*0.9, np.max(min_distances)*1.02)
    ax2.tick_params(width=1.25, length=2, labelsize=16)

    if np.nanmin(E_PA) <= 0:
        ax2.set_ylim(bottom=np.round(np.nanmin(E_PA) * 1.1, 2))
    else:
        ax2.set_ylim(bottom=np.round(np.nanmin(E_PA) * 0.9, 2))

    if np.nanmax(E_PA) <= 0:
        ax2.set_ylim(top=np.round(np.nanmax(E_PA) * 0.9, 2))
    else:
        ax2.set_ylim(top=np.round(np.nanmax(E_PA) * 1.1, 2))

    fig.suptitle('$' + title_plot.replace(' ', '\ ') + '$', x=0.22, fontsize=30)
    fig.tight_layout()  # might be removed to solve the non updating 3d plot
    fig.show()


def moss_burstein_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius):
    """ Compute the 'Moss-Burstein' or 'band-filling' correction
    :param Host_Cell: Cell object of the host cell calculation
    :param Defect_Cell: Cell object of the defect cell calculation
    :param DefectS: list of Defect objects
    :param spheres_radius: radius of the spheres in angstrom (float)
    :return: Moss-Burstein correction for acceptors (holes) and donnors (electrons)
    """

    bands_data = Defect_Cell.bands_data
    if Defect_Cell.ispin == 1:
        kpoints_weights = Defect_Cell.kpoints_weights
        max_occupation = 2.
    else:
        kpoints_weights = list(Defect_Cell.kpoints_weights / 2.) * 2
        max_occupation = 1.

    E_PA_out = potential_alignment_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius, False)[-1]
    E_CBM_aligned = Host_Cell.CBM + E_PA_out
    E_VBM_aligned = Host_Cell.VBM + E_PA_out

    E_donnor = - sum([k * sum(f[1] * (f[0] - E_CBM_aligned) * bf.heaviside(f[0] - E_CBM_aligned))
                      for f, k in zip(bands_data, kpoints_weights)])
    E_acceptor = - sum([k * sum((max_occupation - f[1]) * (E_VBM_aligned - f[0]) * bf.heaviside(E_VBM_aligned - f[0]))
                        for f, k in zip(bands_data, kpoints_weights)])

    return [E_acceptor, E_donnor]


def band_extrema_correction(Host_Cell, Host_Cell_B):
    """ Compute the correction of the band extrema computed with a functional (Host_Cell)
    in order to retrieve the same gap computed with another functional (Host_Cell_B)
    :param Host_Cell: Cell object of the host cell calculation
    :param Host_Cell_B: Cell object of the host cell calculation (with a different functional)
    :return:
    """

    DE_VBM = Host_Cell_B.VBM - Host_Cell.VBM
    DE_CBM = Host_Cell_B.CBM - Host_Cell.CBM

    return [DE_VBM, DE_CBM]


def phs_correction(z_h, z_e, DE_VBM, DE_CBM):
    """ Compute the PHS correction
    :param z_h: number of holes in the PHS
    :param z_e: number of electrons in the PHS
    :param DE_VBM: correction of the VBM
    :param DE_CBM: correction of the CBM
    """
    return [- z_h * DE_VBM, z_e * DE_CBM]


def vbm_correction(Defect_Cell, DE_VBM):
    """ Correction of the VBM energy
    :param Defect_Cell: Cell object of the defect cell calculation
    :param DE_VBM: correction of the VBM
    """

    return Defect_Cell.charge * DE_VBM


def makov_payne_correction(Defect_Cell, geometry, e_r, mk_1_1):
    """
    :param Defect_Cell: Cell object of the defect cell calculation
    :param geometry: geometry of the host cell
    :param e_r: relative permittivity
    :param mk_1_1: Value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1
    """

    c_sh_dico = {'sc': -0.369, 'fcc': -0.343, 'bcc': -0.342, 'hcp': -0.478, 'other': -1./3}
    c_sh = c_sh_dico[geometry]

    return (1. + c_sh * (1. - 1./e_r)) * Defect_Cell.charge**2 * mk_1_1 / e_r
