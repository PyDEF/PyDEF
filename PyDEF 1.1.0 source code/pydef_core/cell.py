"""
    Module used to import results of VASP calculations in PyDEF
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import matplotlib; matplotlib.use('TkAgg')  # (to avoid "terminating with uncaught exception of type NSException" error)
# noinspection PyUnresolvedReferences
import matplotlib.backends.backend_tkagg  # (for compilation)
import numpy as np
import matplotlib.pyplot as plt
import re
import copy
import pydef_core.figure as pf
import pydef_core.basic_functions as bf
# plt.rcParams.update({'mathtext.default': 'regular'})


class Cell:
    """ Object containing various data on a VASP calculation """

    def __init__(self, outcar_file, doscar_file):
        """ Read the OUTCAR and DOSCAR output files of a VASP calculation
        :param outcar_file: location of the OUTCAR file (string)
        :param doscar_file: location of the DOSCAR file (string) """

        # --------------------------------------------------- OUTCAR ---------------------------------------------------

        self.OUTCAR = outcar_file
        self.DOSCAR = doscar_file

        self.outcar = bf.read_file(outcar_file)  # content of the OUTCAR file

        if self.outcar[0][:6] != ' vasp.':
            raise bf.PydefOutcarError('The given file appears to not be a valid OUTCAR file.')

        # ------------------------------------------- CALCULATION PROPERTIES -------------------------------------------

        self.functional, self.functional_title = get_functional(self.outcar)  # functional used
        self.nedos =  bf.grep(self.outcar, 'NEDOS =',  0, 'number of ions',  'int',   1)  # number of point in the DOS
        self.encut =  bf.grep(self.outcar, 'ENCUT  =', 0, 'eV',              'float', 1)  # ENCUT used
        self.ediff =  bf.grep(self.outcar, 'EDIFF  =', 0, 'stopping',        'float', 1)  # EDIFF value
        self.emin =   bf.grep(self.outcar, 'EMIN   =', 0, ';',               'float', 1)  # minimum energy for the DOS
        self.emax =   bf.grep(self.outcar, 'EMAX   =', 0, 'energy-range',    'float', 1)  # maximum energy for the DOS
        self.ismear = bf.grep(self.outcar, 'ISMEAR =', 0, ';',               'int',   1)  # ISMEAR tag
        self.lorbit = bf.grep(self.outcar, 'LORBIT =', 0, '0 simple, 1 ext', 'int',   1)  # LORBIT tag
        self.isym =   bf.grep(self.outcar, 'ISYM   =', 0, '0-nonsym',        'int',   1)  # ISYM tag
        self.istart = bf.grep(self.outcar, 'ISTART =', 0, 'job',             'int',   1)  # ISTART tag
        self.ispin =  bf.grep(self.outcar, 'ISPIN  =', 0, 'spin',            'int',   1)  # ISPIN tag
        self.icharg = bf.grep(self.outcar, 'ICHARG =', 0, 'charge:',         'int',   1)  # ICHARG tag

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
        self.kpoints_coords, self.kpoints_weights = get_kpoints_weights_and_coords(self.outcar, self.nkpts)
        self.kpoints_coords_r = get_kpoints_reciprocal_coords(self.outcar, self.nkpts)
        self.nbands = bf.grep(self.outcar, 'NBANDS=', 0, False, 'int', 1)  # number of bands
        self.bands_data = get_band_occupation(self.outcar, self.nkpts, self.functional)  # bands energy and occupation
        self.VBM, self.CBM = get_band_extrema(self.bands_data)  # VBM and CBM energies
        self.gap = self.CBM - self.VBM  # electronic gap
        if self.functional != 'G0W0@GGA' and self.functional != 'GW0@GGA':
            self.potentials = get_electrostatic_potentials(self.outcar, self.atoms)  # electrostatic averaged potentials
        else:
            self.potentials = None

        # --------------------------------------------------- OTHERS ---------------------------------------------------

        self.ID = ''.join([f + str(g) for f, g in zip(self.atoms_types, self.nb_atoms)]) + '_' + self.functional\
                  + '_q' + str(int(self.charge))
        self.title = self.display_name + ' ' + self.functional_title + ' q=%.0f' % self.charge  # title of the

        # --------------------------------------------------- DOSCAR ---------------------------------------------------

        if self.DOSCAR != '':
            self.doscar = bf.read_file(doscar_file)  # content of the DOSCAR file

            self.dos_energy, self.total_dos, self.total_dos_up, self.total_dos_down, self.dos_opa, self.dos_opa_up, \
            self.dos_opa_down, self.dos_opas, self.dos_opas_up, self.dos_opas_down = self.analyse_dos()

            # Maximum value of each DOS excluding the first value
            self.dosmax = np.max(self.total_dos[1:])
            if self.ispin == 2:
                self.dosmax_up = np.max(self.total_dos_up[1:])
                self.dosmax_down = np.max(self.total_dos_down[1:])

            self.dpp = DosPlotParameters(self)  # DOS plot parameters

        if self.icharg == 11:
            self.bpp = BandDiagramPlotParameters(self)

    def analyse_dos(self):
        """ Analyse the DOSCAR file and return the DOS according to the parameters of dpp """

        # Check that the OUTCAR and DOSCAR files are consistent
        if self.lorbit == 11:
            if len(self.doscar) != 6 + sum(self.nb_atoms) * (self.nedos + 1) + self.nedos:
                raise bf.PydefDoscarError('The DOSCAR file is inconsistent with the OUTCAR file')
        else:
            if len(self.doscar) != 6 + sum(self.nb_atoms):  # Beware of the white line at the end of the file
                raise bf.PydefDoscarError('The DOSCAR file is inconsistent with the OUTCAR file')

        raw_data = self.doscar[6:]  # total and projected DOS

        # -------------------------------------------- ENERGY AND TOTAL DOS --------------------------------------------

        tot_dos_data = bf.convert_stringcolumn_to_array(raw_data[:self.nedos])

        if self.ispin == 2.:
            energy, total_dos_up, total_dos_down = tot_dos_data[:3]  # Total DOS and energy
            total_dos = total_dos_up + total_dos_down
        elif self.ispin == 1:
            energy, total_dos = tot_dos_data[:2]  # Total DOS and energy
            total_dos_up = None
            total_dos_down = None
        else:
            return None

        # ------------------------------------------ PROJECTED DOS PROCESSING ------------------------------------------

        if self.lorbit == 11:

            # Orbitals projected DOS
            dos_op_raw = raw_data[self.nedos:]

            # Remove useless lines from the projected DOS
            for i in range(sum(self.nb_atoms) - 1, -1, -1):
                del dos_op_raw[(self.nedos + 1) * i]

            # DOS projected on every orbitals (s, px, py, pz, dxx, ...)
            dos_op_xyz = bf.convert_stringcolumn_to_array(dos_op_raw)[1:]
            if self.ispin == 2.:
                dos_op_up_xyz = dos_op_xyz[::2]
                dos_op_down_xyz = dos_op_xyz[1:][::2]
            else:
                dos_op_up_xyz = None
                dos_op_down_xyz = None

            # DOS projected on each main orbital (s, p, d...)
            if len(self.orbitals) == 3:  # s p d case
                orbitals_size = np.array([1, 3, 5])
            elif len(self.orbitals) == 4:  # s p d f case
                orbitals_size = np.array([1, 3, 5, 7])
            else:
                return None

            if self.ispin == 1.:
                dos_op = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_xyz, orbitals_size)]
                dos_op_up = None
                dos_op_down = None
            elif self.ispin == 2.:
                dos_op = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_xyz, orbitals_size*2)]
                dos_op_up = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_up_xyz, orbitals_size)]
                dos_op_down = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_down_xyz, orbitals_size)]
            else:
                return None

            # DOS projected on every main orbital (s, p, d...) for each atom
            dos_opa = [np.transpose(f) for f in np.split(np.transpose(dos_op), self.nb_atoms_tot)]
            if self.ispin == 2.:
                dos_opa_up = [np.transpose(f) for f in np.split(np.transpose(dos_op_up), self.nb_atoms_tot)]
                dos_opa_down = [np.transpose(f) for f in np.split(np.transpose(dos_op_down), self.nb_atoms_tot)]
            else:
                dos_opa_up = None
                dos_opa_down = None

            # Projected DOS on each atomic species
            dos_opas = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa, self.nb_atoms)]
            if self.ispin == 2.:
                dos_opas_up = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa_up, self.nb_atoms)]
                dos_opas_down = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa_down, self.nb_atoms)]
            else:
                dos_opas_up = None
                dos_opas_down = None

            return energy, total_dos, total_dos_up, total_dos_down, dos_opa, dos_opa_up, dos_opa_down, \
                   dos_opas, dos_opas_up, dos_opas_down

    def plot_dos(self):
        """ Plot the DOS of the calculation according to the parameters in dpp """

        if self.DOSCAR == '':
            raise bf.PydefDoscarError('No DOSCAR file specified')

        spin_cond = self.ispin == 2 and self.dpp.display_spin is True
        fsize = self.dpp.text_size  # test size

        # --------------------------------------------------- ENERGY ---------------------------------------------------

        energy = copy.deepcopy(self.dos_energy)
        fermi_energy = self.fermi_energy
        cbm_energy = self.CBM
        vbm_energy = self.VBM

        if self.dpp.fermi_shift is True:
            shift = - fermi_energy - self.dpp.input_shift
        else:
            shift = - self.dpp.input_shift

        energy += shift
        fermi_energy += shift
        cbm_energy += shift
        vbm_energy += shift

        # ----------------------------------------------- DOS PROCESSING -----------------------------------------------

        total_dos = copy.deepcopy(self.total_dos)
        total_dos_up = copy.deepcopy(self.total_dos_up)
        total_dos_down = copy.deepcopy(self.total_dos_down)

        dos_opas = copy.deepcopy(self.dos_opas)
        dos_opas_up = copy.deepcopy(self.dos_opas_up)
        dos_opas_down = copy.deepcopy(self.dos_opas_down)

        dos_opa = copy.deepcopy(self.dos_opa)
        dos_opa_up = copy.deepcopy(self.dos_opa_up)
        dos_opa_down = copy.deepcopy(self.dos_opa_down)

        if self.dpp.dos_type == 'OPAS':

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms_types]
            colors = copy.deepcopy(self.dpp.colors_proj)

            # Total projected DOS for each atomic species
            if self.dpp.tot_proj_dos is True:
                dos_opas = [np.sum(f, axis=0) for f in dos_opas]
                if spin_cond is True:
                    dos_opas_up = [np.sum(f, axis=0) for f in dos_opas_up]
                    dos_opas_down = [np.sum(f, axis=0) for f in dos_opas_down]

                p_labels = [['$' + f + '$'] for f in self.atoms_types]
                colors = copy.deepcopy(self.dpp.colors_tot)

            # Atomic species selection
            p_labels = np.concatenate(bf.choose_in(self.atoms_types, p_labels, self.dpp.choice_opas))
            p_dos = np.row_stack(bf.choose_in(self.atoms_types, dos_opas, self.dpp.choice_opas))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_up, self.dpp.choice_opas))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_down, self.dpp.choice_opas))
            else:
                p_dos_up = None
                p_dos_down = None

        elif self.dpp.dos_type == 'OPA':

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms]
            colors = copy.deepcopy(self.dpp.colors_proj)

            # Total projected DOS on s, p, d orbitals for every atoms
            if self.dpp.tot_proj_dos is True:
                dos_opa = [np.sum(f, axis=0) for f in dos_opa]
                if spin_cond is True:
                    dos_opa_up = [np.sum(f, axis=0) for f in dos_opa_up]
                    dos_opa_down = [np.sum(f, axis=0) for f in dos_opa_down]

                p_labels = [['$' + f + '$'] for f in self.atoms]
                colors = copy.deepcopy(self.dpp.colors_tot)

            # Atoms selection
            p_labels = np.concatenate(bf.choose_in(self.atoms, p_labels, self.dpp.choice_opa))
            p_dos = np.row_stack(bf.choose_in(self.atoms, dos_opa, self.dpp.choice_opa))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms, dos_opa_up, self.dpp.choice_opa))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms, dos_opa_down, self.dpp.choice_opa))
            else:
                p_dos_up = None
                p_dos_down = None

        else:
            p_dos = None
            p_dos_up = None
            p_dos_down = None
            colors = None
            p_labels = None

        # ---------------------------------------------- PLOT PARAMETERS -----------------------------------------------

        fig = pf.new_figure(self.dpp.figure.name)
        ax = fig.add_subplot(self.dpp.figure.nb_rows, self.dpp.figure.nb_cols, self.dpp.subplot_nb)

        title = pf.convert_string_to_pymath(self.dpp.title)
        title += pf.subplot_title_indexing(self.dpp.subplot_nb, self.dpp.figure.nb_cols, self.dpp.figure.nb_rows)
        ax.set_title(title, fontsize=fsize, fontweight='bold')

        # X axis label
        if self.dpp.fermi_shift is True:
            xlabel = '$E-E_F$ ($eV$)'
        else:
            xlabel = '$E$ ($eV$)'

        # Y axis label
        if self.dpp.label_display is False or self.dpp.yticks_display is True:
            ylabel = 'DOS ($states/eV$)'
        else:
            ylabel = 'DOS ($a.u.$)'

        # Axis label display
        is_last_row = self.dpp.subplot_nb >= (self.dpp.figure.nb_rows - 1) * self.dpp.figure.nb_cols + 1
        is_first_col = self.dpp.subplot_nb in np.array(range(self.dpp.figure.nb_rows)) * self.dpp.figure.nb_cols + 1

        if self.dpp.label_display is True:
            # X-axis
            if self.dpp.xlabel_display is True:
                ax.set_xlabel(xlabel, fontsize=fsize)
            if self.dpp.xticklabels_display is False:
                plt.setp(ax.get_xticklabels(), visible=False)

            # Y-axis
            if self.dpp.ylabel_display is True:
                ax.set_ylabel(ylabel, fontsize=fsize)
            if self.dpp.yticks_display is False:
                ax.set_yticks([])
            if self.dpp.common_ylabel_display is True:
                fig.text(0.017, 0.5, ylabel, ha='center', va='center', rotation='vertical', fontsize=fsize)

        # Automatic labelling
        else:
            # X-axis
            if is_last_row is True:
                ax.set_xlabel(xlabel, fontsize=fsize)

            # Y-axis
            if is_first_col is True:
                ax.set_ylabel(ylabel, fontsize=fsize)

        ax.tick_params(width=1.5, length=4, labelsize=fsize - 2)
        ax.set_xlim(self.dpp.E_range)
        ax.set_ylim(self.dpp.DOS_range)

        # ---------------------------------------------------- PLOT ----------------------------------------------------

        # Total DOS
        if self.dpp.display_total_dos is True:
            if spin_cond is True:
                ax.plot(energy, total_dos_up, color='black', label='Total DOS', lw=2)
                ax.plot(energy, -total_dos_down, color='black', lw=2)
            else:
                ax.plot(energy, total_dos, color='black', label='Total DOS', lw=2)

        # Projected DOS
        if self.dpp.display_proj_dos is True:
            if self.dpp.plot_areas is True:
                if spin_cond is True:
                    ax.stackplot(energy, p_dos_up, colors=colors, lw=0, labels=p_labels)
                    ax.stackplot(energy, -p_dos_down, colors=colors, lw=0)
                else:
                    ax.stackplot(energy, p_dos, colors=colors, lw=0, labels=p_labels)
            else:
                if spin_cond is True:
                    [ax.plot(energy, f, c=g, label=h, lw=2) for f, g, h in zip(p_dos_up, colors, p_labels)]
                    [ax.plot(energy, -f, c=g, lw=2) for f, g in zip(p_dos_down, colors)]
                else:
                    [ax.plot(energy, f, c=g, label=h, lw=2) for f, g, h in zip(p_dos, colors, p_labels)]

        # Legend
        if self.dpp.display_legends is True:
            legend = ax.legend(fontsize=fsize - 6, loc='best', fancybox=True)
            legend.draggable()

        fig.tight_layout(rect=(0.02, 0, 1, 1))

        # Annotations
        self.annotate_dos(ax, cbm_energy, vbm_energy, fermi_energy, spin_cond, fsize)

        def update_plot():
            self.delete_annotations()
            self.annotate_dos(ax, cbm_energy, vbm_energy, fermi_energy, spin_cond, fsize)

        ax.callbacks.connect('xlim_changed', lambda x: update_plot())
        ax.callbacks.connect('ylim_changed', lambda x: update_plot())

        fig.show()

    # noinspection PyAttributeOutsideInit
    def annotate_dos(self, ax, cbm_energy, vbm_energy, fermi_energy, spin_cond, fsize):
        """ Annotate the plot """

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Display energy levels
        if self.dpp.display_BM_levels is True:
            self.cb_line, = ax.plot([cbm_energy, cbm_energy], ylim, '--', color='red')
            self.cb_anot = ax.annotate('$E_C$', xy=(cbm_energy, ylim[1] * 0.75), fontsize=fsize - 2, color='red')
            self.cb_anot.draggable()

            self.vb_line, = ax.plot([vbm_energy, vbm_energy], ylim, '--', color='blue')
            self.vb_anot = ax.annotate('$E_V$', xy=(vbm_energy, ylim[1] * 0.75), fontsize=fsize - 2, color='blue')
            self.vb_anot.draggable()
        else:
            self.cb_line = None; self.cb_anot = None; self.vb_line = None; self.vb_anot = None

        # Display fermi level
        if self.dpp.display_Fermi_level is True:
            self.fermi_line, = ax.plot([fermi_energy, fermi_energy], ylim, '--', color='black')
            self.fermi_anot = ax.annotate('$E_F$', xy=(fermi_energy, ylim[1] * 0.75), fontsize=fsize - 2, color='black')
            self.fermi_anot.draggable()
        else:
            self.fermi_line = None; self.fermi_anot = None

        # Display axis in case of spin computation
        if spin_cond is True:
            self.xline = ax.annotate('', xy=(xlim[1], 0), xytext=(xlim[0], 0), arrowprops=dict(facecolor='k', width=1.3))
            if ylim[1] > 0.:
                self.ylinep = ax.annotate('', xy=(xlim[0], ylim[1]), xytext=(xlim[0], ylim[0]),
                                          arrowprops=dict(facecolor='k', width=2))
                self.spin_up_anot = ax.annotate('Spin up', xy=(0, 1.02), xycoords='axes fraction',
                                                ha='center', va='center', fontsize=fsize)
                self.spin_up_anot.draggable()
            else:
                self.ylinep = None; self.spin_up_anot = None

            if ylim[0] < 0.:
                self.ylinem = ax.annotate('', xy=(xlim[0], ylim[0]), xytext=(xlim[0], ylim[1]),
                                          arrowprops=dict(facecolor='k', width=2))
                self.spin_down_anot = ax.annotate('Spin down', xy=(0, -0.02), xycoords='axes fraction',
                                                  ha='center', va='center', fontsize=fsize)
                self.spin_down_anot.draggable()
            else:
                self.ylinem = None; self.spin_down_anot = None

            ax.set_yticklabels([str(abs(x)) for x in ax.get_yticks()])  # display the absolute values of the y-axis
        else:
            self.xline = None; self.ylinep = None; self.ylinem = None

    def delete_annotations(self):
        """ Delete all the annotations on the plot """

        elements = ('cb_line', 'cb_anot', 'vb_line', 'vb_anot', 'fermi_line', 'fermi_anot', 'xline', 'ylinep', 'ylinem',
                    'spin_down_anot', 'spin_up_anot')

        for element in elements:
            try:
                getattr(self, element).remove()
            except AttributeError:
                pass

    def plot_band_diagram(self):

        if self.icharg != 11:
            raise bf.PydefIchargError("ICHARG tag should be 11")

        bands_energies = np.transpose([f[0] for f in self.bands_data])  # energies of each band at each kpoint
        vbm_energy = self.VBM

        if self.bpp.vbm_shift is True:
            bands_energies -= self.VBM
            vbm_energy = 0.0

        if self.bpp.highlight_vbm_cbm is True:
            max_bands = [max(f) for f in bands_energies]
            vbm_index = np.where(np.array(max_bands) == vbm_energy)[0][0]
            vbm_band_energy = bands_energies[vbm_index]
            cbm_band_energy = bands_energies[vbm_index+1]
        else:
            vbm_band_energy = None
            cbm_band_energy = None

        x_values_temp = [bf.distance(f, g) for f, g in zip(self.kpoints_coords_r[:-1], self.kpoints_coords_r[1:])]
        x_values = np.cumsum([0] + x_values_temp)
        if self.ispin == 2:
            x_values = np.append(x_values, x_values)

        # ---------------------------------------------- PLOT PARAMETERS -----------------------------------------------

        fsize = self.bpp.text_size
        fig = pf.new_figure(self.bpp.figure.name)
        ax = fig.add_subplot(self.bpp.figure.nb_rows, self.bpp.figure.nb_cols, self.bpp.subplot_nb)

        title = pf.convert_string_to_pymath(self.bpp.title)
        title += pf.subplot_title_indexing(self.bpp.subplot_nb, self.bpp.figure.nb_cols, self.bpp.figure.nb_rows)
        ax.set_title(title, fontsize=fsize, fontweight='bold')

        ax.set_ylabel('Energy ($eV$)', fontsize=fsize)
        ax.tick_params(width=1.5, length=4, labelsize=fsize - 2)
        ax.set_xlim(0, np.max(x_values))
        ax.set_ylim(self.bpp.energy_range)

        if self.bpp.hs_kpoints_names != ['']:

            nb_hs_kpoints = len(self.bpp.hs_kpoints_names)
            ax.set_xticks([f[0] for f in np.split(x_values, nb_hs_kpoints-1)] + [x_values[-1]])
            ax.set_xticklabels(['$' + f + '$' for f in self.bpp.hs_kpoints_names])

        # ---------------------------------------------------- PLOT ----------------------------------------------------

        for energy in bands_energies:
            ax.plot(x_values, energy, c='k')

        if self.bpp.highlight_vbm_cbm is True:
            ax.plot(x_values, vbm_band_energy, c='blue', label='VBM')
            ax.plot(x_values, cbm_band_energy, c='red', label='CBM')

        ax.grid('on')
        try:
            ax.legend(loc='best', fancybox=True, fontsize=20).draggable()
        except AttributeError:
            pass

        fig.tight_layout()
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
    """ Retrieve the cell parameters from the OUTCAR file content
    :param outcar: content of the outcar file (list of strings, each one for a line)
    :return: cristallographic parameters of the cell
    """
    index = bf.grep(outcar, 'direct lattice vectors')[-1][1]  # location of the cristallographic parameters in the OUTCAR
    raw_data = outcar[index + 1:index + 4]  # direct and reciprocal lattice vectors
    return [[float(f) for f in g.split()[:3]] for g in raw_data]


def get_atoms_positions(outcar, atoms):
    """
    :param outcar: content of the outcar file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers)
    :return: position of each atom as a dictionary
    """

    str_beg = 'position of ions in cartesian coordinates  (Angst):'
    index_beg = bf.grep(outcar, str_beg, nb_found=1)[0][1] + 1  # index of the first atom position
    index_end = outcar[index_beg:].index('') - 1
    atoms_positions = [[float(f) for f in g.split()] for g in outcar[index_beg: index_end+index_beg]]

    # Check that the number of positions retrieved is equal to the number of atoms
    if len(atoms_positions) != len(atoms):
        raise bf.PydefImportError("The number of atoms positions is not consistent with the total number of atoms")
    else:
        return dict(zip(atoms, atoms_positions))


def get_band_occupation(outcar, nkpts, functional):
    """ Retrieve the bands occupation for each kpoint
    :param outcar: content of the outcar file (list of strings)
    :param nkpts: number of kpoints (int)
    :param functional: functional used (string)
    :return: last energy and occupation of the bands for each kpoint
    """

    if functional == 'GW0@GGA':
        str_beg = "  band No. old QP-enery  QP-energies   sigma(KS)   T+V_ion+V_H  V^pw_x(r,r')   Z            occupation"
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)])[-nkpts:] + 2
        col_index = 2
    elif functional == 'G0W0@GGA':
        str_beg = "  band No.  KS-energies  QP-energies   sigma(KS)   V_xc(KS)     V^pw_x(r,r')   Z            occupation"
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)]) + 2
        col_index = 2
    else:
        str_beg = '  band No.  band energies     occupation'
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)]) + 1
        col_index = 1

    indices_end = np.array([outcar[f:].index('') for f in indices_beg])
    raw_data = [outcar[f: g] for f, g in zip(indices_beg, indices_end + indices_beg)]
    data = [bf.convert_stringcolumn_to_array(f) for f in raw_data]

    return [[f[col_index], f[-1]] for f in data]


def get_band_extrema(bands_data):
    """ Retrieve the VBM and CBM energies from bands data
    :param bands_data: bands occupation and energy for all k-points (list of list of numpy array with first element is
    energy and second is band occupation)
    :return: Valence band maximum and Conduction band minimum
    """

    vbm_indices = [np.where(f[1] != 0)[0][-1] for f in bands_data]  # index where the band occupation is different than zero
    vbm_energy = max([f[0][g] for f, g in zip(bands_data, vbm_indices)])  # last band occupied with the maximum energy
    cbm_energy = min([f[0][g + 1] for f, g in zip(bands_data, vbm_indices)])  # first band non occcupied with the lowest energy

    return vbm_energy, cbm_energy


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
    """ Retrieve the electrostatic averaged potentials from the OUTCAR file
    :param outcar: content of the OUTCAR file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers)
    :return: dictionary with the electrostatic potential for each atom """

    index_beg = bf.grep(outcar, 'average (electrostatic) potential at core', nb_found=1)[0][1] + 3
    index_end = outcar[index_beg:].index(' ')

    potentials_str = outcar[index_beg: index_beg + index_end]
    potentials_raw = np.concatenate([[float(f) for f in re.split('     |-', q)[1:]] for q in potentials_str])
    potentials = np.array([-f[1] for f in np.split(potentials_raw, len(atoms))])

    if len(potentials) != len(atoms):
        raise bf.PydefImportError('Number of electrostatic potentials retrieved and number are not consistent')

    return dict(zip(list(atoms), potentials))


def get_kpoints_weights_and_coords(outcar, nkpts):
    """ Retrieve the kpoints weights from the OUTCAR file content
    :param outcar: content of the OUTCAR file (list of strings)
    :param nkpts: number of kpoints (int)
    :return: numpy array """

    index_beg = bf.grep(outcar, 'k-points in reciprocal lattice and weights', nb_found=1)[0][1] + 1
    index_end = outcar[index_beg:].index(' ')

    data_str = outcar[index_beg: index_beg+index_end]
    x, y, z, weights = bf.convert_stringcolumn_to_array(data_str)
    coordinates = [[f, g, h] for f, g, h in zip(x, y, z)]

    if len(weights) != nkpts:
        raise bf.PydefImportError('Number of kpoint weights retrieved and number of kpoints are not consistent')
    else:
        return coordinates, weights


def get_kpoints_reciprocal_coords(outcar, nkpts):

    index_beg = bf.grep(outcar, ' k-points in units of 2pi/SCALE and weight:', nb_found=1)[0][1] + 1
    index_end = outcar[index_beg:].index(' ')

    data_str = outcar[index_beg: index_beg+index_end]
    coordinates = np.transpose(bf.convert_stringcolumn_to_array(data_str)[:3])

    if len(coordinates) != nkpts:
        raise bf.PydefImportError('Number of kpoint coordinates in reciprocal space retrieved '
                                  'and number of kpoints are not consistent')
    else:
        return coordinates


class DosPlotParameters:
    """ Parameters for plotting the DOS of a Cell object """

    def __init__(self, cell):
        """
        :param cell: Cell object
        """

        # Plot parameters
        self.display_proj_dos = True  # if True, display the projected DOS
        self.dos_type = 'OPAS'  # type of DOS plotted ('OPA' : s,p,d orbitals projected DOS for each atom or 'OPAS' : s,p,d orbitals projected DOS for each atomic species)
        self.tot_proj_dos = False  # if True, then the total projected DOS is plotted (according to 'dos_type')
        self.choice_opas = cell.atoms_types  # list of atomic species
        self.choice_opa = cell.atoms  # list of atoms
        self.E_range = np.sort([cell.emin, cell.emax])  # energy range (list of float)
        if cell.ispin == 2:
            self.DOS_range = [-cell.dosmax_down, cell.dosmax_up]  # DOS range (list of float)
        else:
            self.DOS_range = [0, cell.dosmax]
        if len(cell.orbitals) == 4:  # s p d f orbitals
            self.colors_proj = ['#990000', '#e60000', '#ff6666', '#ff66cc',
                                '#003399', '#0000e6', '#9999ff', '#cc66ff',
                                '#00802b', '#00b33c', '#1aff66', '#99ff99',
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
        self.display_spin = True  # if True, display the DOS of the spin up and down, if False, display the total DOS
        self.plot_areas = True  # if True, plot the DOS as stacked areas, else plot the DOS as non stacked lines

        # Figure and axis parameters
        self.figure = pf.Figure(1, 1, 'New Figure')  # figure object
        self.subplot_nb = 1  # subplot number
        self.text_size = 24  # size of the text displayed
        self.title = cell.title  # Title of the plot
        self.label_display = False  # if True, the xlabel and ylabel display depend on 'xlabel_display' and 'ylabel_display'. Else, the xlabel and ylabel are smartly displayed
        self.xlabel_display = True  # if True, the xlabel is displayed
        self.ylabel_display = True  # if True, the ylabel is displayed
        self.common_ylabel_display = False  # if True, a common ylabel is displayed in the middle of the left side
        self.xticklabels_display = True  # if True, display the tick labels of the x-axis
        self.yticks_display = True  # if True, display the ticks of the y-axis
        self.display_legends = True  # if True, display the legends


class BandDiagramPlotParameters:

    def __init__(self, cell):

        # Plot parameters
        self.energy_range = [np.min(cell.bands_data), np.max(cell.bands_data)]
        self.hs_kpoints_names = ['']  # list of names of the kpoints of high symmetry
        self.vbm_shift = False   # if True, shift the bands energy such that the VBM energy is zero
        self.highlight_vbm_cbm = False

        # Figure and axis parameters
        self.figure = pf.Figure(1, 1, 'New Figure')
        self.subplot_nb = 1
        self.text_size = 24
        self.title = cell.title


def normalise_composition(cell1, cell2):
    """ Normalise the population of two Cell objects """

    for key in cell1.population.keys():
        if key not in cell2.population.keys():
            cell2.population[key] = 0

    for key in cell2.population.keys():
        if key not in cell1.population.keys():
            cell1.population[key] = 0
