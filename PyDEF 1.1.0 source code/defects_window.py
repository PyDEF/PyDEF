""" Defect Label Window
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import ttk
import pickle
import numpy as np
import Tkinter as tk
import pydef_core.defect as pd
import tkMessageBox as mb
import tkFileDialog as fd

import utility_tkinter_functions as ukf


class Defect_Window(tk.Toplevel):
    """ Window for creating defect labels """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('Defect Label')

        self.main_window = parent  # PyDEF main window
        self.parent = parent  # parent window
        self.project = parent.project  # current project

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)  # main ttk frame
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------------- MENU ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.menubar = tk.Menu(self)

        self.defects_menu = tk.Menu(self.menubar, tearoff=0)
        self.defects_menu.add_command(label='Save defect label(s)...', command=self.save_selected_defects,
                                      accelerator='Ctrl+S')
        self.defects_menu.add_command(label='Load defect label(s)...', command=self.open_saved_defects,
                                      accelerator='Ctrl+O')
        self.menubar.add_cascade(label='File', menu=self.defects_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label='About', command=self.parent.open_about_window,
                                   accelerator='Shift+Ctrl+A')
        self.help_menu.add_command(label='Documentation', command=self.parent.open_user_guide,
                                   accelerator='Shift+Ctrl+D')
        self.help_menu.add_command(label='Parameters', command=self.parent.open_parameters_window,
                                   accelerator='Shift+Ctrl+P')
        self.menubar.add_cascade(label='Help', menu=self.help_menu)

        self.config(menu=self.menubar)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------- KEYBOARD SHORCUTS ----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.bind('<Control-s>', lambda event: self.save_selected_defects())
        self.bind('<Control-o>', lambda event: self.open_saved_defects())
        self.bind('<Control-w>', lambda event: self.parent.close_defects_window())

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- INPUT FRAME ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=0, column=0, sticky='nswe', padx=10, pady=3)
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Labels
        ttk.Label(self.input_frame, text='Name').grid(row=0, column=0, padx=5, pady=3)
        ttk.Label(self.input_frame, text='Defect type').grid(row=1, column=0, padx=5, pady=3)

        # Variables
        self.defect_id_var = tk.StringVar()
        self.defect_type_var = tk.StringVar()
        self.defect_id_var.set('automatic')

        # Inputs
        self.id_entry = ttk.Entry(self.input_frame, textvariable=self.defect_id_var)
        self.id_entry.grid(row=0, column=1, sticky='we', padx=5, pady=3)

        self.defect_type_ccb = ttk.Combobox(self.input_frame, values=['Vacancy', 'Interstitial', 'Substitutional'],
                                            textvariable=self.defect_type_var, state='readonly')
        self.defect_type_ccb.grid(row=1, column=1, sticky='we', padx=5, pady=3)

        self.defect_type_ccb.bind('<<ComboboxSelected>>', lambda event: self.display_choices())

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- DEFECTS LIST -----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.defects_list_frame = ttk.Frame(self.main_frame)
        self.defects_list_frame.grid(row=1, column=0, sticky='nswe')
        self.defects_list_frame.grid_rowconfigure(0, weight=1)

        self.yscrollbar = ttk.Scrollbar(self.defects_list_frame, orient='vertical')  # scrollbar for the y-axis
        self.defects_list = tk.Listbox(self.defects_list_frame, selectmode='extended', width=40)

        self.yscrollbar.pack(side='right', fill='y')
        self.defects_list.pack(side='left', fill='both', expand=True)

        self.yscrollbar.config(command=self.defects_list.yview)
        self.defects_list.config(yscrollcommand=self.yscrollbar.set)

        self.defects_list.insert(0, *self.project.Defects)

        def open_defect_properties_window(event):
            """ Open the plot properties window when 'event' happens """
            selection = self.defects_list.curselection()
            if len(selection) != 0:
                defect_id = self.defects_list.get(selection[0])
                Defect_Properties_Window(self, self.project.Defects[defect_id])

        self.defects_list.bind('<Double-Button-1>', open_defect_properties_window)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------- BUTTONS -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.button_frame = ttk.Frame(self.input_frame)
        self.button_frame.grid(row=3, column=0, columnspan=3, sticky='nswe', padx=5, pady=3)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        def create_defect():
            """ Create a Defect object from the value in the fields and add it to the listbox below
            if a Defect object with the same name was previously added, it is overwritten """

            defect_type = self.defect_type_var.get()
            if defect_type == '':
                mb.showwarning('Attention', 'Select first a defect type', parent=self)
                return None

            if hasattr(self, 'atoms_frame') is False:
                mb.showwarning('Attention', 'You must import a VASP calculation first', parent=self)
                return None

            defect_id = self.defect_id_var.get()  # defect ID
            if ',' in defect_id:
                mb.showwarning('Attention', 'The name of a defect label can not contain a comma', parent=self)
                return None

            if defect_type == 'Vacancy' or defect_type == 'Interstitial':

                atom = self.atom1_var.get()  # atom selected
                try:
                    chem_pot = self.chem_pot1_var.get()  # chemical potential set
                except ValueError:
                    mb.showwarning('Attention', 'The chemical potential must be a number')
                    return None

                if atom == '' or chem_pot == '':  # create the Defect object if the field are not vacant
                    mb.showwarning('Attention', 'One of the field is missing', parent=self)
                    return None
                else:
                    defect = pd.Defect(defect_type, [atom], [chem_pot])

            if defect_type == 'Substitutional':

                atom1 = self.atom1_var.get()
                atom2 = self.atom2_var.get()

                try:
                    chem_pot1 = self.chem_pot1_var.get()  # chemical potential set
                except ValueError:
                    mb.showwarning('Attention', 'The chemical potential must be a number')
                    return None

                try:
                    chem_pot2 = self.chem_pot2_var.get()  # chemical potential set
                except ValueError:
                    mb.showwarning('Attention', 'The chemical potential must be a number')
                    return None

                if atom1 == '' or atom2 == '' or chem_pot1 == '' or chem_pot2 == '':
                    mb.showerror('Error', 'One of the field is missing', parent=self)
                    return None
                else:
                    defect = pd.Defect(defect_type, [atom1, atom2], [chem_pot1, chem_pot2])

            if defect_id != '' and defect_id != 'automatic':
                defect.ID = defect_id

            self.load_defect(defect)

        def delete_defect():
            """ Remove the selected defects from the list and from the dictionary """
            selected = self.defects_list.curselection()
            if len(selected) == 0:
                mb.showwarning('Error', 'Select one defect label in the list first', parent=self)
            else:
                defect_id = self.defects_list.get(selected)  # get the ID of the selected defects in the listbox
                self.defects_list.delete(selected)  # remove the defect form the listbox
                self.project.Defects.pop(defect_id)  # remove the defect from the dictionary
                print('Defect "%s" deleted' % defect_id)

        ttk.Button(self.button_frame, text='Create defect label', command=create_defect
                   ).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(self.button_frame, text='Delete defect label', command=delete_defect
                   ).grid(row=0, column=1, padx=5, pady=3)

        ukf.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------ METHODS ---------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def display_choices(self):
        """ Display combobox and entries for choosing the atom(s) affected and the chemical potentials depending
        on the type on the type of defect selected """

        try:
            self.atoms_frame.destroy()  # destroy the atoms frame if it was previously created
        except AttributeError:
            pass

        if self.project.Cells != {}:  # check that there is at least a Cell object in the study
            # all atoms of the project
            all_atoms = np.concatenate([cell.atoms for cell in self.project.Cells.itervalues()])
            atoms_choice = np.sort(list(set(all_atoms)))  # ensemble of choice for the atom(s) affected
            defect_type = self.defect_type_var.get()  # type of the defect
        else:
            return None  # stop the function if there are no Cell object in the project

        # Frame for the affected atom(s) and chemical potential input
        self.atoms_frame = ttk.Frame(self.input_frame)
        self.atoms_frame.grid(row=2, column=0, columnspan=2, sticky='we')
        self.atoms_frame.grid_columnconfigure(0, weight=1)
        self.atoms_frame.grid_columnconfigure(1, weight=1)
        self.atoms_frame.grid_columnconfigure(2, weight=1)

        # Labels
        ttk.Label(self.atoms_frame, text='Atom(s) affected').grid(row=1, column=0)
        ttk.Label(self.atoms_frame, text='Chemical potential (eV)').grid(row=2, column=0)

        # Variables
        self.atom1_var = tk.StringVar()  # atom affected 1
        self.atom2_var = tk.StringVar()  # atom affected 2
        self.chem_pot1_var = tk.DoubleVar()  # chemical potential of atom affected 1
        self.chem_pot2_var = tk.DoubleVar()  # chemical potential of atom affected 2

        def set_chem_pot1():
            """ Change the value of the chemical potential 1 """
            atomic_species = self.atom1_var.get().split(' (')[0]  # atomic species selected
            try:
                chem_pot = float(pd.FERE[atomic_species])
            except KeyError:
                chem_pot = 0.0
            self.chem_pot1_var.set(chem_pot)

        def set_chem_pot2():
            """ Change the value of the chemical potential 2 """
            atomic_species = self.atom2_var.get().split(' (')[0]
            try:
                chem_pot = float(pd.FERE[atomic_species])
            except KeyError:
                chem_pot = 0.0
            self.chem_pot2_var.set(chem_pot)

        if defect_type == 'Vacancy' or defect_type == 'Interstitial':

            if defect_type == 'Vacancy':
                labeltext = 'Atom removed'
            else:
                labeltext = 'Atom added'

            # Label
            ttk.Label(self.atoms_frame, text=labeltext).grid(row=0, column=1, columnspan=2)

            # Atom affected
            self.atom_choice_ccb1 = ttk.Combobox(self.atoms_frame, values=list(atoms_choice),
                                                 textvariable=self.atom1_var, state='readonly', width=7)
            self.atom_choice_ccb1.grid(row=1, column=1, columnspan=2)

            # Chemical potential
            self.chem_pot_entry1 = ttk.Entry(self.atoms_frame, textvariable=self.chem_pot1_var, width=8)
            self.chem_pot_entry1.grid(row=2, column=1, columnspan=2)

            self.atom_choice_ccb1.bind('<<ComboboxSelected>>', lambda event: set_chem_pot1())

        if defect_type == 'Substitutional':

            # Labels
            ttk.Label(self.atoms_frame, text='Atom removed').grid(row=0, column=1)
            ttk.Label(self.atoms_frame, text='Atom added').grid(row=0, column=2)

            # Atoms affected
            self.atom_choice_ccb1 = ttk.Combobox(self.atoms_frame, values=list(atoms_choice),
                                                 textvariable=self.atom1_var, state='readonly', width=7)
            self.atom_choice_ccb1.grid(row=1, column=1)

            self.atom_choice_ccb2 = ttk.Combobox(self.atoms_frame, values=list(atoms_choice),
                                                 textvariable=self.atom2_var, state='readonly', width=7)
            self.atom_choice_ccb2.grid(row=1, column=2)

            self.atom_choice_ccb1.bind('<<ComboboxSelected>>', lambda event1: set_chem_pot1())
            self.atom_choice_ccb2.bind('<<ComboboxSelected>>', lambda event2: set_chem_pot2())

            # Chemical potentials
            self.chem_pot_entry1 = ttk.Entry(self.atoms_frame, textvariable=self.chem_pot1_var, width=8)
            self.chem_pot_entry1.grid(row=2, column=1)

            self.chem_pot_entry2 = ttk.Entry(self.atoms_frame, textvariable=self.chem_pot2_var, width=8)
            self.chem_pot_entry2.grid(row=2, column=2)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------- METHODS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------ DEFECTS ---------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def save_selected_defects(self):
        """ Save the selected defect objects in the list"""
        selection = self.defects_list.curselection()
        if len(selection) == 0:
            mb.showwarning('Error', 'Select at least one defect label from the list first', parent=self)
            return None

        for selected in selection:
            defect_id = self.defects_list.get(selected)
            defect = self.project.Defects[defect_id]
            openfile = fd.asksaveasfile(initialdir=self.project.dd_vasp, defaultextension='.pydef',
                                        initialfile=defect.ID, mode='wb')
            try:
                pickle.dump(defect, openfile, -1)
                openfile.close()
            except AttributeError:
                continue

    def open_saved_defects(self):
        """ Load Defect object(s) from one file or many files """
        files = fd.askopenfiles(mode='rb', defaultextension='.pydef', initialdir=self.project.dd_pydef)
        for f in files:
            defect = pickle.load(f)
            if defect.__class__ is not pd.Defect:
                mb.showerror('Error', 'This file is not a valid file', parent=self)
                continue
            else:
                self.load_defect(defect)

    def load_defect(self, defect):
        """ Load a Defect object 'defect' in the project.
        If the Defect object ID is already in the project, ask if overwrite it """

        if defect.ID in self.project.Defects.keys():  # if there is a Defect object with the same ID already in the project
            overwrite = mb.askyesno('Warning', 'The defect label loaded has the same name has another one in the project.'
                                               '\nDo you want to overwrite it?', parent=self)
            if overwrite is True:
                self.project.Defects[defect.ID] = defect
                print('Defect %s modified' % defect.ID)
            else:
                return None
        else:  # load the defect in the project
            self.defects_list.insert(0, defect.ID)
            self.project.Defects[defect.ID] = defect
            print('Defect %s added' % defect.ID)


class Defect_Properties_Window(tk.Toplevel):
    """ Give information on the defect selected """

    def __init__(self, parent, defect):

        tk.Toplevel.__init__(self, parent)

        self.title(defect.ID)
        self.resizable(False, False)
        self.bind('<Control-w>', lambda event: self.destroy())

        self.project = parent.project
        self.parent = parent

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')

        ttk.Label(self.main_frame, text='Type: %s' % defect.defect_type).grid(row=0, columnspan=2, padx=5, pady=3)

        if defect.defect_type == 'Vacancy' or defect.defect_type == 'Interstitial':
            if defect.defect_type == 'Vacancy':
                textlabel = 'Atom removed'
            else:
                textlabel = 'Atom added'

            self.atom_frame_label = ttk.Label(self, text=textlabel, font="-weight bold")
            self.atom_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.atom_frame_label, labelanchor='n')
            self.atom_frame.grid(row=1, padx=5, pady=3)

            ttk.Label(self.atom_frame, text='Atom: %s' % defect.atom[0]).grid(row=0)
            ttk.Label(self.atom_frame, text='Chemical potential: %s eV' % defect.chem_pot_input[0]).grid(row=1)

        if defect.defect_type == 'Substitutional':

            self.atom_frame1_label = ttk.Label(self, text='Atom removed', font="-weight bold")
            self.atom_frame1 = ttk.LabelFrame(self.main_frame, labelwidget=self.atom_frame1_label, labelanchor='n')
            self.atom_frame1.grid(row=1, column=0, padx=5, pady=3)

            ttk.Label(self.atom_frame1, text='Atom: %s' % defect.atom[0]).grid(row=0)
            ttk.Label(self.atom_frame1, text='Chemical potential: %s eV' % defect.chem_pot_input[0]).grid(row=1)

            self.atom_frame2_label = ttk.Label(self, text='Atom added', font="-weight bold")
            self.atom_frame2 = ttk.LabelFrame(self.main_frame, labelwidget=self.atom_frame2_label, labelanchor='n')
            self.atom_frame2.grid(row=1, column=1, padx=5, pady=3)

            ttk.Label(self.atom_frame2, text='Atom: %s' % defect.atom[1]).grid(row=0)
            ttk.Label(self.atom_frame2, text='Chemical potential: %s eV' % defect.chem_pot_input[1]).grid(row=1)

        ukf.centre_window(self)
