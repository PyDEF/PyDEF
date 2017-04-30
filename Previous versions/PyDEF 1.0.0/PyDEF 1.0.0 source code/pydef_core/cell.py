"""
    Module used to import results of VASP calculations in PyDEF
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""
import matplotlib; matplotlib.use('TkAgg')  # (to avoid "terminating with uncaught exception of type NSException" error)
import matplotlib.backends.backend_tkagg  # (for compilation)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tk
import re
import string
# plt.rcParams.update({'mathtext.default': 'regular'})

import basic_functions as bf
import figure as fc


class Cell:
    """ Object containing various data on a calculation """

    def __init__(self, OUTCAR, DOSCAR):
        """
        :param OUTCAR: location of the OUTCAR file (string)
        :param DOSCAR: location of the DOSCAR file (string)
        :return: an object containing data on the calculation
        """

        # --------------------------------------------------- OUTCAR ---------------------------------------------------

        self.OUTCAR = OUTCAR
        self.DOSCAR = DOSCAR

        self.outcar = bf.read_file(OUTCAR)  # content of the OUTCAR file

        if self.outcar[0][:6] != ' vasp.':
            raise bf.PydefOutcarError('The given file appears to not be a valid OUTCAR file.')

        # ------------------------------------------- CALCULATION PROPERTIES -------------------------------------------

        self.functional, self.functional_title = get_functional(self.outcar)  # functional used
        self.nedos = bf.grep(self.outcar, 'NEDOS =', 0, 'number of ions', 'int', 1)  # number of point in the DOS
        self.encut = bf.grep(self.outcar, 'ENCUT  =', 0, 'eV', 'float', 1)  # ENCUT used
        self.ediff = bf.grep(self.outcar, 'EDIFF  =', 0, 'stopping', 'float', 1)  # EDIFF value
        self.emin = bf.grep(self.outcar, 'EMIN   =', 0, ';', 'float', 1)  # minimum energy for the DOS
        self.emax = bf.grep(self.outcar, 'EMAX   =', 0, 'energy-range', 'float', 1)  # maximum energy for the DOS
        self.ismear = bf.grep(self.outcar, 'ISMEAR =', 0, ';', 'int', 1)  # ISMEAR used
        self.lorbit = bf.grep(self.outcar, 'LORBIT =', 0, '0 simple, 1 ext', 'int', 1)  # LORBIT used
        self.isym = bf.grep(self.outcar, 'ISYM   =', 0, '0-nonsym', 'float', 1)  # ISYM used
        self.istart = bf.grep(self.outcar, 'ISTART =', 0, 'job', 'float', 1)  # ISTART tag

        # --------------------------------------------- SYSTEM PROPERTIES ----------------------------------------------

        self.nb_atoms_tot = bf.grep(self.outcar, 'NIONS =', 0, False, 'int', 1)  # total number of atoms
        self.nb_atoms = [int(f) for f in bf.grep(self.outcar, 'ions per type =', 0).split()]  # population of each atomic species
        self.atoms_types = [bf.grep(self.outcar, 'VRHFIN =', f, ':') for f in range(len(bf.grep(self.outcar, 'VRHFIN =')))]  # atomic species
        self.population = dict(zip(self.atoms_types, self.nb_atoms))
        self.atoms_valence = [int(float(f)) for f in bf.grep(self.outcar, 'ZVAL   =', -1).split()]  # valence of each atomic species
        self.atoms = np.concatenate([[f + ' (' + str(g) + ')' for g in range(1, q + 1)] for f, q in zip(self.atoms_types, self.nb_atoms)])  # atoms list
        self.nb_electrons = bf.grep(self.outcar, 'NELECT =', 0, 'total number', 'float', 1)  # total number of electrons
        self.charge = sum(np.array(self.nb_atoms) * np.array(self.atoms_valence)) - self.nb_electrons
        self.orbitals = [f for f in bf.grep(self.outcar, '# of ion', 0, 'tot').split(' ') if f != '']

        # verification of the consistence of the data retrieved
        if self.nb_atoms_tot != sum(self.nb_atoms) or \
                len(self.nb_atoms) != len(self.atoms_types) or \
                len(self.nb_atoms) != len(self.atoms_valence):
            raise bf.PydefImportError('Numbers of atoms retrieved are not consistent')

        self.name, self.display_name = get_system_name(self.atoms_types, self.nb_atoms, False)
        self.rname, self.display_rname = get_system_name(self.atoms_types, self.nb_atoms, True)

        # --------------------------------------------- CALCULATION RESULT ---------------------------------------------

        # Number of electronic steps
        if self.functional != 'G0W0@GGA' and self.functional != 'GW0@GGA':
            self.nb_iterations = len(bf.grep(self.outcar, 'Iteration'))  # for non GW calculations
        else:
            self.nb_iterations = bf.grep(self.outcar, 'NELM    =', 0, 'number', 'int', 1)  # for GW calculations

        # Cristallographic properties
        self.cell_parameters = get_cell_parameters(self.outcar)  # cristallographic parameters
        self.atoms_positions = get_atoms_positions(self.outcar, self.atoms)  # atoms positions

        # Energy & Density of states
        self.energy = bf.grep(self.outcar, 'free energy    TOTEN  =', -1, 'eV', 'float', self.nb_iterations)  # total energy
        self.fermi_energy = bf.grep(self.outcar, ' BZINTS: Fermi energy:', -1, ';', 'float')  # fermi energy
        if self.ismear == 0:
            self.fermi_energy = bf.grep(self.outcar, 'E-fermi :', 0, 'XC(G=0)', 'float', nb_found=1)
        self.nkpts = bf.grep(self.outcar, 'NKPTS =', 0, 'k-points in BZ', 'int', 1)  # number of k-points
        self.kpoints_weights = get_kpoints_weight(self.outcar, self.nkpts)
        self.nbands = bf.grep(self.outcar, 'NBANDS=', 0, False, 'int', 1)  # number of bands
        self.bands_data = get_band_occupation(self.outcar, self.nkpts, self.functional, self.nbands)  # bands energy and occupation
        self.VBM, self.CBM = get_band_extrema(self.bands_data)  # VBM and CBM energies
        self.gap = self.CBM - self.VBM  # electronic gap
        if self.functional != 'G0W0@GGA' and self.functional != 'GW0@GGA':
            self.potentials = get_electrostatic_potentials(self.outcar, self.atoms)  # electrostatic averaged potentials
        else:
            self.potentials = None

        # --------------------------------------------------- OTHERS ---------------------------------------------------

        self.ID = ''.join([f + str(g) for f, g in zip(self.atoms_types, self.nb_atoms)]) + '_' + self.functional\
                  + '_q' + str(int(self.charge))
        self.title = self.display_name + ' ' + self.functional_title + ' q=%.0f' % self.charge  # title of the plot

        # --------------------------------------------------- DOSCAR ---------------------------------------------------

        if self.DOSCAR != '':
            self.doscar = bf.read_file(DOSCAR)  # content of the DOSCAR file

            # Check that the OUTCAR and DOSCAR files are consistent
            if self.lorbit == 11:
                if len(self.doscar) != 6 + sum(self.nb_atoms) * (self.nedos + 1) + self.nedos:
                    raise bf.PydefDoscarError('The DOSCAR file is inconsistent with the OUTCAR file')
            else:
                if len(self.doscar) != 6 + sum(self.nb_atoms):  # Beware of the white line at the end of the file
                    raise bf.PydefDoscarError('The DOSCAR file is inconsistent with the OUTCAR file')

            dos_data = np.transpose([[float(f) for f in q.split()] for q in self.doscar[6:self.nedos+6]])[1]
            self.dosmax = max(dos_data)  # maximum value of the total DOS

            self.dpp = Dos_Plot_Parameters(self)  # DOS plot parameters

    def plot_dos(self):
        """ Plot the DOS of the calculation according to the parameters in dpp """

        if self.doscar == '':
            raise bf.PydefDoscarError('No DOSCAR file specified')

        data = [[float(f) for f in q.split()] for q in self.doscar[6:]]  # total and projected DOS

        energy, total_dos = np.transpose(data[:self.nedos])[:2]  # Total DOS and energy

        E_F = self.fermi_energy
        E_CBM = self.CBM
        E_VBM = self.VBM

        if self.dpp.fermi_shift:
            shift = - E_F - self.dpp.input_shift
        else:
            shift = 0.0 - self.dpp.input_shift

        if self.dpp.normalise_dos is True:
            normalise = float(self.dosmax)
        else:
            normalise = 1.0

        energy += shift
        E_F += shift
        E_CBM += shift
        E_VBM += shift

        if self.dpp.display_proj_dos is True:

            # Orbitals projected DOS
            dos_op = data[self.nedos:]

            # Projected dos on every orbitals (s, px, py, pz, dxx,...) for each atom (and energy)
            dos_opa_all = [np.transpose(f) for f in [dos_op[(self.nedos + 1) * i - self.nedos:(self.nedos + 1) * i]
                                                     for i in range(1, sum(self.nb_atoms) + 1)]]

            # Projected dos on orbitals for every atom
            if len(self.orbitals) == 3:  # s p d case
                dos_opa_spdf = [[np.array(f[1]), np.sum(f[2:5], axis=0), np.sum(f[5:10], axis=0)] for f in dos_opa_all]
            elif len(self.orbitals) == 4:  # s p d f case
                dos_opa_spdf = [[np.array(f[1]), np.sum(f[2:5], axis=0), np.sum(f[5:10], axis=0), np.sum(f[10:17], axis=0)] for f in dos_opa_all]
            else:
                return None

            # Atomic species index for splitting
            ats_indices = [int(sum(self.nb_atoms[:f + 1])) for f in range(len(self.nb_atoms))][:-1]

            # Projected dos on orbitals for every atoms divided between atomic species
            dos_opa = [dos_opa_spdf[i:j] for i, j in zip([0] + ats_indices, ats_indices + [None])]

            if self.dpp.dos_type == 'OPAS':

                # Projected DOS on s, p, d orbitals for each atomic species
                if len(self.orbitals) == 3:
                    proj_dos = [[np.sum([f[0] for f in g], axis=0), np.sum([f[1] for f in g], axis=0),
                                 np.sum([f[2] for f in g], axis=0)] for g in dos_opa]
                    proj_labels = [['$' + f + '\ s$', '$' + f + '\ p$', '$' + f + '\ d$'] for f in self.atoms_types]
                elif len(self.orbitals) == 4:
                    proj_dos = [[np.sum([f[0] for f in g], axis=0), np.sum([f[1] for f in g], axis=0),
                                 np.sum([f[2] for f in g], axis=0), np.sum([f[3] for f in g], axis=0)] for g in dos_opa]
                    proj_labels = [['$' + f + '\ s$', '$' + f + '\ p$', '$' + f + '\ d$', '$' + f + '\ f$'] for f in self.atoms_types]
                else:
                    return None
                colors = self.dpp.colors_proj

                if self.dpp.tot_proj_dos is True:

                    # Total projected DOS on s, p, d orbitals for each atomic species
                    proj_dos = [np.sum(f, axis=0) for f in proj_dos]
                    proj_labels = [['$' + f + '$'] for f in self.atoms_types]
                    colors = self.dpp.colors_tot

                proj_dos_dict = dict(zip(self.atoms_types, proj_dos))
                proj_labels_dict = dict(zip(self.atoms_types, proj_labels))

                proj_dos = [proj_dos_dict[f] for f in self.dpp.choice_opas]
                proj_labels = [proj_labels_dict[f] for f in self.dpp.choice_opas]

            elif self.dpp.dos_type == 'OPA':

                # Projected DOS on s, p, d orbitals for every atoms
                proj_dos = dos_opa_spdf
                if len(self.orbitals) == 3:
                    proj_labels = [['$' + f + '\ s$', '$' + f + '\ p$', '$' + f + '\ d$'] for f in self.atoms]
                elif len(self.orbitals) == 4:
                    proj_labels = [['$' + f + '\ s$', '$' + f + '\ p$', '$' + f + '\ d$', '$' + f + '\ f$'] for f in self.atoms]
                colors = self.dpp.colors_proj

                if self.dpp.tot_proj_dos is True:

                    # Total projected DOS on s, p, d orbitals for every atoms
                    proj_dos = [np.sum(f, axis=0) for f in proj_dos]
                    proj_labels = [['$' + f + '$'] for f in self.atoms]
                    colors = self.dpp.colors_tot

                proj_dos_dict = dict(zip(self.atoms, proj_dos))
                proj_labels_dict = dict(zip(self.atoms, proj_labels))

                proj_dos = [proj_dos_dict[f] for f in self.dpp.choice_opa]
                proj_labels = [proj_labels_dict[f] for f in self.dpp.choice_opa]

        # ----------------------------------------------- PLOT PARAMETERS ----------------------------------------------

        width, height = bf.get_screen_size()
        if self.dpp.figure.name == 'New Figure':
            fig = plt.figure(figsize=(width, height-2.2))
        else:
            fig = plt.figure(self.dpp.figure.name, figsize=(width, height-2.2))

        ax = fig.add_subplot(self.dpp.figure.nb_rows, self.dpp.figure.nb_cols, self.dpp.subplot_nb)
        # Main title
        if self.dpp.figure.nb_rows == 1 and self.dpp.figure.nb_cols == 1:
            new_title = '$' + self.dpp.title.replace(' ', '\ ') + '$'
        else:
            # add a letter for labelling
            new_title = '$' + self.dpp.title.replace(' ', '\ ') + '$' + [' ' + f + ')' for f in list(string.ascii_lowercase)][self.dpp.subplot_nb - 1]

        ax.set_title(new_title, fontsize=self.dpp.text_size, fontweight='bold')

        # Axes titles
        if self.dpp.fermi_shift is True:
            xlabel = '$E-E_F\ (eV)$'
        else:
            xlabel = '$E\ (eV)$'
        ylabel = '$DOS\ (a.u.)$'

        if self.dpp.label_display is True:  # custom label display
            if self.dpp.xlabel_display is True:
                ax.set_xlabel(xlabel, fontsize=self.dpp.text_size)
            if self.dpp.ylabel_display is True:
                ax.set_ylabel(ylabel, fontsize=self.dpp.text_size)
            if self.dpp.common_ylabel_display is True:
                fig.text(0.017, 0.5, ylabel, ha='center', va='center', rotation='vertical', fontsize=self.dpp.text_size)
            if self.dpp.xticklabels_display is False:
                plt.setp(ax.get_xticklabels(), visible=False)

        else:  # automatic label display (assuming that the energy range is the same for all plots)
            if self.dpp.subplot_nb >= (self.dpp.figure.nb_rows - 1) * self.dpp.figure.nb_cols + 1:
                ax.set_xlabel(xlabel, fontsize=self.dpp.text_size)
            else:
                plt.setp(ax.get_xticklabels(), visible=False)

            if self.dpp.subplot_nb in np.array(range(self.dpp.figure.nb_rows)) * self.dpp.figure.nb_cols + 1:
                ax.set_ylabel(ylabel, fontsize=self.dpp.text_size)

        ax.yaxis.set_major_locator(tk.NullLocator())
        ax.tick_params(width=1.5, length=4, labelsize=self.dpp.text_size - 2)
        ax.set_xlim(self.dpp.E_range)
        ax.set_ylim(self.dpp.DOS_range)

        # ----------------------------------------------- PLOT & DISPLAY -----------------------------------------------

        if self.dpp.display_proj_dos is True:
            ax.stackplot(energy, np.row_stack(proj_dos)/normalise, colors=colors, linewidths=0, labels=np.concatenate(proj_labels))

        if self.dpp.display_total_dos is True:
            ax.plot(energy, total_dos/normalise, color='black', label='Total DOS')

        # Display energy levels
        if self.dpp.display_BM_levels is True:
            ax.plot([E_CBM, E_CBM], [self.dpp.DOS_range[0], self.dpp.DOS_range[1]], '--', color='red')
            ax.text(E_CBM, self.dpp.DOS_range[1] * 0.75, '$E_C$', fontsize=self.dpp.text_size - 2, color='red')
            ax.plot([E_VBM, E_VBM], [self.dpp.DOS_range[0], self.dpp.DOS_range[1]], '--', color='blue')
            ax.text(E_VBM, self.dpp.DOS_range[1] * 0.75, '$E_V$', fontsize=self.dpp.text_size - 2, color='blue')

        if self.dpp.display_Fermi_level is True:
            ax.plot([E_F, E_F], [self.dpp.DOS_range[0], self.dpp.DOS_range[1]], '--', color='black')
            ax.text(E_F, self.dpp.DOS_range[1] * 0.75, '$E_F$', fontsize=self.dpp.text_size - 2, color='black')

        # Legends
        if self.dpp.display_legends is True:
            legend = ax.legend(fontsize=self.dpp.text_size - 6, loc='upper right')
            legend.draggable()

        fig.tight_layout(rect=(0.02, 0, 1, 1))
        fig.show()



def get_functional(outcar):
    """ Retrieve the functional used from the outcar data
    :param outcar: content of the OUTCAR file (list of strings)
    :return: functional of used
    """

    # Default values
    functional = 'other'  # used for display inline
    functional_title = 'other'  # used for display in matplotlib

    lexch = bf.grep(outcar, 'LEXCH   =', 0, 'internal', 'str', 1)
    lhfcalc = bf.grep(outcar, 'LHFCALC =', 0, 'Hartree', 'str', 1)
    hfscreen = bf.grep(outcar, 'HFSCREEN=', 0, 'screening', 'float', 1)
    gw = bf.grep(outcar, 'Response functions by sum over occupied states:', nb_found=2)

    if lexch == '2' and lhfcalc == 'F':
        functional = 'LDA'
        functional_title = 'LDA'
    if lexch == '8' and lhfcalc == 'F':
        functional = 'GGA'
        functional_title = 'GGA'
    if lexch == '8' and lhfcalc == 'T':
        if hfscreen == 0.2:
            functional = 'HSE'
            functional_title = 'HSE'
        if hfscreen == 0.0:
            functional = 'PBE0'
            functional_title = 'PBE0'
    if gw is not None:
        nelm = bf.grep(outcar, 'NELM    =', 0, 'number', 'int', 1)
        if nelm == 1:
            functional = 'G0W0@GGA'
            functional_title = 'G_0W_0@GGA'
        elif nelm > 1:
            functional = 'GW0@GGA'
            functional_title = 'GW_0@GGA'

    return functional, functional_title


def get_cell_parameters(outcar):
    """
    :param outcar: content of the outcar file (list of strings)
    :return: cristallographic parameters of the cell
    """
    index = bf.grep(outcar, 'direct lattice vectors')[0][1]  # location of the cristallographic parameters in the OUTCAR
    return [[float(f) for f in g.split()[:3]] for g in outcar[index + 1:index + 4]]


def get_atoms_positions(outcar, atoms):
    """
    :param outcar: content of the outcar file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers)
    :return: position of each atom as a dictionary
    """

    index_beg = bf.grep(outcar, 'position of ions in cartesian coordinates  (Angst):', nb_found=1)[0][1] + 1  # index of the first atom position
    index_end = [f[1] for f in bf.grep(outcar, '---------') if f[1] > index_beg][0] - 3  # index of the last atom position
    atoms_positions = [[float(f) for f in g.split()] for g in outcar[index_beg:index_end]]

    # Check that the number of positions retrieved is equal to the number of atoms
    if len(atoms_positions) != len(atoms):
        raise bf.PydefImportError("The number of atoms positions is not consistent with the total number of atoms")
    else:
        return dict(zip(atoms, atoms_positions))


def get_band_occupation(outcar, nkpts, functional, nbands):
    """
    :param outcar: content of the outcar file (list of strings)
    :param nkpts: number of kpoints (int)
    :param functional: functional used (string)
    :param nbands: number of bands (int)
    :return: last energy and occupation of the bands for each kpoint
    """

    kpoints_indices = [f[1] for f in bf.grep(outcar, 'k-point ')[- nkpts:]]  # last k-points occupation calculated

    if functional != 'G0W0@GGA' and functional != 'GW0@GGA':
        nb_bands = [[g for f, g in zip(outcar, range(len(outcar))) if (f == '') & (g > h)][0]
                    for h in kpoints_indices][0] - kpoints_indices[0] - 2  # number of bands

        # check that the number of bands found is consistence with the number if bands retrieved previously
        if nb_bands != nbands:
            raise bf.PydefImportError('The number of bands retrieved from the kpoints is not consistent')

        bands_str = [outcar[f + 2:f + nb_bands + 2] for f in kpoints_indices]  # band occupation for each k-points as strings
        col_index = 1  # index of the column containing the energy

    else:
        nb_bands = [[g for f, g in zip(outcar, range(len(outcar))) if (f == '') & (g > h)][0]
                    for h in kpoints_indices][1] - kpoints_indices[0] - 6  # number of bands

        bands_str = [outcar[f + 3:f + 3 + nb_bands] for f in kpoints_indices]  # band occupation for each k-points as strings
        col_index = 2  # index of the column containing the energy

    bands_data = [np.transpose([[float(s) for s in f.split()] for f in q]) for q in bands_str]  # band occupation for each k-points
    return [[f[col_index], f[-1]] for f in bands_data]  # return energy and occupation for each k-point


def get_band_extrema(bands_data):
    """
    :param bands_data: bands occupation and energy for all k-points (list of list of numpy array)
    :return: Valence band maximum and Conduction band minimum
    """

    VBM_indices = [np.where(f[1] != 0)[0][-1] for f in bands_data]  # index where the band occupation is different than zero
    VBM_energy = max([f[0][g] for f, g in zip(bands_data, VBM_indices)])  # last band occupied with the maximum energy
    CBM_energy = min([f[0][g + 1] for f, g in zip(bands_data, VBM_indices)])  # first band non occcupied with the lowest energy

    return VBM_energy, CBM_energy


def get_system_name(atoms_types, nb_atoms, reduced):
    """
    :param atoms_types: atomic species in the system (list of strings)
    :param nb_atoms: population of each atomic species (list of integers)
    :param reduced: if True, then tries to reduce the name of the system. Ex: Cd8In16S32 --> CdIn2S4
    :return: name of the system studied
    """
    if len(atoms_types) > 1:
        if reduced is True:
            common_factor = bf.get_gcd(nb_atoms)  # common factor between atomic population
            nb_atoms = [f/common_factor for f in nb_atoms]
    else:
        nb_atoms = [1]

    name = ''
    name_display = ''  # name for display in matplotlib

    for f, g in zip(nb_atoms, atoms_types):
        if f != 1:
            name += g + str(f)
            name_display += g + '_{' + str(f) + '}'
        else:
            name += g
            name_display += g

    return name, name_display


def get_electrostatic_potentials(outcar, atoms):
    """
    :param outcar: content of the OUTCAR file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers)
    :return: electrostatic averaged potentials
    """

    index_potentials = bf.grep(outcar, 'average (electrostatic) potential at core', nb_found=1)[0][1]  # index where the potentials are
    index_potentials_end = [g for f, g in zip(outcar, range(len(outcar)))
                            if (f == ' ') & (g > index_potentials)][0]  # first blank line after the potentials

    potentials_str = outcar[index_potentials + 3:index_potentials_end]  # all of potentials as strings
    potentials_atom_nb = np.concatenate([[float(f) for f in re.split('     |-', q)[1:]]
                                         for q in potentials_str])  # All potentials and corresponding atom
    potentials = [-f[1] for f in np.split(potentials_atom_nb, len(atoms))]

    if len(potentials) != len(atoms):
        raise bf.PydefImportError('Number of electrostatic potentials retrieved and number are not consistent')
    return dict(zip(list(atoms), potentials))


def get_kpoints_weight(outcar, nkpts):
    """
    :param outcar: content of the OUTCAR file (list of strings)
    :param nkpts: number of kpoints (int)
    :return:
    """

    index_weight = bf.grep(outcar, 'k-points in reciprocal lattice and weights', nb_found=1)[0][1]
    index_weight_end = [g for f, g in zip(outcar, range(len(outcar))) if (f == ' ') & (g > index_weight)][0]

    kpoints_weights_str = outcar[index_weight + 1:index_weight_end]
    kpoints_weights = np.transpose([[float(f) for f in q.split()] for q in kpoints_weights_str])[-1]

    if len(kpoints_weights) != nkpts:
        raise bf.PydefImportError('Number of kpoint weights retrieved and number of kpoints are not consistent')
    else:
        return kpoints_weights


class Dos_Plot_Parameters:
    """ Parameters for plotting the DOS of a Cell object
    """

    def __init__(self, aCell):
        """
        :param aCell: Cell object
        """

        # Plot parameters
        self.display_proj_dos = True  # if True, display the projected DOS
        self.dos_type = 'OPAS'  # type of DOS plotted ('OPA' : s,p,d orbitals projected DOS for each atom or 'OPAS' : s,p,d orbitals projected DOS for each atomic species)
        self.tot_proj_dos = False  # if True, then the total projected DOS is plotted (according to 'dos_type')
        self.choice_opas = aCell.atoms_types  # list of atomic species
        self.choice_opa = aCell.atoms  # list of atoms
        self.E_range = np.sort([aCell.emin, aCell.emax])  # energy range (list of float)
        self.DOS_range = [0, aCell.dosmax]  # DOS range (list of float)
        if len(aCell.orbitals) == 4:  # s p d f orbitals
            self.colors_proj = ['#990000', '#e60000', '#ff6666', '#ff66cc',
                                '#003399', '#0000e6', '#9999ff', '#cc66ff'
                                '#00802b', '#00b33c', '#1aff66', '#99ff99'
                                '#999900', '#e6e600', '#ffff33', '#ffff99']  # list of colors for orbital projected plots
        else:
            self.colors_proj = ['#990000', '#e60000', '#ff6666',
                                '#003399', '#0000e6', '#9999ff',
                                '#00802b', '#00b33c', '#1aff66',
                                '#999900', '#e6e600', '#ffff33']  # list of colors for orbital projected plots
        self.colors_tot = ['#ff0000', '#0033cc', '#33cc33', '#e6e600']  # list of colors for total projected plots
        self.fermi_shift = False  # if True, then the zero of energy is the fermi level
        self.normalise_dos = False   # if True, normalise the DOS
        self.display_total_dos = False  # if True, display the total DOS
        self.display_BM_levels = False  # if True, display the band maxima levels
        self.display_Fermi_level = True  # if True, display the fermi levels
        self.input_shift = 0.0

        # Figure and axis parameters
        self.figure = fc.Figure(1, 1, 'New Figure')  # figure object
        self.subplot_nb = 1  # subplot number
        self.text_size = 24  # size of the text displayed
        self.title = aCell.title  # Title of the plot
        self.label_display = False  # if True, the xlabel and ylabel display depend on 'xlabel_display' and 'ylabel_display'. Else, the xlabel and ylabel are smartly displayed
        self.xlabel_display = True  # if True, the xlabel is displayed
        self.ylabel_display = True  # if True, the ylabel is displayed
        self.common_ylabel_display = False  # if True, a common ylabel is displayed in the middle of the left side
        self.xticklabels_display = True  # if True, display the tick labels of the x-axis
        # self.yticks_display = False  # if True, display the ticks of the y-axis
        # self.yticklabels_display = False  # if True, display the tick labels of the y-axis
        self.display_legends = True  # if True, display the legends


def normalise_composition(cell1, cell2):
    """ Normalise the population of two Cell objects """

    for key in cell1.population.keys():
        if key not in cell2.population.keys():
            cell2.population[key] = 0

    for key in cell2.population.keys():
        if key not in cell1.population.keys():
            cell1.population[key] = 0
