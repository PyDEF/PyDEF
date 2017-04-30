"""
    Defect study module
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import copy
import string

import matplotlib.pyplot as plt
import matplotlib.ticker as tk
import numpy as np

import basic_functions as bf
import figure as pf
import formation_energy_corrections as zc
import cell as cc


class Defect_Cell_Study:
    """ Object containing data on the various corrections of the defect formation energy for a given defect cell """

    def __init__(self, Host_Cell, Defect_Cell, DefectS, spheres_radius, z_e, z_h, geometry, e_r, mk_1_1, DE_VBM, DE_CBM,
                 potential_alignment_correction=True, moss_burstein_correction=True, phs_correction=True,
                 vbm_correction=True, makov_payne_correction=True):

        """
        :param Host_Cell: Cell object of the host cell calculation
        :param Defect_Cell: Cell object of the defect cell calculation
        :param DefectS: list of Defect objects
        :param spheres_radius: radius of the spheres in angstrom (float)
        :param z_e: number of electrons in the PHS
        :param z_h: number of holes in the PHS
        :param geometry: geometry of the host cell
        :param e_r: relative permittivity
        :param mk_1_1: value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1
        :param DE_VBM: correction of the VBM
        :param DE_CBM: correction of the CBM
        :param potential_alignment_correction: if True, the potential alignment correction is done
        :param moss_burstein_correction: if True, the Moss-Burstein correction is done
        :param phs_correction: if True, the PHS correction is done
        :param vbm_correction: if True, the VBM correction is done
        :param makov_payne_correction: if True, the Makov-Payne correction is done
        """

        self.Host_Cell = Host_Cell
        self.Defect_Cell = Defect_Cell
        self.DefectS = DefectS
        self.spheres_radius = spheres_radius

        # Check that the Host Cell and the Defect Cell have the same cristal parameters
        if Host_Cell.cell_parameters != Defect_Cell.cell_parameters:
            raise bf.PydefDefectCellError("The host cell is not consistent with the defect cell")

        # if Defect_Cell.isym != 0:
        #    raise bf.PydefDefectCellError('You should se ISYM to 0')

        # Title of the defects for display (name of the defects + charge of the cell)
        if len(DefectS) == 1:
            self.defects_title = self.DefectS[0].name + '^{' + bf.float_to_str(int(self.Defect_Cell.charge)) + '}'
        else:
            self.defects_title = '(' + ' & '.join([f.name for f in self.DefectS]) + ')^{' \
                                 + bf.float_to_str(int(self.Defect_Cell.charge)) + '}'

        # Title of the Defect Cell Study for display
        self.title = Host_Cell.display_rname + ' - ' + self.defects_title

        # --------------------------------------------- CORRECTIONS ---------------------------------------------------

        if potential_alignment_correction is True:
            self.pa_corr_temp = zc.potential_alignment_correction(Host_Cell, Defect_Cell, DefectS,
                                                                  spheres_radius, False)[-1]
            self.pa_corr = self.pa_corr_temp * Defect_Cell.charge
        else:
            self.pa_corr = 0.0

        if moss_burstein_correction is True:
            self.mb_corr = zc.moss_burstein_correction(Host_Cell, Defect_Cell, DefectS, spheres_radius)
        else:
            self.mb_corr = [0.0, 0.0]

        if phs_correction is True:
            self.phs_corr = zc.phs_correction(z_h, z_e, DE_VBM, DE_CBM)
        else:
            self.phs_corr = [0.0, 0.0]

        if vbm_correction is True:
            self.vbm_corr = zc.vbm_correction(Defect_Cell, DE_VBM)
        else:
            self.vbm_corr = 0.0

        if makov_payne_correction is True:
            self.mp_corr = zc.makov_payne_correction(Defect_Cell, geometry, e_r, mk_1_1)
        else:
            self.mp_corr = 0.0

        # Total correction
        self.tot_corr = self.pa_corr + sum(self.mb_corr) + sum(self.phs_corr) + self.vbm_corr + self.mp_corr

        self.E_for_0 = Defect_Cell.energy - Host_Cell.energy + sum([f.n * f.chem_pot for f in DefectS]) \
                       + Defect_Cell.charge * Host_Cell.VBM + self.tot_corr

    def plot_potential_alignment(self, show_atoms_label):
        """ Draw 3 plots in a same figure
        1) Graphical representation of the positions of the defects and the atoms, and the spheres around the defects
        2) Average electrostatic energy difference between defect and host cells as a function of the spheres radius
        3) Electrostatic energy difference between defect and host cells between each atom as a function of their
           minimum distance from a defect

        :param show_atoms_label: if True, display the atom label on the 3D representation
        """

        zc.plot_potential_alignment(self.Host_Cell, self.Defect_Cell, self.DefectS, self.spheres_radius, self.title,
                                    show_atoms_label)


class Defect_Study:
    """ Object containing different Defect_Cell_Study objects """

    def __init__(self, Host_Cell, Host_Cell_B, DefectS, geometry, e_r, mk_1_1, DE_VBM_input, DE_CBM_input, gaps_input,
                 potential_alignment_correction=True, moss_burstein_correction=True, phs_correction=True,
                 vbm_correction=True, makov_payne_correction=True):
        """
        :param Host_Cell: Cell object of the host cell calculation
        :param Host_Cell_B: Cell object of the host cell calculation (with a different functional)
        :param DefectS: list of Defect objects
        :param geometry: geometry of the host cell
        :param e_r: relative permittivity
        :param mk_1_1: value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1
        :param DE_VBM_input: further correction of the VBM
        :param DE_CBM_input: further correction to the CBM
        :param gaps_input: experimental gaps as a string such as '2.4, Indirect gap, 2.8, Direct gap'
        :param potential_alignment_correction: if True, the potential alignment correction is done
        :param moss_burstein_correction: if True, the Moss-Burstein correction is done
        :param phs_correction: if True, the PHS correction is done
        :param vbm_correction: if True, the VBM correction is done
        :param makov_payne_correction: if True, the Makov-Payne correction is done
        """

        self.Host_Cell = Host_Cell
        self.DefectS = DefectS

        self.Host_Cell_B = Host_Cell_B
        self.geometry = geometry
        self.e_r = e_r
        self.mk_1_1 = mk_1_1
        self.gaps_input = gaps_input
        self.DE_VBM_input = DE_VBM_input
        self.DE_CBM_input = DE_CBM_input

        self.defect_cell_studies = {}

        # Corrections
        self.potential_alignment_correction = potential_alignment_correction
        self.moss_burstein_correction = moss_burstein_correction
        self.phs_correction = phs_correction
        self.vbm_correction = vbm_correction
        self.makov_payne_correction = makov_payne_correction

        # ID & Title
        self.defects_title = ' & '.join([f.name for f in DefectS])
        if len(DefectS) > 1:
            self.defects_label = '(' + self.defects_title + ')'
        else:
            self.defects_label = self.defects_title

        if (self.vbm_correction is True or self.phs_correction is True) and (Host_Cell != Host_Cell_B):
            self.ID = Host_Cell.ID + '_corr_' + Host_Cell_B.functional + '_' + '_'.join([f.ID for f in DefectS])

            self.title = Host_Cell.display_rname + ' - ' + Host_Cell.functional_title + ' corrected ' + \
                         Host_Cell_B.functional_title + ' - ' + self.defects_title
        else:
            self.ID = Host_Cell.ID + '_' + '_'.join([f.ID for f in DefectS])

            self.title = Host_Cell.display_rname + ' - ' + Host_Cell.functional_title + ' - ' + self.defects_title

        # Correction of the band extrema
        if self.vbm_correction is True or self.phs_correction is True:
            self.DE_VBM = zc.band_extrema_correction(Host_Cell, Host_Cell_B)[0] + self.DE_VBM_input
            self.DE_CBM = zc.band_extrema_correction(Host_Cell, Host_Cell_B)[1] + self.DE_CBM_input
        else:
            self.DE_VBM = 0.0
            self.DE_CBM = 0.0

        # Gaps
        if gaps_input != ['']:
            gaps_labels = [f.strip() for f in gaps_input[1::2]]  # list of gaps label
            gaps = [float(f) for f in gaps_input[0::2]]  # values of the gaps
            self.gaps = dict(zip(gaps_labels, gaps))
        else:
            self.gaps = {}
        self.gaps['Calculated gap'] = self.Host_Cell.gap - self.DE_VBM + self.DE_CBM

        # Plot parameters
        self.dpp = Dos_Plot_Parameters(Host_Cell)
        self.fpp = Formation_Plot_Parameters(self)
        self.tpp = Transition_Plot_Parameters(self)

    def create_defect_cell_study(self, Defect_Cell, spheres_radius, z_e, z_h):
        """
        :param Defect_Cell: Call object of the defect cell
        :param spheres_radius: radius of the spheres
        :param z_e: number of electrons in the conduction band of the defect cell
        :param z_h: number of holes in the valence band of the defect cell
        """

        defect_cell_study = Defect_Cell_Study(self.Host_Cell, Defect_Cell, self.DefectS, spheres_radius, z_e, z_h,
                                              self.geometry, self.e_r, self.mk_1_1, self.DE_VBM, self.DE_CBM,
                                              self.potential_alignment_correction, self.moss_burstein_correction,
                                              self.phs_correction, self.vbm_correction, self.makov_payne_correction)

        self.defect_cell_studies[Defect_Cell.ID] = defect_cell_study

    def plot_dos(self):
        """ Plot the DOS of the host cell and each defect cell in the study """

        Host_Cell = copy.deepcopy(self.Host_Cell)
        defect_cell_studies = copy.deepcopy(self.defect_cell_studies)

        if hasattr(Host_Cell, 'doscar') is False:
            print('DOSCAR missing')
            return None

        for study in defect_cell_studies.values():
            if hasattr(study.Defect_Cell, 'doscar') is False:
                print('DOSCAR missing')
                return None

        nb_rows = len(defect_cell_studies) + 1

        # Figure
        figure = pf.Figure(nb_rows, 1, 'Comparison of the DOS of %s' % self.ID)

        # Host Cell
        Host_Cell.dpp = cc.Dos_Plot_Parameters(Host_Cell)
        Host_Cell.dpp.figure = figure
        Host_Cell.dpp.DOS_range = self.dpp.DOS_range
        Host_Cell.dpp.display_Fermi_level = False
        Host_Cell.dpp.display_BM_levels = True
        Host_Cell.dpp.E_range = self.dpp.E_range
        Host_Cell.dpp.label_display = True
        Host_Cell.dpp.xlabel_display = False
        Host_Cell.dpp.ylabel_display = False
        Host_Cell.dpp.common_ylabel_display = True
        Host_Cell.dpp.xticklabels_display = False
        Host_Cell.dpp.title = Host_Cell.display_rname

        cell_studies = defect_cell_studies.values()
        cell_charges = [f.Defect_Cell.charge for f in cell_studies]

        # Change the plot parameters for all defect cell
        for i, j in zip(np.argsort(cell_charges), range(2, len(cell_charges) + 2)):
            cell_studies[i].Defect_Cell.dpp = cc.Dos_Plot_Parameters(cell_studies[i].Defect_Cell)
            cell_studies[i].Defect_Cell.dpp.figure = figure
            cell_studies[i].Defect_Cell.dpp.subplot_nb = j
            cell_studies[i].Defect_Cell.dpp.DOS_range = self.dpp.DOS_range
            cell_studies[i].Defect_Cell.dpp.E_range = self.dpp.E_range
            cell_studies[i].Defect_Cell.dpp.title = cell_studies[i].title
            cell_studies[i].Defect_Cell.dpp.label_display = True
            cell_studies[i].Defect_Cell.dpp.xlabel_display = False
            cell_studies[i].Defect_Cell.dpp.ylabel_display = False
            cell_studies[i].Defect_Cell.dpp.display_legends = False
            cell_studies[i].Defect_Cell.dpp.xticklabels_display = False
            if self.dpp.align_potential is True:
                cell_studies[i].Defect_Cell.dpp.input_shift = cell_studies[i].pa_corr_temp
                print cell_studies[i].Defect_Cell.dpp.input_shift
            #if atoms is not False:
            #    cell_studies[i].Defect_Cell.dpp.dos_type = 'OPA'
            #    cell_studies[i].Defect_Cell.dpp.choice_opa = [f.atom[-1] for f in self.DefectS]

            if j == len(cell_charges) + 1:
                cell_studies[i].Defect_Cell.dpp.xticklabels_display = True
                cell_studies[i].Defect_Cell.dpp.xlabel_display = True

            cell_studies[i].Defect_Cell.plot_dos()

        Host_Cell.plot_dos()

    def get_formation_energy_low_EF(self, E_Fermi):
        """ Get the lowest formation energy at a given value of the Fermi energy """

        # all formation energies at E_Fermi
        E_for_EF = [f.E_for_0 + f.Defect_Cell.charge * E_Fermi for f in self.defect_cell_studies.itervalues()]

        # Corresponding charges
        charges = [f.Defect_Cell.charge for f in self.defect_cell_studies.itervalues()]

        # return Fermi energy, minimum formation energy at E_Fermi, charge of defect and defect label
        return [[E_Fermi, f, g] for f, g in zip(E_for_EF, charges) if f == min(E_for_EF)][0]

    def get_transition_levels(self, E_Fermi_range):
        """ Retrieve all transitions levels energy
        :param E_Fermi_range: range of Fermi energies
        """

        # lowest formation energy and corresponding charge of the defect(s)
        E_for_low, q_low = np.transpose([self.get_formation_energy_low_EF(f) for f in E_Fermi_range])[1:]

        # indices of the transitions
        transition_indices = np.where(np.diff(q_low) != 0.)[0] + 1

        # for each transition, return the fermi energy, the formation energy, the new charge and old charge states
        return [[E_Fermi_range[f], E_for_low[f], q_low[f], q_low[f-1]]for f in transition_indices]

    def plot_formation_energy(self):
        """ Plot the defect formation energy as a function of the Fermi level energy """

        E_Fermi = np.linspace(self.fpp.E_range[0], np.max(self.gaps.values() +
                                                          [self.fpp.E_range[1]]), 10000)  # energies of the Fermi level
        E_for = [f.E_for_0 + f.Defect_Cell.charge * E_Fermi for f
                 in self.defect_cell_studies.itervalues()]  # corresponding formation energies
        E_for_low = np.transpose([self.get_formation_energy_low_EF(f) for f in E_Fermi])[1]
        transition_levels = self.get_transition_levels(E_Fermi)

        # ------------------------------------------- FIGURE PARAMETERS ------------------------------------------------

        fig, ax = formation_figure_parameters(self.fpp)

        # -------------------------------------------- PLOT PARAMETERS -------------------------------------------------

        [ax.plot(E_Fermi, f, color='black', linewidth=1.5) for f in E_for]  # formation energies
        ax.plot(E_Fermi, E_for_low, color='black', linewidth=4)  # lowest formation energy
        [ax.plot([f[1], f[1]], [ax.get_ylim()[0], ax.get_ylim()[1]], label=f[0], linewidth=2, linestyle='--')
         for f in self.gaps.iteritems()]

        if self.fpp.display_charges is True:
            charges = [f.Defect_Cell.charge for f in self.defect_cell_studies.itervalues()]
            [charges_annotation(E_Fermi, f, g, ax, self.fpp.text_size - 3) for f, g in zip(E_for, charges)]

        if self.fpp.display_transition_levels is True:
            for level in transition_levels:
                ax.plot([level[0], level[0]], [ax.get_ylim()[0], level[1]], linestyle='--', color='black')
                text = r'$\epsilon(' + bf.float_to_str(level[3]) + '/' + bf.float_to_str(level[2]) + ')$'
                annotation = ax.annotate(text, xy=(level[0], ax.get_ylim()[0] + 0.1 * np.diff(ax.get_ylim())[0]),
                                         ha='center', va='top', fontsize=self.fpp.text_size - 2, backgroundcolor='w')
                annotation.draggable()

        legend = ax.legend(loc='best', fancybox=True, fontsize=self.fpp.text_size - 2)
        legend.draggable()

        fig.tight_layout()
        fig.show()

    def plot_transition_levels(self):
        """ Plot the transition levels of the study """

        E_Fermi = np.linspace(self.tpp.E_range[0], self.tpp.E_range[1], 30000)  # range of fermi energies
        transition_levels = self.get_transition_levels(E_Fermi)  # all transition levels in the range of fermi energies
        gap = self.gaps[self.tpp.gap_choice]

        # ------------------------------------------- FIGURE PARAMETERS -----------------------------------------------

        fig, ax = transition_figure_parameters(self.tpp)
        ax.set_xlim(-0.01, 1.2)

        # -------------------------------------------- PLOT PARAMETERS ------------------------------------------------

        ax.stackplot([0, 0, 1.1, 1.1], [[0, ax.get_ylim()[0]-1, ax.get_ylim()[0]-1, 0]], colors=['grey'], linewidths=4)
        ax.plot([0, 0, 1.1, 1.1], [ax.get_ylim()[1], gap, gap, ax.get_ylim()[1]], color='black', linewidth=4)

        ax.annotate(' $VBM$', xy=(1.1, 0.0), fontsize=self.tpp.text_size, va='center', ha='left').draggable()
        ax.annotate(' $CBM$', xy=(1.1, gap), fontsize=self.tpp.text_size, va='center', ha='left').draggable()

        for transition in transition_levels:
            ax.plot([0.1, 1], [transition[0], transition[0]], linewidth=2, color='black')
            charges = sorted(list(set(np.concatenate([f[2:] for f in transition_levels]))), reverse=True)
            tr_fermi = [f[0] for f in transition_levels]
            for charge, tr in zip(charges, [tr_fermi[0] - 0.06] + list(tr_fermi[:-1] + np.diff(tr_fermi)/2.0) + [tr_fermi[-1] + 0.06]):
                ax.annotate('$' + bf.float_to_str(charge) + '$', xy=(0.55, tr), fontsize=self.tpp.text_size,
                            va='center', ha='center').draggable()

        fig.tight_layout()
        fig.show()

    def save_results(self, filename):
        """
        :param filename:
        :return:
        """

        filename.write('HOST CELL\n')
        filename.write('ID: \t %s \n' % self.Host_Cell.ID)
        filename.write('Method: \t %s \n' % self.Host_Cell.functional)
        filename.write('Energy: \t %.5f eV \n' % self.Host_Cell.energy)
        filename.write('VBM: \t %.5f eV \n' % self.Host_Cell.VBM)
        filename.write('CBM: \t %.5f eV \n' % self.Host_Cell.CBM)
        filename.write('Gap: \t %.5f eV \n' % self.Host_Cell.gap)

        if self.Host_Cell != self.Host_Cell_B:
            filename.write('\nHOST CELL B\n')
            filename.write('ID: \t %s \n' % self.Host_Cell_B.ID)
            filename.write('Method: \t %s \n' % self.Host_Cell_B.functional)
            filename.write('VBM: \t %.5f eV \n' % self.Host_Cell_B.VBM)
            filename.write('CBM: \t %.5f eV \n' % self.Host_Cell_B.CBM)
            filename.write('Gap: \t %.5f eV \n' % self.Host_Cell_B.gap)

        filename.write('\nGAP CORRECTION\n')
        filename.write('DE_V: %.5f eV \n' % self.DE_VBM)
        filename.write('DE_C: %.5f eV \n' % self.DE_CBM)

        filename.write('\nDEFECTS\n')
        filename.write('Name\tType\tatom(s)\tcoordinates\tchemical potential(s) (eV)\tn\n')
        for defect in self.DefectS:
            filename.write(defect.ID + '\t' + defect.defect_type + '\t' + '&'.join(defect.atom) + '\t' +
                           str(defect.coord) + '\t' + str(defect.chem_pot) + '\t' + str(defect.n) + '\n')

        filename.write('\nDEFECT CELLS\n')
        filename.write('Name\tCharge\tEnergy\tVBM correction\tPHS correction (holes)\tPHS correction (electrons)'
                       '\tPotential alignment\tMoss-Burstein correction (holes)\tMoss-Burstein correction (electrons)'
                       '\tMakov-Payne correction\tTotal\n')
        for cell in self.defect_cell_studies.itervalues():
            filename.write(cell.Defect_Cell.ID + '\t' + str(int(cell.Defect_Cell.charge)) +
                           '\t %.5f' % cell.Defect_Cell.energy + '\t %.5f' % cell.vbm_corr +
                           '\t %.5f' % cell.phs_corr[0] + '\t %.5f' % cell.phs_corr[1] + '\t %.5f' % cell.pa_corr +
                           '\t %.5f' % cell.mb_corr[0] + '\t %.5f' % cell.mb_corr[1] + '\t %.5f' % cell.mp_corr +
                           '\t %.5f' % cell.tot_corr + '\n')

        filename.write('\nCORRECTIONS PARAMETERS\n')
        filename.write('Name\tNb of electrons\tSpheres radius\n')
        for cell in self.defect_cell_studies.itervalues():
            filename.write(cell.Defect_Cell.ID + '\t' + str(int(cell.Defect_Cell.nb_electrons)) +
                           '\t %.5f' % cell.spheres_radius + '\n')

        filename.write('\nTRANSITION LEVELS\n')
        for level in self.get_transition_levels(np.linspace(self.tpp.E_range[0], self.tpp.E_range[1], 100000)):
            filename.write('%.0f' % level[3] + '\%.0f' % level[2] + ' : %.5f' % level[0] + 'eV\n')

        filename.close()


class Dos_Plot_Parameters:
    """ Plot parameters for the DOS """

    def __init__(self, aCell):
        """
        :param aCell: Cell object
        """

        self.DOS_range = [0, 50]  # DOS range displayed
        self.E_range = np.sort([aCell.emin, aCell.emax])  # Energy range displayed
        self.align_potential = False


class Formation_Plot_Parameters:
    """ Plot parameters for the formation levels """

    def __init__(self, aDefect_Study):
        """
        :param aDefect_Study: Defect_Study or Material_Study object
        """

        # DEFECT STUDIES & MATERIAL STUDIES

        # Plot parameters
        self.E_range = [0, max(aDefect_Study.gaps.values()) * 1.05]  # Fermi energy range displayed
        self.for_range = ['auto', 'auto']  # formation energy range displayed
        self.display_transition_levels = True  # if True, display the transitions levels
        self.display_charges = True  # if True, display the charges associated with the formation energy lines

        # Figure parameters
        self.figure = pf.Figure(1, 1, 'New Figure')  # PyDEF Figure object
        self.subplot_nb = 1  # subplot number
        self.title = aDefect_Study.title
        self.label_display = False  # if True, the display of the axis labels is controlled by 'xlabel_display'
                                    # and 'ylabel_display'
        self.xlabel_display = True  # if True, the x axis label is displayed
        self.ylabel_display = True  # if True, the y axis label is displayed
        self.common_ylabel_display = False  # if True, a common y axis label is displayed
        self.xticklabels_display = True  # if True, the x axis ticks labels are displayed
        self.yticklabels_display = True  # if True, the y axis ticks labels are displayed
        self.text_size = 24  # size of the text

        # MATERIAL STUDIES
        self.display_colored_lines = True  # if True, display a light version of the defect name
        self.display_charges_light = True  # if True, display only the charge of the associated line
        self.highlight_charge_change = True  # if True, highlight charge change
        self.lines_colors = ['red', 'yellowgreen', 'blue', 'y', 'black', 'brown', 'darkgreen', 'navy', 'gold',
                             'm', 'teal', 'darkmagenta']*10
        self.display_gaps_legend = True


class Transition_Plot_Parameters:
    """ Plot parameters for the transition level diagram """

    def __init__(self, aDefect_Study):

        # Plot parameters
        self.E_range = [-0.5, max(aDefect_Study.gaps.values()) * 1.05]  # Fermi energy range
        self.gap_choice = 'Calculated gap'  # gap displayed (i.e. position of the CBM with respect to the VBM)

        # Figure parameters
        self.figure = pf.Figure(1, 1, 'New Figure')  # Figure
        self.subplot_nb = 1  # subplot number
        self.title = aDefect_Study.title
        self.text_size = 24  # size of the text
        self.label_display = False  # if True, the display of the axis labels is controlled by 'xlabel_display'
                                    # and 'ylabel_display' variables
        self.ylabel_display = True  # if True, the y axis label is displayed
        self.common_ylabel_display = False  # if True, a common y axis label is displayed
        self.yticklabels_display = False  # if True, the y axis ticks labels are displayed

        # Onlt for Material_Study object
        self.display_formation_energy = True


def charges_annotation(E_Fermi, E_for, charge, ax, text_size):
    """ Add an annotation giving the charge of the formation energy at the beginning of the line
    :param E_Fermi: Fermi energy range
    :param E_for: defect formation energy for a given charge 'charge'
    :param charge: charge associated with the defect formation energy
    :param ax: matplotlib.axes object
    :param text_size: size of the text
    """

    if float(charge) > 0:
        index = np.where(np.abs(E_for - ax.get_ylim()[0]) < 5e-4)[0]
        if len(index) != 0:
            coordinates = (E_Fermi[index[-1]], E_for[index[-1]])  # coordinates of the annotation
            hor_al = 'center'  # horizontal alignment of the annotation
            ver_al = 'bottom'  # vertical alignment of the annotation
        else:
            coordinates = (E_Fermi[0] + 0.01 * E_Fermi[-1], E_for[0] + float(charge) * 0.05 * E_Fermi[-1])
            hor_al = 'left'
            ver_al = 'center'
    else:
        index = np.where(np.abs(E_for - ax.get_ylim()[1]) < 5e-4)[0]
        if len(index) != 0:
            coordinates = (E_Fermi[index[0]], E_for[index[0]])
            hor_al = 'center'
            ver_al = 'top'

        else:
            coordinates = (E_Fermi[0] + 0.01 * E_Fermi[-1], E_for[0] + float(charge) * 0.05 * E_Fermi[-1])
            hor_al = 'left'
            ver_al = 'center'

    annotation = ax.annotate('$q = %s$' % bf.float_to_str(charge), xy=coordinates,
                             bbox=dict(boxstyle='square', fc='1', pad=0.05),
                             ha=hor_al, va=ver_al, fontsize=text_size)
    annotation.draggable()


def formation_figure_parameters(fpp):
    """ Figure parameters for formation energy plots
    :param fpp: Formation_Plot_Parameters object
    """

    width, height = bf.get_screen_size()
    if fpp.figure.name == 'New Figure':
        fig = plt.figure(figsize=(width, height-2.2))
    else:
        fig = plt.figure(fpp.figure.name, figsize=(width, height-2.2))

    ax = fig.add_subplot(fpp.figure.nb_rows, fpp.figure.nb_cols, fpp.subplot_nb)

    # Main title
    if fpp.figure.nb_rows == 1 and fpp.figure.nb_cols == 1:
        new_title = '$' + fpp.title.replace(' ', '\ ') + '$'
    else:
        # add a letter for labelling
        new_title = '$' + fpp.title.replace(' ', '\ ') + '$' + [' ' + f + ')' for f in list(string.ascii_lowercase)][fpp.subplot_nb - 1]

    ax.set_title(new_title, fontsize=fpp.text_size, fontweight='bold')

    # Axes titles
    xlabel = r'$\Delta E_F\ (eV)$'
    ylabel = '$E_{for}^q\ (eV)$'

    if fpp.label_display is True:  # custom label display
        if fpp.xlabel_display is True:
            ax.set_xlabel(xlabel, fontsize=fpp.text_size)
        if fpp.ylabel_display is True:
            ax.set_ylabel(ylabel, fontsize=fpp.text_size)
        if fpp.common_ylabel_display is True:
            fig.text(0.017, 0.5, ylabel, ha='center', va='center', rotation='vertical', fontsize=fpp.text_size)
        if fpp.xticklabels_display is False:
            plt.setp(ax.get_xticklabels(), visible=False)
        if fpp.yticklabels_display is False:
            plt.setp(ax.get_yticklabels(), visible=False)

    else:  # automatic label display (assuming that the energy range is the same for all plots)
        if fpp.subplot_nb >= (fpp.figure.nb_rows - 1) * fpp.figure.nb_cols + 1:
            ax.set_xlabel(xlabel, fontsize=fpp.text_size)
        else:
            plt.setp(ax.get_xticklabels(), visible=False)

        if fpp.subplot_nb in np.array(range(fpp.figure.nb_rows)) * fpp.figure.nb_cols + 1:
            ax.set_ylabel(ylabel, fontsize=fpp.text_size)
        else:
            plt.setp(ax.get_yticklabels(), visible=False)

    ax.tick_params(width=1.5, length=4, labelsize=fpp.text_size - 2)
    ax.set_xlim(fpp.E_range)
    if fpp.for_range != ['auto', 'auto']:
        ax.set_ylim(float(fpp.for_range[0]), float(fpp.for_range[1]))
    ax.grid('on')

    return fig, ax


def transition_figure_parameters(tpp):
    """ Figure parameters for Transition levels plots
    :param tpp: Transition_Plot_Parameters object
    """

    width, height = bf.get_screen_size()
    if tpp.figure.name == 'New Figure':
        fig = plt.figure(figsize=(width, height-2.2))
    else:
        fig = plt.figure(tpp.figure.name, figsize=(width, height-2.2))

    ax = fig.add_subplot(tpp.figure.nb_rows, tpp.figure.nb_cols, tpp.subplot_nb)

    # Main title
    if tpp.figure.nb_rows == 1 and tpp.figure.nb_cols == 1:
        new_title = '$' + tpp.title.replace(' ', '\ ') + '$'
    else:
        # add a letter for labelling
        new_title = '$' + tpp.title.replace(' ', '\ ') + '$' + \
                    [' ' + f + ')' for f in list(string.ascii_lowercase)][tpp.subplot_nb - 1]

    ax.set_title(new_title, fontsize=tpp.text_size, fontweight='bold')

    # Axis titles
    ylabel = r'$ \Delta E_F\ (eV)$'

    if tpp.label_display is True:  # custom label display
        if tpp.ylabel_display is True:
            ax.set_ylabel(ylabel, fontsize=tpp.text_size)
        if tpp.common_ylabel_display is True:
            fig.text(0.017, 0.5, ylabel, ha='center', va='center', rotation='vertical', fontsize=tpp.text_size)
        if tpp.yticklabels_display is False:
            plt.setp(ax.get_yticklabels(), visible=False)
    else:
        if tpp.subplot_nb in np.array(range(tpp.figure.nb_rows)) * tpp.figure.nb_cols + 1:
            ax.set_ylabel(ylabel, fontsize=tpp.text_size)
        else:
            plt.setp(ax.get_yticklabels(), visible=False)

    ax.tick_params(width=1.5, length=4, labelsize=tpp.text_size - 4, axis='y')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.xaxis.set_major_locator(tk.NullLocator())
    ax.yaxis.set_ticks_position('left')

    ax.set_ylim(tpp.E_range[0], tpp.E_range[1])

    return fig, ax
