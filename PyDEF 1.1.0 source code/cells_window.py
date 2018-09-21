""" VASP calculation importation window
    version: DevB1
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import math
import pickle
import ttk
import numpy as np
import Tkinter as tk
import tkFileDialog as fd
import tkMessageBox as mb
from tkColorChooser import askcolor

import pydef_core.cell as pc
import pydef_core.basic_functions as bf

import figures_window as pfw
import utility_tkinter_functions as utk
import defect_studies_window as dsw
import items_choice_window as icw
import utility_tkinter_functions as ukf


class Cells_Window(tk.Toplevel):
    """ Window for importing VASP calculations outputs and managing these data """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('VASP calculations importation tool')

        self.main_window = parent  # PyDEF main window
        self.parent = parent  # parent window
        self.project = parent.project  # current project

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)  # main ttk frame
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------- MENUBAR ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.menubar = tk.Menu(self)

        self.cells_menu = tk.Menu(self.menubar, tearoff=0)
        self.cells_menu.add_command(label='Save calculation(s)...', command=self.save_selected_cells, accelerator='Ctrl+S')
        self.cells_menu.add_command(label='Open calculation(s)...', command=self.open_saved_cells, accelerator='Ctrl+O')
        self.menubar.add_cascade(label='File', menu=self.cells_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label='About', command=self.parent.open_about_window, accelerator='Shift+Ctrl+A')
        self.help_menu.add_command(label='Documentation', command=self.parent.open_user_guide, accelerator='Shift+Ctrl+D')
        self.help_menu.add_command(label='Parameters', command=self.parent.open_parameters_window, accelerator='Shift+Ctrl+P')
        self.menubar.add_cascade(label='Help', menu=self.help_menu)

        self.config(menu=self.menubar)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------- KEYBOARD SHORCUTS ----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.bind('<Control-s>', lambda event: self.save_selected_cells())
        self.bind('<Control-o>', lambda event: self.open_saved_cells())
        self.bind('<Control-w>', lambda event: self.parent.close_cells_window())

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- MANAGE CELLS -----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.input_frame = ttk.Frame(self.main_frame)  # Input frame
        self.input_frame.grid(row=0, column=0, sticky='nswe', pady=10, padx=10)
        self.input_frame.grid_columnconfigure(1, weight=1)

        def get_OUTCAR():
            """ Open a window to select the OUTCAR file """
            filename = fd.askopenfilename(parent=self, initialdir=self.project.dd_vasp)
            if filename != '':
                self.OUTCAR_input_var.set(filename)

        def get_DOSCAR():
            """ Open a window to select the DOSCAR file """
            filename = fd.askopenfilename(parent=self, initialdir=self.project.dd_vasp)
            if filename != '':
                self.DOSCAR_input_var.set(filename)

        # Labels
        ttk.Label(self.input_frame, text='Name').grid(row=0, column=0, padx=5, pady=1)
        ttk.Button(self.input_frame, text='OUTCAR',  width=10, command=get_OUTCAR).grid(row=1, column=0, padx=5, pady=1)
        ttk.Button(self.input_frame, text='DOSCAR',  width=10, command=get_DOSCAR).grid(row=2, column=0, padx=5, pady=1)

        # Variables
        self.cell_id_input_var = tk.StringVar()
        self.OUTCAR_input_var = tk.StringVar()
        self.DOSCAR_input_var = tk.StringVar()
        self.cell_id_input_var.set('automatic')

        # Inputs
        ttk.Entry(self.input_frame, textvariable=self.cell_id_input_var, width=70).grid(row=0, column=1, sticky='we')
        ttk.Entry(self.input_frame, textvariable=self.OUTCAR_input_var,  width=70).grid(row=1, column=1, sticky='we')
        ttk.Entry(self.input_frame, textvariable=self.DOSCAR_input_var,  width=70).grid(row=2, column=1, sticky='we')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- BUTTONS --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)  # Buttons frame
        self.button_frame.grid(row=1, column=0, pady=5)

        def create_cell():
            """ Create a cell object from the value in the fields and add it to the list
            if a cell object with the same name was previously added, it is overwritten """

            OUTCAR = self.OUTCAR_input_var.get()  # OUTCAR location
            DOSCAR = self.DOSCAR_input_var.get()  # DOSCAR location

            if OUTCAR == '':
                mb.showwarning('Error', 'The OUTCAR file is missing', parent=self)
                return None  # stop the process if the OUTCAR location is missing
            else:
                try:
                    cell = pc.Cell(OUTCAR, DOSCAR)  # create the Cell object
                except bf.PydefOutcarError:
                    mb.showerror('Error', 'The given file is not a valid OUTCAR file', parent=self)
                    return None
                except bf.PydefImportError:
                    mb.showerror('Error', 'An error occurred while reading the OUTCAR file. '
                                          'Refer to the documentation for more informations', parent=self)
                    return None
                except bf.PydefDoscarError:
                    mb.showerror('Error', 'The given DOSCAR file is not consistent with the OUTCAR file.'
                                          'Refer to the documentation for more informations', parent=self)
                    return None
                except IOError:
                    mb.showerror('Error', 'The given files do not exist', parent=self)
                    return None

            if self.cell_id_input_var.get() != '' and self.cell_id_input_var.get() != 'automatic':
                cell.ID = self.cell_id_input_var.get()  # if the cell ID is given, then change the ID of the Cell object
            self.load_cell(cell)  # load the cell in the project

        def delete_cell():
            """ Remove the selected cell from the list and from the dictionary """
            selected = self.cells_list.curselection()
            if len(selected) == 0:
                mb.showwarning('Error', 'Select one calculation from the list first', parent=self)
            else:
                cell_id = self.cells_list.get(selected[0])  # ID of the cell selected
                self.cells_list.delete(selected[0])  # remove the cell form the listbox
                self.project.Cells.pop(cell_id)  # remove the cell from the dictionary
                print('Cell "%s" deleted' % cell_id)

            self.defect_window_update()  # Defect window update
            self.defect_study_window_update()  # Defect Study window update
            self.defect_study_properties_window_update()  # Defect study properties windows update

        def plot_dos():
            """ Plot the DOS of the selected Cells """
            selection = self.cells_list.curselection()
            if len(selection) == 0:
                mb.showwarning('Error', 'Select at least one calculation from the list first', parent=self)
                return None
            for selected in selection:
                cell_id = self.cells_list.get(selected)
                cell = self.project.Cells[cell_id]
                try:
                    cell.plot_dos()
                except bf.PydefDoscarError:
                    mb.showwarning('Error', 'No DOSCAR file was specified', parent=self)

        def plot_band_diagram():
            """ Plot the band diagram of the selected Cells """
            selection = self.cells_list.curselection()
            if len(selection) == 0:
                mb.showwarning('Error', 'Select at least one calculation from the list first', parent=self)
                return None
            for selected in selection:
                cell_id = self.cells_list.get(selected)
                cell = self.project.Cells[cell_id]
                try:
                    cell.plot_band_diagram()
                except bf.PydefIchargError:
                    mb.showwarning('Error', 'The calculation need to be performed according to the "standard method" presented at '
                                            'https://cms.mpi.univie.ac.at/wiki/index.php/Si_bandstructure'
                                            '#Procedure_1:_Standard_procedure_.28DFT.29')

        ttk.Button(self.button_frame, text='Import data', command=create_cell).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.button_frame, text='Delete data', command=delete_cell).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(self.button_frame, text='Plot DOS', command=plot_dos).grid(row=1, column=0, padx=5)
        ttk.Button(self.button_frame, text='Plot Band diagram', command=plot_band_diagram).grid(row=1, column=1, padx=5)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- CELLS LIST FRAME ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.cells_list_frame = ttk.Frame(self.main_frame)
        self.cells_list_frame.grid(row=2, column=0, sticky='nswe')
        self.cells_list_frame.grid_rowconfigure(0, weight=1)

        self.yscrollbar = ttk.Scrollbar(self.cells_list_frame, orient='vertical')  # scrollbar for the y-axis
        self.cells_list = tk.Listbox(self.cells_list_frame, selectmode='extended', width=40)

        self.yscrollbar.pack(side='right', fill='y')
        self.cells_list.pack(side='left', fill='both', expand=True)

        self.yscrollbar.config(command=self.cells_list.yview)
        self.cells_list.config(yscrollcommand=self.yscrollbar.set)

        self.cells_list.insert(0, *self.project.Cells)  # Load all the Cells of the project in the listbox

        def open_cell_properties_window():
            """ Open the plot properties window when 'event' happens """
            selection = self.cells_list.curselection()
            if len(selection) != 0:
                cell_id = self.cells_list.get(selection[0])
                Cell_Properties_Window(self, self.project.Cells[cell_id])

        self.cells_list.bind('<Double-Button-1>', lambda event: open_cell_properties_window())

        ukf.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------ METHODS ---------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------- CELLS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def save_selected_cells(self):
        """ Save the selected cells object in the list"""
        selection = self.cells_list.curselection()
        if len(selection) == 0:
            mb.showwarning('Error', 'Select at least one calculation from the list first', parent=self)
            return None

        for selected in selection:
            cell_id = self.cells_list.get(selected)
            cell = self.project.Cells[cell_id]
            openfile = fd.asksaveasfile(parent=self, initialdir=self.project.dd_vasp,
                                        defaultextension='.pydef', initialfile=cell.ID, mode='wb')
            try:
                pickle.dump(cell, openfile, -1)
                openfile.close()
            except AttributeError:  # in case the user click on 'cancel' and no file is given
                continue

    def open_saved_cells(self):
        """ Open and load Cell object(s) from one file or many files """
        files = fd.askopenfiles(parent=self, mode='rb', defaultextension='.pydef')

        for f in files:
            cell = pickle.load(f)
            if cell.__class__ is not pc.Cell:
                mb.showerror('Error', 'This file is not a valid file', parent=self)
                continue
            else:
                self.load_cell(cell)

    # noinspection PyAttributeOutsideInit
    def load_cell(self, cell):
        """ Load a Cell object 'cell' in the project.
        If the Cell object ID is already in the project, ask if overwrite it """

        if cell.ID in self.project.Cells.keys():  # if there is a Cell object with the same ID already in the project
            overwrite = mb.askyesno('Warning', 'The calculation loaded has the same name has another one in the project.'
                                               '\nDo you want to overwrite it?', parent=self)
            if overwrite is True:
                self.project.Cells[cell.ID] = cell
                print('Cell %s modified' % cell.ID)
            else:
                return None
        else:  # load the cell in the project
            self.cells_list.insert(0, cell.ID)
            self.project.Cells[cell.ID] = cell
            print('Cell "%s" added' % cell.ID)

        # Update the Figures dictionary, combobox and subplot numbers
        self.figure_window = pfw.Figure_Window(self)
        try:
            self.figure_window.load_figure(cell.dpp.figure)
        except AttributeError:
            pass
        try:
            self.figure_window.load_figure(cell.bpp.figure)
        except AttributeError:
            pass
        self.figure_window.destroy()

        # Update the windows
        self.defect_window_update()  # Defect window update
        self.defect_study_window_update()  # Defect Study window update
        self.defect_study_properties_window_update()  # Defect study properties windows update

    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------- WIDGETS UPDATE ------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def defect_window_update(self):
        """ Update the combobox of the Defect Window """
        try:
            defect_type = self.parent.defects_window.defect_type_var.get()
            if defect_type != '':
                self.parent.defects_window.display_choices()
        except AttributeError:
            pass

    def defect_study_window_update(self):
        """ Update the figures combobox values of the Defect Study Window"""
        try:
            # Update the Host cell combobox
            self.parent.defect_studies_window.host_cell_ccb['values'] = self.project.Cells.keys()
            if self.parent.defect_studies_window.host_cell_var.get() not in self.project.Cells.keys():
                self.parent.defect_studies_window.host_cell_ccb.set('')

            # Update the Host cell B combobox
            self.parent.defect_studies_window.host_cell_b_ccb['values'] = self.project.Cells.keys()
            if self.parent.defect_studies_window.host_cell_b_var.get() not in self.project.Cells.keys():
                self.parent.defect_studies_window.host_cell_b_ccb.set('None')
        except AttributeError:
            pass

    def defect_study_properties_window_update(self):
        """ Update the defect cell combobox of the Defect_Cell_Properties_Window objects """
        try:
            defect_study_properties_windows = [child for child in
                                               self.main_window.defect_studies_window.winfo_children()
                                               if child.__class__ is dsw.Defect_Study_Properties_Window]
            for window in defect_study_properties_windows:
                window.populate_defect_cells_ccb()
                window.defect_cell_ccb.set('')
        except AttributeError:
            pass


class Cell_Properties_Window(tk.Toplevel):
    """ Display various informations on the calculation and the parameters for the plot of the density of states """

    def __init__(self, parent, cell):
        """
        :param parent: Parent window
        :param cell: a Cell object
        """

        tk.Toplevel.__init__(self, parent)

        self.title(cell.ID)
        self.bind('<Control-w>', lambda event: self.destroy())
        self.resizable(False, False)

        self.main_window = parent.parent  # main PyDEF window
        self.parent = parent  # parent window
        self.project = parent.project  # current project
        self.cell = cell  # current cell

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.cell_notebook = ttk.Notebook(self)
        self.cell_notebook.pack(fill='both', expand=True)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------- PROPERTIES & RESULTS -------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.properties_frame = ttk.Frame(self.cell_notebook)
        self.cell_notebook.add(self.properties_frame, text='Properties & Results')
        self.properties_frame.grid_columnconfigure(0, weight=1)
        self.properties_frame.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------------- FILES --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.file_loc_frame_label = ttk.Label(self, text='Files location', font='-weight bold')
        self.file_loc_frame = ttk.LabelFrame(self.properties_frame, labelwidget=self.file_loc_frame_label)
        self.file_loc_frame.grid(row=0, column=0, columnspan=2, sticky='we', padx=5, pady=5)

        ttk.Label(self.file_loc_frame, text='OUTCAR: ' + self.cell.OUTCAR).grid(row=0, sticky='w')
        ttk.Label(self.file_loc_frame, text='DOSCAR: ' + self.cell.DOSCAR).grid(row=1, sticky='w')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------- SYSTEM PROPERTIES ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.system_prop_frame_label = ttk.Label(self, text='System properties', font='-weight bold')
        self.system_prop_frame = ttk.LabelFrame(self.properties_frame, labelwidget=self.system_prop_frame_label)
        self.system_prop_frame.grid(row=1, column=0, sticky='nswe', padx=5, pady=5)

        def open_detailed_pop_window():
            """ Open a new window giving population of each atomic species """
            self.pop_but.configure(state='disabled')
            self.cell_pop_window = Cell_Population_Window(self)
            self.cell_pop_window.protocol('WM_DELETE_WINDOW', self.close_detailed_pop_window)

        ttk.Label(self.system_prop_frame, text='System name: ' + self.cell.name).\
            grid(row=0, column=0, sticky='w')
        ttk.Label(self.system_prop_frame, text='Number of atoms: %s' % int(self.cell.nb_atoms_tot)).\
            grid(row=2, column=0, sticky='w')
        ttk.Label(self.system_prop_frame, text='Number of electrons: %s' % int(self.cell.nb_electrons)).\
            grid(row=3, column=0, sticky='w')
        ttk.Label(self.system_prop_frame, text='Charge: %s' % int(self.cell.charge)).\
            grid(row=4, column=0, sticky='w')
        self.pop_but = ttk.Button(self.system_prop_frame, text='Detailed population', command=open_detailed_pop_window)
        self.pop_but.grid(row=5, column=0, sticky='w')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------- SYSTEM PARAMETERS ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.system_param_frame_label = ttk.Label(self, text='Calculation properties', font='-weight bold')
        self.system_param_frame = ttk.LabelFrame(self.properties_frame, labelwidget=self.system_param_frame_label)
        self.system_param_frame.grid(row=1, column=1, sticky='nswe', padx=5, pady=5)

        ttk.Label(self.system_param_frame, text='Method: ' + self.cell.functional).grid(row=0, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='NEDOS: %s' % int(self.cell.nedos)).grid(row=1, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='EDIFF: %s eV' % self.cell.ediff).grid(row=2, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='ENCUT: %s eV' % self.cell.encut).grid(row=3, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='ISMEAR: %s' % self.cell.ismear).grid(row=4, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='LORBIT: %s' % self.cell.lorbit).grid(row=5, column=0, sticky='w')
        ttk.Label(self.system_param_frame, text='ISPIN: %s' % self.cell.ispin).grid(row=6, column=0, sticky='w')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------- CALCULATION RESULTS ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.results_frame_label = ttk.Label(self, text='Calculations results', font='-weight bold')
        self.results_frame = ttk.LabelFrame(self.properties_frame, labelwidget=self.results_frame_label)
        self.results_frame.grid(row=2, columnspan=2, sticky='nswe', padx=5, pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)

        def open_band_occupation_window():
            """ Open a new window giving the occupation of each band for each calculated k-point """
            self.band_but.configure(state='disabled')
            self.band_window = Band_Occupation_Window(self)
            self.band_window.protocol('WM_DELETE_WINDOW', self.close_band_occupation_window)

        ttk.Label(self.results_frame, text='Nb electronic iterations: %s' % int(self.cell.nb_iterations))\
            .grid(row=0, column=0, sticky='w')
        ttk.Label(self.results_frame, text='Nb k-points: %s' % int(self.cell.nkpts))\
            .grid(row=1, column=0, sticky='w')
        ttk.Label(self.results_frame, text='Nb bands: %s' % int(self.cell.nbands))\
            .grid(row=2, column=0, sticky='w')
        self.band_but = ttk.Button(self.results_frame, text='Bands occupation', command=open_band_occupation_window)
        self.band_but.grid(row=3, column=0, sticky='w')

        ttk.Label(self.results_frame, text='Free energy: %s eV' % self.cell.energy)\
            .grid(row=0, column=1, sticky='w')
        ttk.Label(self.results_frame, text='Fermi energy: %s eV' % self.cell.fermi_energy)\
            .grid(row=1, column=1, sticky='w')
        ttk.Label(self.results_frame, text='VBM energy: %s eV' % self.cell.VBM)\
            .grid(row=2, column=1, sticky='w')
        ttk.Label(self.results_frame, text='CBM energy: %s eV' % self.cell.CBM)\
            .grid(row=3, column=1, sticky='w')
        ttk.Label(self.results_frame, text='Gap: %s eV' % self.cell.gap)\
            .grid(row=4, column=1, sticky='w')

        if hasattr(self.cell, 'doscar'):
            self.display_dos_parameters_window()
        if self.cell.icharg == 11:
            self.display_band_diagram_plot_parameters_window()

        self.display_window_buttons()

        ukf.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------ METHODS ---------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # noinspection PyAttributeOutsideInit
    def display_dos_parameters_window(self):
        """ Display the DOS parameters frame """

        self.dos_param_frame = ttk.Frame(self.cell_notebook)
        self.cell_notebook.add(self.dos_param_frame, text='DOS plot parameters')
        self.dos_param_frame.grid_columnconfigure(0, weight=1)
        self.dos_param_frame.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- COLUMN 1 -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.column1_frame = ttk.Frame(self.dos_param_frame)
        self.column1_frame.grid(row=0, column=0, padx=5, sticky='nswe')
        self.column1_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- DOS type -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.display_spin_var = tk.BooleanVar()
        self.display_spin_var.set(self.cell.dpp.display_spin)

        self.dos_type_frame_labelframe = ttk.Frame(self)
        ttk.Label(self.dos_type_frame_labelframe, text='DOS displayed', font='-weight bold').pack(side='left')
        if self.cell.ispin == 2:
            self.spin_button = ttk.Checkbutton(self.dos_type_frame_labelframe, text='Spin projection',
                                               onvalue=True, offvalue=False, variable=self.display_spin_var)
            self.spin_button.pack()

        self.dos_type_frame = ttk.LabelFrame(self.column1_frame, labelwidget=self.dos_type_frame_labelframe)
        self.dos_type_frame.grid(row=0, column=0, sticky='nswe', padx=5)
        self.dos_type_frame.grid_columnconfigure(0, weight=1)

        self.opas_items_choice = self.cell.dpp.choice_opas  # Initial choice for the OPAS items choice
        self.opa_items_choice = self.cell.dpp.choice_opa  # Initial choice for the OPA items choice

        self.proj_colors_choice = self.cell.dpp.colors_proj  # Projected DOS colors choice
        self.tot_colors_choice = self.cell.dpp.colors_tot  # Total projected DOS colors choice

        # -------------------------------------------------- TOTAL DOS -------------------------------------------------

        self.tot_dos_var = tk.BooleanVar()
        self.tot_dos_var.set(self.cell.dpp.display_total_dos)

        self.tot_dos = ttk.Checkbutton(self.dos_type_frame, text='Total DOS', variable=self.tot_dos_var,
                                       onvalue=True, offvalue=False).grid(row=0, column=0)

        # ------------------------------------------------ PROJECTED DOS -----------------------------------------------

        self.proj_dos_var = tk.BooleanVar()  # determine if the projected DOS is plotted

        # Initial state of the checkbutton
        if self.cell.lorbit == 11:
            self.proj_dos_var.set(self.cell.dpp.display_proj_dos)
        else:
            self.proj_dos_var.set(False)
            self.proj_dos_checkbutton.configure(state='disabled')

        # Labelframe and checkbutton
        def enable_proj_dos():
            """ Enable the projected dos frame is the checkbutton is checked and disable it if it is not """
            if self.proj_dos_var.get() is True:
                utk.enable_frame(self.proj_dos_frame)
            elif self.proj_dos_var.get() is False:
                utk.disable_frame(self.proj_dos_frame)

        self.proj_dos_checkbutton = ttk.Checkbutton(self, text='Projected DOS', onvalue=True, offvalue=False,
                                                    variable=self.proj_dos_var, command=enable_proj_dos)

        self.proj_dos_frame = ttk.LabelFrame(self.dos_type_frame, labelwidget=self.proj_dos_checkbutton,
                                             labelanchor='n')
        self.proj_dos_frame.grid(row=1, column=0, sticky='nswe', padx=5)
        self.proj_dos_frame.grid_columnconfigure(0, weight=1)
        self.proj_dos_frame.grid_columnconfigure(1, weight=1)
        self.proj_dos_frame.grid_columnconfigure(2, weight=1)

        # CONTENT
        # DOS type
        self.dos_type_var = tk.StringVar()  # Type of the DOS
        self.dos_type_var.set(self.cell.dpp.dos_type)

        ttk.Label(self.proj_dos_frame, text='DOS for each...').grid(row=0, column=0, sticky='w')

        ttk.Radiobutton(self.proj_dos_frame, text='Atomic species', variable=self.dos_type_var, value='OPAS'
                        ).grid(row=1, column=0)
        ttk.Radiobutton(self.proj_dos_frame, text='Atom', variable=self.dos_type_var, value='OPA',
                        ).grid(row=1, column=1)

        # Projection choice
        self.tot_proj_dos_var = tk.BooleanVar()  # Projected DOS or total projected DOS
        self.tot_proj_dos_var.set(self.cell.dpp.tot_proj_dos)

        ttk.Label(self.proj_dos_frame, text='Projection').grid(row=2, column=0, sticky='w')
        ttk.Radiobutton(self.proj_dos_frame, text='Orbitals projection', variable=self.tot_proj_dos_var,
                        value=False).grid(row=3, column=0)
        ttk.Radiobutton(self.proj_dos_frame, text='Total DOS', variable=self.tot_proj_dos_var, value=True
                        ).grid(row=3, column=1)

        # Areas or lines
        self.plot_areas_var = tk.BooleanVar()
        self.plot_areas_var.set(self.cell.dpp.plot_areas)

        ttk.Label(self.proj_dos_frame, text='Projected DOS type...').grid(row=4, column=0, sticky='w')
        ttk.Radiobutton(self.proj_dos_frame, text='Stacked areas', variable=self.plot_areas_var, value=True
                        ).grid(row=5, column=0)
        ttk.Radiobutton(self.proj_dos_frame, text='Non-stacked lines', variable=self.plot_areas_var, value=False
                        ).grid(row=5, column=1)

        # Items and colors choice
        def open_atoms_choice_window():
            """ Open the Items_Choice_Window """

            output_var = tk.StringVar()
            if self.dos_type_var.get() == 'OPAS':
                items = self.cell.atoms_types
                items_on = self.opas_items_choice
                label_on = 'Atomic species plotted'
                label_off = 'Atomic species non plotted'
            else:
                items = self.cell.atoms
                items_on = self.opa_items_choice
                label_on = 'Atoms plotted'
                label_off = 'Atoms not plotted'

            self.items_choice_window = icw.Items_Choice_Window(self, items, items_on, output_var, label_on, label_off)
            self.items_choice_window.grab_set()
            self.wait_window(self.items_choice_window)
            if self.dos_type_var.get() == 'OPAS':
                self.opas_items_choice = output_var.get().split(',')
                print('OPAS choice %s' % self.opas_items_choice)
            else:
                self.opa_items_choice = output_var.get().split(',')
                print('OPA choice %s' % self.opa_items_choice)
            self.items_choice_window.grab_release()

        def open_color_choice_window():
            """ Open the Colors_Choice_Window """

            self.colors_choice_window = Colors_Choice_Window(self)
            self.colors_choice_window.grab_set()
            self.wait_window(self.colors_choice_window)
            self.colors_choice_window.grab_release()

        ttk.Label(self.proj_dos_frame, text=' ').grid(row=6, column=0)

        self.items_button = ttk.Button(self.proj_dos_frame, text='Data plotted', command=open_atoms_choice_window)
        self.items_button.grid(row=7, column=0)

        self.colors_but = ttk.Button(self.proj_dos_frame, text='Colours', command=open_color_choice_window)
        self.colors_but.grid(row=7, column=1)

        enable_proj_dos()  # initiate the projected DOS frame state

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------ PLOT DISPLAY ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.plot_display_frame_label = ttk.Label(self, text='Data displayed', font="-weight bold")
        self.plot_display_frame = ttk.LabelFrame(self.column1_frame, labelwidget=self.plot_display_frame_label)
        self.plot_display_frame.grid(row=1, column=0, sticky='nswe', padx=5)

        # Fermi level
        self.fermi_level_dis_var = tk.BooleanVar()
        self.fermi_level_dis_var.set(self.cell.dpp.display_Fermi_level)

        ttk.Checkbutton(self.plot_display_frame, text='Fermi level', variable=self.fermi_level_dis_var, onvalue=True,
                        offvalue=False).grid(row=0, column=0, sticky='w')

        # Band extrema
        self.band_extrema_dis_var = tk.BooleanVar()
        self.band_extrema_dis_var.set(self.cell.dpp.display_BM_levels)

        ttk.Checkbutton(self.plot_display_frame, text='Band extrema levels', variable=self.band_extrema_dis_var,
                        onvalue=True, offvalue=False).grid(row=1, column=0, sticky='w')

        # Legend
        self.legend_dis_var = tk.BooleanVar()
        self.legend_dis_var.set(self.cell.dpp.display_legends)

        ttk.Checkbutton(self.plot_display_frame, text='Legend', onvalue=True, offvalue=False,
                        variable=self.legend_dis_var).grid(row=2, column=0, sticky='w')

        # Fermi shift
        def update_energy_range():
            """ Update the energy range"""
            if self.fermi_shift_var.get() is True:
                self.e_low_var.set(np.round((self.e_low_var.get() - self.cell.fermi_energy), 3))
                self.e_high_var.set(np.round((self.e_high_var.get() - self.cell.fermi_energy), 3))
            else:
                self.e_low_var.set(np.round((self.e_low_var.get() + self.cell.fermi_energy), 3))
                self.e_high_var.set(np.round((self.e_high_var.get() + self.cell.fermi_energy), 3))

        self.fermi_shift_var = tk.BooleanVar()
        self.fermi_shift_var.set(self.cell.dpp.fermi_shift)

        ttk.Checkbutton(self.plot_display_frame, text='Fermi level as zero of energy',
                        variable=self.fermi_shift_var, onvalue=True, offvalue=False,
                        command=update_energy_range).grid(row=3, column=0, sticky='w')

        # Energy range
        self.e_low_var = tk.DoubleVar()
        self.e_high_var = tk.DoubleVar()
        self.e_low_var.set(self.cell.dpp.E_range[0])
        self.e_high_var.set(self.cell.dpp.E_range[1])

        self.e_range_frame = ttk.Frame(self.plot_display_frame)
        self.e_range_frame.grid(row=5, column=0, sticky='w')

        ttk.Label(self.e_range_frame, text='Energy: from').pack(side='left')
        ttk.Entry(self.e_range_frame, textvariable=self.e_low_var, width=6).pack(side='left')
        ttk.Label(self.e_range_frame, text='eV to').pack(side='left')
        ttk.Entry(self.e_range_frame, textvariable=self.e_high_var, width=6).pack(side='left')
        ttk.Label(self.e_range_frame, text='eV').pack(side='left')

        # Normalise DOS
        self.normalise_dos_var = tk.BooleanVar()
        self.normalise_dos_var.set(self.cell.dpp.normalise_dos)

        def update_dos_range():
            """ Update the DOS range """
            if self.normalise_dos_var.get() is True:
                self.dos_low_var.set(np.round((self.dos_low_var.get()/self.cell.dosmax), 5))
                self.dos_high_var.set(np.round((self.dos_high_var.get()/self.cell.dosmax), 5))
            else:
                self.dos_low_var.set(np.round((self.dos_low_var.get()*self.cell.dosmax), 5))
                self.dos_high_var.set(np.round((self.dos_high_var.get()*self.cell.dosmax), 5))

        ttk.Checkbutton(self.plot_display_frame, text='Normalise DOS', variable=self.normalise_dos_var,
                        onvalue=True, offvalue=False, command=update_dos_range).grid(row=4, column=0, sticky='w')

        # DOS range
        self.dos_low_var = tk.DoubleVar()
        self.dos_high_var = tk.DoubleVar()
        self.dos_low_var.set(self.cell.dpp.DOS_range[0])
        self.dos_high_var.set(self.cell.dpp.DOS_range[1])

        self.dos_range_frame = ttk.Frame(self.plot_display_frame)
        self.dos_range_frame.grid(row=6, column=0, sticky='w')

        ttk.Label(self.dos_range_frame, text='DOS: from').pack(side='left')
        ttk.Entry(self.dos_range_frame, textvariable=self.dos_low_var, width=7).pack(side='left')
        ttk.Label(self.dos_range_frame, text='states/eV to').pack(side='left')
        ttk.Entry(self.dos_range_frame, textvariable=self.dos_high_var, width=7).pack(side='left')
        ttk.Label(self.dos_range_frame, text='states/eV').pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------- COLUMN 2 --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.column2_frame = ttk.Frame(self.dos_param_frame)
        self.column2_frame.grid(row=0, column=1, padx=5, sticky='nswe')
        self.column2_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------- FIGURE PARAMETERS ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.figure_parameters_frame_label = ttk.Label(self, text='Figure', font="-weight bold")
        self.figure_parameters_frame = ttk.LabelFrame(self.column2_frame, labelwidget=self.figure_parameters_frame_label)
        self.figure_parameters_frame.grid(row=0, column=1, padx=5, sticky='nswe')
        self.figure_parameters_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------- FIGURE ---------------------------------------------------

        self.figure_var = tk.StringVar()
        self.figure_var.set(self.cell.dpp.figure.name)

        self.figure_frame = ttk.Frame(self.figure_parameters_frame)
        self.figure_frame.grid(row=0, column=0)

        def create_figure():
            """ Create a Figure_Window object """

            self.figure_window = pfw.Figure_Window(self)
            self.figure_window.grab_set()
            self.wait_window(self.figure_window)
            self.figure_window.grab_release()

        def delete_figure():
            """ Delete the current selected figure in the combobox """

            figures_window = pfw.Figure_Window(self)
            figures_window.delete_figure(self.figure_var)
            figures_window.destroy()

        ttk.Button(self.figure_frame, text='Create Figure', command=create_figure).grid(row=1, column=0, padx=5, pady=3)
        ttk.Button(self.figure_frame, text='Delete Figure', command=delete_figure).grid(row=1, column=1, padx=5, pady=3)
        self.fig_combobox = ttk.Combobox(self.figure_frame, values=self.project.Figures.keys(), width=15,
                                         textvariable=self.figure_var, state='readonly')
        self.fig_combobox.grid(row=0, column=0, columnspan=2, padx=5, pady=3)

        self.fig_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_subplot_nb())

        # --------------------------------------------------- SUBPLOT NB -----------------------------------------------

        self.subplot_nb_var = tk.IntVar()
        self.subplot_nb_var.set(self.cell.dpp.subplot_nb)

        self.subplot_frame = ttk.Frame(self.figure_parameters_frame)
        self.subplot_frame.grid(row=1, column=0)

        def open_subplot_nb_choice_window():
            """ Open the Subplot_Number_Choice_Window """
            subplot_window = pfw.Subplot_Number_Choice_Window(self, self.cell,
                                                              self.project.Figures[self.figure_var.get()],
                                                              self.subplot_nb_var)
            subplot_window.grab_set()
            self.wait_window(subplot_window)
            subplot_window.grab_release()

        ttk.Button(self.subplot_frame, text='Plot position', command=open_subplot_nb_choice_window).pack(side='left', padx=5, pady=3)
        ttk.Entry(self.subplot_frame, textvariable=self.subplot_nb_var, width=2, state='readonly').pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- LABELS PARAMETERS --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.label_parameters_frame_label = ttk.Label(self, text='Labels', font="-weight bold")
        self.label_parameters_frame = ttk.LabelFrame(self.column2_frame, labelwidget=self.label_parameters_frame_label)
        self.label_parameters_frame.grid(row=1, column=1, padx=5, sticky='nswe')
        self.label_parameters_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- TITLE --------------------------------------------------

        self.title_var = tk.StringVar()
        self.title_var.set(self.cell.dpp.title)

        self.title_frame = ttk.Frame(self.label_parameters_frame)
        self.title_frame.grid(row=0, column=0, sticky='w')

        ttk.Label(self.title_frame, text='Title').pack(side='left')
        ttk.Entry(self.title_frame, textvariable=self.title_var, width=30).pack(side='left', expand=True, fill='x')

        # --------------------------------------------------- TEXT SIZE ------------------------------------------------

        self.text_size_var = tk.IntVar()
        self.text_size_var.set(self.cell.dpp.text_size)

        self.text_size_frame = ttk.Frame(self.label_parameters_frame)
        self.text_size_frame.grid(row=1, column=0)

        ttk.Label(self.text_size_frame, text='Text size').pack(side='left')
        self.spin = tk.Spinbox(self.text_size_frame, from_=10, to=100, textvariable=self.text_size_var, width=3)
        self.spin.pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------- AXIS LABELS -----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.label_display_var = tk.BooleanVar()
        self.xlabel_display_var = tk.BooleanVar()
        self.ylabel_display_var = tk.BooleanVar()
        self.common_ylabel_display_var = tk.BooleanVar()
        self.xticklabels_display_var = tk.BooleanVar()
        self.yticks_display_var = tk.BooleanVar()

        self.label_display_var.set(self.cell.dpp.label_display)
        self.xlabel_display_var.set(self.cell.dpp.xlabel_display)
        self.ylabel_display_var.set(self.cell.dpp.ylabel_display)
        self.common_ylabel_display_var.set(self.cell.dpp.common_ylabel_display)
        self.xticklabels_display_var.set(self.cell.dpp.xticklabels_display)
        self.yticks_display_var.set(self.cell.dpp.yticks_display)

        def enable_axis_label():
            """ Enable the projected dos frame is the checkbutton is checked and disable it if it is not """
            if self.label_display_var.get() is True:
                utk.enable_frame(self.axis_label_frame)
            elif self.label_display_var.get() is False:
                utk.disable_frame(self.axis_label_frame)

        self.auto_label_frame = ttk.Frame(self)
        ttk.Label(self.auto_label_frame, text='Axis labelling').grid(row=0, column=0, columnspan=2)
        ttk.Radiobutton(self.auto_label_frame, variable=self.label_display_var, value=True, text='Personalised',
                        command=enable_axis_label).grid(row=1, column=0)
        ttk.Radiobutton(self.auto_label_frame, variable=self.label_display_var, value=False, text='Auto',
                        command=enable_axis_label).grid(row=1, column=1)

        self.axis_label_frame = ttk.LabelFrame(self.label_parameters_frame, labelwidget=self.auto_label_frame)
        self.axis_label_frame.grid(row=5, column=0, padx=5, pady=5)

        ttk.Checkbutton(self.axis_label_frame, text='X axis label', variable=self.xlabel_display_var).\
            grid(row=0, column=0)
        ttk.Checkbutton(self.axis_label_frame, text='Y axis label', variable=self.ylabel_display_var).\
            grid(row=1, column=0)
        ttk.Checkbutton(self.axis_label_frame, text='Common Y axis label', variable=self.common_ylabel_display_var).\
            grid(row=2, column=0)
        ttk.Checkbutton(self.axis_label_frame, text='X axis values', variable=self.xticklabels_display_var).\
            grid(row=3, column=0)
        ttk.Checkbutton(self.axis_label_frame, text='Y axis values', variable=self.yticks_display_var).\
            grid(row=4, column=0)

        enable_axis_label()  # initiate

    # noinspection PyAttributeOutsideInit
    def display_band_diagram_plot_parameters_window(self):
        """ Display the band diagram plot parameters window """

        band_param_frame = ttk.Frame(self.cell_notebook)
        self.cell_notebook.add(band_param_frame, text='Band diagram plot parameters')
        band_param_frame.grid_columnconfigure(0, weight=1)
        band_param_frame.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- COLUMN 1 -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        column1_frame = ttk.Frame(band_param_frame)
        column1_frame.grid(row=0, column=0, padx=5, sticky='nswe')
        column1_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------ DATA DISPLAYED ----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        data_displayed_frame_label = ttk.Label(self, text='Data displayed', font="-weight bold")
        data_displayed_frame = ttk.LabelFrame(column1_frame, labelwidget=data_displayed_frame_label)
        data_displayed_frame.grid(row=0, column=0, sticky='nswe', padx=5)

        # -------------------------------------------------- VARIABLES -------------------------------------------------

        self.b_en_low_var = tk.DoubleVar()
        self.b_en_high_var = tk.DoubleVar()
        self.vbm_shift_var = tk.BooleanVar()
        self.highlight_vbm_cbm_var = tk.BooleanVar()
        self.hs_kpoints_var = tk.StringVar()

        self.b_en_low_var.set(self.cell.bpp.energy_range[0])
        self.b_en_high_var.set(self.cell.bpp.energy_range[1])
        self.vbm_shift_var.set(self.cell.bpp.vbm_shift)
        self.highlight_vbm_cbm_var.set(self.cell.bpp.highlight_vbm_cbm)
        self.hs_kpoints_var.set(', '.join(self.cell.bpp.hs_kpoints_names))

        # -------------------------------------------- LABELS ANB INPUT BOXES ------------------------------------------

        # Energy range
        energy_range_frame = ttk.Frame(data_displayed_frame)
        energy_range_frame.grid(sticky='w')

        ttk.Label(energy_range_frame, text='Energy: from').pack(side='left')
        ttk.Entry(energy_range_frame, textvariable=self.b_en_low_var, width=6).pack(side='left')
        ttk.Label(energy_range_frame, text='eV to').pack(side='left')
        ttk.Entry(energy_range_frame, textvariable=self.b_en_high_var, width=6).pack(side='left')
        ttk.Label(energy_range_frame, text='eV').pack(side='left')

        # VBM shift
        def update_energy_range():
            """ Update the energy range"""

            if self.vbm_shift_var.get() is True:
                self.b_en_low_var.set(np.round((self.b_en_low_var.get() - self.cell.VBM), 3))
                self.b_en_high_var.set(np.round((self.b_en_high_var.get() - self.cell.VBM), 3))
            else:
                self.b_en_low_var.set(np.round((self.b_en_low_var.get() + self.cell.VBM), 3))
                self.b_en_high_var.set(np.round((self.b_en_high_var.get() + self.cell.VBM), 3))

        ttk.Checkbutton(data_displayed_frame, text='VBM as zero of energy', variable=self.vbm_shift_var,
                        onvalue=True, offvalue=False, command=update_energy_range).grid(sticky='w')

        # Highlight VBM & CBM
        ttk.Checkbutton(data_displayed_frame, text='Highlight VBM & CBM', variable=self.highlight_vbm_cbm_var,
                        onvalue=True, offvalue=False).grid(sticky='w')

        # High Symmetry K-points
        hs_kpoints_frame = ttk.Frame(data_displayed_frame)
        hs_kpoints_frame.grid(sticky='w')

        ttk.Label(hs_kpoints_frame, text='High symmetry K-points ').pack(side='left')
        ttk.Entry(hs_kpoints_frame, textvariable=self.hs_kpoints_var, width=20).pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- COLUMN 2 -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        column2_frame = ttk.Frame(band_param_frame)
        column2_frame.grid(row=0, column=1, padx=5, sticky='nswe')
        column2_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------- FIGURE PARAMETERS ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        b_figure_parameters_frame_label = ttk.Label(self, text='Figure', font="-weight bold")
        b_figure_parameters_frame = ttk.LabelFrame(column2_frame, labelwidget=b_figure_parameters_frame_label)
        b_figure_parameters_frame.grid(row=0, column=1, sticky='nswe', padx=5)

        # --------------------------------------------------- FIGURE ---------------------------------------------------

        self.b_figure_var = tk.StringVar()
        self.b_figure_var.set(self.cell.bpp.figure.name)

        b_figure_frame = ttk.Frame(b_figure_parameters_frame)
        b_figure_frame.grid(row=0, column=0)

        def create_figure():
            """ Create a Figure_Window object """

            figure_window = pfw.Figure_Window(self)
            figure_window.grab_set()
            self.wait_window(figure_window)
            figure_window.grab_release()

        def delete_figure():
            """ Delete the current selected figure in the combobox """

            figures_window = pfw.Figure_Window(self)
            figures_window.delete_figure(self.b_figure_var)
            figures_window.destroy()

        ttk.Button(b_figure_frame, text='Create Figure', command=create_figure).grid(row=1, column=0, padx=5, pady=3)
        ttk.Button(b_figure_frame, text='Delete Figure', command=delete_figure).grid(row=1, column=1, padx=5, pady=3)
        self.b_fig_combobox = ttk.Combobox(b_figure_frame, values=self.project.Figures.keys(), width=15,
                                           textvariable=self.b_figure_var, state='readonly')
        self.b_fig_combobox.grid(row=0, column=0, columnspan=2, padx=5, pady=3)

        self.b_fig_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_b_subplot_nb())

        # --------------------------------------------------- SUBPLOT NB -----------------------------------------------

        self.b_subplot_nb_var = tk.IntVar()
        self.b_subplot_nb_var.set(self.cell.bpp.subplot_nb)

        b_subplot_frame = ttk.Frame(b_figure_parameters_frame)
        b_subplot_frame.grid(row=1, column=0)

        def open_subplot_nb_choice_window():
            """ Open the Subplot_Number_Choice_Window """
            b_subplot_window = pfw.Subplot_Number_Choice_Window(self, self.cell,
                                                                self.project.Figures[self.b_figure_var.get()],
                                                                self.b_subplot_nb_var)
            b_subplot_window.grab_set()
            self.wait_window(b_subplot_window)
            b_subplot_window.grab_release()

        ttk.Button(b_subplot_frame, text='Plot position', command=open_subplot_nb_choice_window).pack(side='left', padx=5, pady=3)
        ttk.Entry(b_subplot_frame, textvariable=self.b_subplot_nb_var, width=2, state='readonly').pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- LABELS PARAMETERS --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        b_label_parameters_frame_label = ttk.Label(self, text='Labels', font="-weight bold")
        b_label_parameters_frame = ttk.LabelFrame(column2_frame, labelwidget=b_label_parameters_frame_label)
        b_label_parameters_frame.grid(row=1, column=1, padx=5, sticky='nswe')
        b_label_parameters_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- TITLE --------------------------------------------------

        self.b_title_var = tk.StringVar()
        self.b_title_var.set(self.cell.bpp.title)

        b_title_frame = ttk.Frame(b_label_parameters_frame)
        b_title_frame.grid(row=0, column=0, sticky='w')

        ttk.Label(b_title_frame, text='Title').pack(side='left')
        ttk.Entry(b_title_frame, textvariable=self.b_title_var, width=30).pack(side='left', expand=True, fill='x')

        # --------------------------------------------------- TEXT SIZE ------------------------------------------------

        self.b_text_size_var = tk.IntVar()
        self.b_text_size_var.set(self.cell.bpp.text_size)

        b_text_size_frame = ttk.Frame(b_label_parameters_frame)
        b_text_size_frame.grid(row=1, column=0)

        ttk.Label(b_text_size_frame, text='Text size').pack(side='left')
        tk.Spinbox(b_text_size_frame, from_=10, to=100, textvariable=self.b_text_size_var, width=3).pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- BUTTONS -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

    def display_window_buttons(self):

        button_frame = ttk.Frame(self)
        button_frame.pack(side='bottom', expand=True, fill='both')

        def save_dos_parameters():
            """ Save all parameters to the Cell object DOS Plot Parameters and close the window """

            # Spin projection
            self.cell.dpp.display_spin = self.display_spin_var.get()

            # Total DOS
            self.cell.dpp.display_total_dos = self.tot_dos_var.get()

            # Projection: DOS type
            self.cell.dpp.display_proj_dos = self.proj_dos_var.get()
            self.cell.dpp.dos_type = self.dos_type_var.get()
            self.cell.dpp.tot_proj_dos = self.tot_proj_dos_var.get()

            # Projected DOS type
            self.cell.dpp.plot_areas = self.plot_areas_var.get()

            # Items choice
            self.cell.dpp.choice_opa = self.opa_items_choice
            self.cell.dpp.choice_opas = self.opas_items_choice

            # Colors choice
            self.cell.dpp.colors_tot = self.tot_colors_choice
            self.cell.dpp.colors_proj = self.proj_colors_choice

            # Fermi level display
            self.cell.dpp.display_Fermi_level = self.fermi_level_dis_var.get()

            # Band extrema display
            self.cell.dpp.display_BM_levels = self.band_extrema_dis_var.get()

            # Fermi shift
            self.cell.dpp.fermi_shift = self.fermi_shift_var.get()

            # DOS normalisation
            self.cell.dpp.normalise_dos = self.normalise_dos_var.get()

            # Energy & DOS ranges
            try:
                self.cell.dpp.E_range = [float(self.e_low_var.get()), float(self.e_high_var.get())]
            except ValueError:
                mb.showerror('Error', 'Enter a correct value for the energy range', parent=self)
                return None

            try:
                self.cell.dpp.DOS_range = [float(self.dos_low_var.get()), float(self.dos_high_var.get())]
            except ValueError:
                mb.showerror('Error', 'Enter a correct value for the DOS range', parent=self)
                return None

            # FIGURE PARAMETERS
            # Legend
            self.cell.dpp.display_legends = self.legend_dis_var.get()

            # Text size
            self.cell.dpp.text_size = self.text_size_var.get()

            # Title
            self.cell.dpp.title = self.title_var.get()

            # Subplot number
            self.cell.dpp.subplot_nb = self.subplot_nb_var.get()

            # Figure
            self.cell.dpp.figure = self.project.Figures[self.figure_var.get()]

            # Axis
            self.cell.dpp.label_display = self.label_display_var.get()
            self.cell.dpp.xlabel_display = self.xlabel_display_var.get()
            self.cell.dpp.ylabel_display = self.ylabel_display_var.get()
            self.cell.dpp.common_ylabel_display = self.common_ylabel_display_var.get()
            self.cell.dpp.xticklabels_display = self.xticklabels_display_var.get()
            self.cell.dpp.yticks_display = self.yticks_display_var.get()

        def save_band_parameters():
            """ Save the band diagram plot parameters """

            # Energy range
            try:
                self.cell.bpp.energy_range = [self.b_en_low_var.get(), self.b_en_high_var.get()]
            except ValueError:
                mb.showerror('Error', 'Enter a correct value for the energy range', parent=self)
                return None

            # VBM shift
            self.cell.bpp.vbm_shift = self.vbm_shift_var.get()

            # Highlight VBM & CBM
            self.cell.bpp.highlight_vbm_cbm = self.highlight_vbm_cbm_var.get()

            # High symmetry K-points
            self.cell.bpp.hs_kpoints_names = [f.strip() for f in self.hs_kpoints_var.get().split(',')]

            # Subplot number
            self.cell.bpp.subplot_nb = self.b_subplot_nb_var.get()

            # Figure
            self.cell.bpp.figure = self.project.Figures[self.b_figure_var.get()]

            # Text size
            self.cell.bpp.text_size = self.b_text_size_var.get()

            # Title
            self.cell.bpp.title = self.b_title_var.get()

        def save_parameters():
            """ Save the parameters and close the window """

            if hasattr(self.cell, 'doscar'):
                save_dos_parameters()
            if self.cell.icharg == 11:
                save_band_parameters()

            self.destroy()

        ttk.Button(button_frame, text='Save', command=save_parameters).pack(side='right', pady=5, padx=3)
        ttk.Button(button_frame, text='Cancel', command=self.destroy).pack(side='right', pady=5, padx=3)

    def update_subplot_nb(self):
        """ Set the subplot number to 1 if it is outside its possible values set """

        figure = self.project.Figures[self.figure_var.get()]
        if self.subplot_nb_var.get() > figure.nb_rows * figure.nb_cols:
            self.subplot_nb_var.set(1)

    def update_b_subplot_nb(self):
        """ Set the subplot number of the band diagram to 1 if it is outside the range of its possible values """
        figure = self.project.Figures[self.b_figure_var.get()]
        if self.b_subplot_nb_var.get() > figure.nb_rows * figure.nb_cols:
            self.b_subplot_nb_var.set(1)

    def close_detailed_pop_window(self):
        """ Close the detailed population window """
        try:
            self.cell_pop_window.destroy()
            self.pop_but.configure(state='normal')
            del self.cell_pop_window
        except AttributeError:
            pass

    def close_band_occupation_window(self):
        """ Close the band occupation window """
        try:
            self.band_window.destroy()
            self.band_but.configure(state='normal')
            del self.band_window
        except AttributeError:
            pass


class Cell_Population_Window(tk.Toplevel):
    """ Give detailed data on the cell population """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title(parent.cell.ID)
        self.resizable(False, False)

        self.parent = parent
        self.cell = parent.cell

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack()

        for f, g, h, i in zip(self.cell.atoms_types, self.cell.nb_atoms,
                              self.cell.atoms_valence, range(len(self.cell.nb_atoms))):
            ttk.Label(self.main_frame, text='There are %s %s atoms with %s valence electrons in the system'
                                            % (g, f, h)).grid(row=i, sticky='w')

        self.bind('<Control-w>', lambda event: self.parent.close_detailed_pop_window())

        ukf.centre_window(self)


class Band_Occupation_Window(tk.Toplevel):
    """ Display the bands energies and occupations of each kpoints"""

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title(parent.cell.ID)
        self.cell = parent.cell
        self.parent = parent

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.tree = ttk.Treeview(self)
        self.tree.pack(side='left', fill='both', expand=True)

        self.yscrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.yscrollbar.pack(side='right', fill='y')

        self.tree['columns'] = ('energy', 'occupation')
        self.tree.column('energy', width=200)
        self.tree.column('occupation', width=100)
        self.tree.heading('energy', text='Energy')
        self.tree.heading('occupation', text='Occupation')
        self.tree.configure(yscrollcommand=self.yscrollbar.set)

        if self.cell.ispin == 1.:
            kpoints_labels = ['kpoint %s' % f for f in range(len(self.cell.bands_data))]
        elif self.cell.ispin == 2.:
            kpoints_labels = ['kpoint %s (spin up)' % f for f in range(1, len(self.cell.bands_data)/2+1)] + \
                             ['kpoint %s (spin down)' % f for f in range(1, len(self.cell.bands_data)/2+1)]

        for kpoint, row, label in zip(self.cell.bands_data, range(1, len(self.cell.bands_data) + 1), kpoints_labels):
            kpoint_id = self.tree.insert('', row, text=label)
            for band, band_nb in zip(np.transpose(kpoint), range(1, len(kpoint[0]) + 1)):
                self.tree.insert(kpoint_id, 'end', text='band ' + str(band_nb), values=(band[0], band[1]))

        self.bind('<Control-w>', lambda event: self.parent.close_band_occupation_window())

        ukf.centre_window(self)


class Colors_Choice_Window(tk.Toplevel):
    """ Window for choosing the color of each item of the plot """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('Colours selector')
        self.resizable(False, False)

        self.cell = parent.cell

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)  # Main ttk frame
        self.main_frame.pack(expand=True, fill='both')

        # ------------------------------------------------ COLORS SELECTOR ---------------------------------------------

        # Items displayed
        if parent.dos_type_var.get() == 'OPAS':
            items_temp = parent.opas_items_choice
        else:
            items_temp = parent.opa_items_choice

        if parent.tot_proj_dos_var.get() is False:
            items = list(np.concatenate([[f + ' %s' %g for g in self.cell.orbitals] for f in items_temp]))
        else:
            items = items_temp

        # Associated colors
        if parent.tot_proj_dos_var.get() is False:
            colors = parent.proj_colors_choice
        else:
            colors = parent.tot_colors_choice

        # dictionary for storing the colors with their associated item
        color_dict = dict(zip(items, colors * int(math.ceil(float(len(items))/len(colors)))))

        def get_color(event):
            """ Retrieve the color associated with the selected item and display it in a label """
            widget = event.widget
            selected = widget.get()
            color = color_dict[selected]
            tk.Label(self.main_frame, text='    ', background=color).grid(row=0, column=1)

        def set_color():
            """ Ask for a color and set it to the current item selected and display it"""
            selected = self.combobox.get()
            if selected == '':
                mb.showwarning('', 'Select an item first', parent=self)
            else:
                color = askcolor(color_dict[selected])
                if color[1] is not None:
                    color_dict[selected] = color[1]
                    tk.Label(self.main_frame, text='    ', background=color[1]).grid(row=0, column=1)

        self.combobox = ttk.Combobox(self.main_frame, values=items, state='readonly')
        self.combobox.grid(row=0, column=0, padx=5, pady=3)
        self.combobox.bind('<<ComboboxSelected>>', get_color)

        tk.Label(self.main_frame, text='    ').grid(row=0, column=1)

        ttk.Button(self.main_frame, text='color', command=set_color).grid(row=0, column=2, padx=5, pady=3)

        # ---------------------------------------------------- BUTTONS -------------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=3)

        def validate():
            """ Save the data in the parent window object and close the window """
            if parent.tot_proj_dos_var.get() is False:
                parent.proj_colors_choice = [color_dict[item] for item in items]
            else:
                parent.tot_colors_choice = [color_dict[item] for item in items]
            self.destroy()

        def set_default_colors():
            """ Set the  """
            if parent.tot_proj_dos_var.get() is False:
                parent.proj_colors_choice = pc.DosPlotParameters(parent.cell).colors_proj
            else:
                parent.tot_colors_choice = pc.DosPlotParameters(parent.cell).colors_tot
            self.destroy()
            Colors_Choice_Window(parent)

        ttk.Button(self.main_button_frame, text='OK', command=validate).pack(side='left', padx=5, pady=3)
        ttk.Button(self.main_button_frame, text='Cancel', command=self.destroy).pack(side='right', padx=5, pady=3)
        ttk.Button(self.main_button_frame, text='Default', command=set_default_colors).pack(side='right', padx=5, pady=3)

        self.bind('<Control-w>', lambda event: self.destroy())

        ukf.centre_window(self)
