""" Defect Study Window
    version: DevB1
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import ttk
import pickle
import Tkinter as tk
import tkMessageBox as mb
import tkFileDialog as fd
import numpy as np

import pydef_core.cell as cc
import pydef_core.defect_study as ds
import pydef_core.basic_functions as bf

import utility_tkinter_functions as utf
import items_choice_window as icw
import figures_window as pfw
import utility_tkinter_functions as utk
import pydef_images


class Defect_Study_Window(tk.Toplevel):
    """ Window for creating Defect_Study objects """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('Defect Studies')

        self.main_window = parent  # PyDEF main window
        self.parent = parent  # parent window
        self.project = parent.project  # current project

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        style = ttk.Style()
        style.configure('Bold.TCheckbutton', font='-weight bold')

        self.main_frame = ttk.Frame(self)  # main ttk frame
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- MENUBAR --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.menubar = tk.Menu(self)

        self.defect_studies_menu = tk.Menu(self.menubar, tearoff=0)
        self.defect_studies_menu.add_command(label='Save defect studies...', command=self.save_selected_defect_studies,
                                             accelerator='Ctrl+S')
        self.defect_studies_menu.add_command(label='Load defect studies...', command=self.open_saved_defect_studies,
                                             accelerator='Ctrl+O')
        self.menubar.add_cascade(label='File', menu=self.defect_studies_menu)

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
        # ---------------------------------------------- KEYBOARD SHORTCUTS --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.bind('<Control-s>', lambda event: self.save_selected_defect_studies())
        self.bind('<Control-o>', lambda event: self.open_saved_defect_studies())
        self.bind('<Control-w>', lambda event: self.parent.close_defect_studies_window())

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------- INPUT ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=0, column=0, sticky='nswe', padx=10)
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Variables
        self.defect_study_id_var = tk.StringVar()  # Defect Study ID
        self.host_cell_var = tk.StringVar()  # Host cell ID
        self.defects_var = tk.StringVar()  # Defects IDs (separated with a comma)
        self.gaps_var = tk.StringVar()  # gaps separated with a comma
        self.defect_study_id_var.set('automatic')

        # ID
        ttk.Label(self.input_frame, text='Name', width=15, anchor='center'
                  ).grid(row=0, column=0, padx=3, pady=3)
        ttk.Entry(self.input_frame, textvariable=self.defect_study_id_var
                  ).grid(row=0, column=1, sticky='we', padx=3, pady=3)

        # Host Cell choice
        ttk.Label(self.input_frame, text='Host cell').grid(row=1, column=0)
        self.host_cell_ccb = ttk.Combobox(self.input_frame, values=self.project.Cells.keys(),
                                          textvariable=self.host_cell_var, state='readonly')
        self.host_cell_ccb.grid(row=1, column=1, sticky='we', padx=3, pady=3)

        # Defect(s) choice
        def choose_defect():
            """ Open a window to choose one or few defect(s) for the study """
            if self.defects_var.get() != '':
                items_on = self.defects_var.get().split(',')
            else:
                items_on = []
            self.defect_window = icw.Items_Choice_Window(self, self.project.Defects, items_on,
                                                         self.defects_var, 'In', 'Out')
            self.defect_window.grab_set()
            self.wait_window(self.defect_window)
            self.defect_window.grab_release()

        self.defect_button = ttk.Button(self.input_frame, text='Defect(s)', command=choose_defect)
        self.defect_button.grid(row=2, column=0, padx=3, pady=3)
        self.defects_entry = ttk.Entry(self.input_frame, textvariable=self.defects_var, state='disabled')
        self.defects_entry.grid(row=2, column=1, sticky='we', padx=3, pady=3)

        # Gaps input
        def open_set_gaps_window():
            """ Open the gap input window """
            self.gap_input_window = Gap_Input_Window(self, self.gaps_var)
            self.gap_input_window.grab_set()
            self.wait_window(self.gap_input_window)
            self.gap_input_window.grab_release()

        ttk.Button(self.input_frame, text='Gaps', command=open_set_gaps_window
                   ).grid(row=3, column=0, padx=3, pady=3)
        ttk.Entry(self.input_frame, textvariable=self.gaps_var, state='disabled'
                  ).grid(row=3, column=1, sticky='we', padx=3, pady=3)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- BUTTONS --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, sticky='nswe', padx=10, pady=5)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        def create_defect_study():
            """ Create a defect study and add it to the project """

            # Host Cell
            host_cell_id = self.host_cell_var.get()
            if host_cell_id != '':
                host_cell = self.project.Cells[host_cell_id]
            else:
                mb.showwarning('Error', 'A host cell is required', parent=self)
                return None

            # Defects
            defects_ids = self.defects_var.get().split(',')
            if defects_ids != ['']:
                defects = [self.project.Defects[defect_id] for defect_id in defects_ids]
            else:
                mb.showwarning('Error', 'At least one defect label is required', parent=self)
                return None

            # Gaps
            gaps_input = self.gaps_var.get().split(';')
            if gaps_input != ['']:
                gaps = []
                for gap_id in gaps_input:
                    gap_value = gap_id.split(' (')[-1][:-4]
                    gap_name = gap_id[:gap_id.find(gap_value) - 1].strip()
                    gaps.append(gap_value)
                    gaps.append(gap_name)
            else:
                gaps = ['']

            # ----------------------------------------------- CORRECTIONS ----------------------------------------------

            # VBM & PHS CORRECTIONS
            if self.phs_corr_var.get() is True or self.vbm_corr_var.get() is True:

                # Host Cell B
                host_cell_b_id = self.host_cell_b_var.get()
                if host_cell_b_id != 'None':
                    host_cell_b = self.project.Cells[host_cell_b_id]
                else:
                    host_cell_b = host_cell

                # Gap correction inputs
                try:
                    de_vbm_input = self.de_vbm_input_var.get()
                    de_cbm_input = self.de_cbm_input_var.get()
                except ValueError:
                    mb.showwarning('Error', 'The correction of the CBM and VBM must be numbers', parent=self)
                    return None
            else:
                host_cell_b = host_cell
                de_vbm_input = 0.0
                de_cbm_input = 0.0

            # MAKOV-PAYNE CORRECTION
            if self.mp_corr_var.get() is True:

                # Geometry
                geometry = self.geometry_var.get()
                if geometry == '':
                    mb.showwarning('Error', 'Select a geometry for the host cell', parent=self)
                    return None

                # Relative permittivity
                try:
                    rel_perm = self.rel_perm.get()
                except ValueError:
                    mb.showerror('Error', 'The relative permittivity must be a number', parent=self)
                    return None
                if rel_perm == 0.0:
                    mb.showerror('Error', 'The relative permittivity can not be zero', parent=self)
                    return None

                # Makov-Payne ratio
                try:
                    mk_1_1 = self.mk_1_1_var.get()
                except ValueError:
                    mb.showerror('Error', 'The Makov-Payne ratio must be a number', parent=self)
                    return None
            else:
                geometry = None
                rel_perm = None
                mk_1_1 = None

            defect_study = ds.Defect_Study(host_cell, host_cell_b, defects, geometry, rel_perm, mk_1_1, de_vbm_input,
                                           de_cbm_input, gaps, self.pa_corr_var.get(), self.mb_corr_var.get(),
                                           self.phs_corr_var.get(), self.vbm_corr_var.get(), self.mp_corr_var.get())

            defect_study_id = self.defect_study_id_var.get()
            if defect_study_id != '' and defect_study_id != 'automatic':
                defect_study.ID = defect_study_id

            self.load_defect_study(defect_study)

        def delete_defect_study():
            """ Remove the selected defect studies from the list and from the dictionary """
            selected = self.defect_studies_list.curselection()
            if len(selected) == 0:
                mb.showerror('Error', 'Please select at least one defect study in the list first', parent=self)
                return None
            defect_study_id = self.defect_studies_list.get(selected[0])
            if mb.askyesno('', 'Are you sure you want to delete the defect study "%s"' % defect_study_id):
                self.defect_studies_list.delete(selected[0])
                self.project.Defect_Studies.pop(defect_study_id)
                print('Defect Study "%s" deleted' % defect_study_id)

        ttk.Button(self.button_frame, text='Create a defect study', command=create_defect_study).grid(row=0, column=0)
        ttk.Button(self.button_frame, text='Delete defect studies', command=delete_defect_study).grid(row=0, column=1)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- CORRECTIONS ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.corr_frame_label = ttk.Label(self, text='Corrections', font=('', '16', 'bold'))
        self.corr_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.corr_frame_label, labelanchor='n')
        self.corr_frame.grid(row=1, column=0, sticky='nswe', padx=10, pady=3)
        self.corr_frame.grid_columnconfigure(0, weight=1)

        # Variables
        self.host_cell_b_var = tk.StringVar()  # Host cell B ID
        self.geometry_var = tk.StringVar()  # geometry of the host cell
        self.rel_perm = tk.DoubleVar()  # relative permittivity
        self.mk_1_1_var = tk.DoubleVar()  # makov-payne correction for e_r=1 and q=1

        # Corrections
        self.vbm_corr_var = tk.BooleanVar()
        self.pa_corr_var = tk.BooleanVar()
        self.mb_corr_var = tk.BooleanVar()
        self.phs_corr_var = tk.BooleanVar()
        self.mp_corr_var = tk.BooleanVar()

        self.vbm_corr_var.set(True)
        self.pa_corr_var.set(True)
        self.mb_corr_var.set(True)
        self.phs_corr_var.set(True)
        self.mp_corr_var.set(True)

        # ------------------------------------------- VBM & PHS CORRECTIONS --------------------------------------------

        self.de_vbm_input_var = tk.DoubleVar()  # input correction of the VBM
        self.de_cbm_input_var = tk.DoubleVar()  # input correction of the CBM
        self.tot_de_vbm_var = tk.DoubleVar()  # Total correction of the VBM
        self.tot_de_cbm_var = tk.DoubleVar()  # Total correction of the CBM

        def enable_gap_corr_frame():
            """ Enable the gap correction frame if the two checkbuttons are checked and disable it if it is not """
            if self.vbm_corr_var.get() is False and self.phs_corr_var.get() is False:
                self.host_cell_b_ccb.configure(state='disabled')
                self.add_de_vbm.configure(state='disabled')
                self.add_de_cbm.configure(state='disabled')
            else:
                self.host_cell_b_ccb.configure(state='readonly')
                self.add_de_vbm.configure(state='enabled')
                self.add_de_cbm.configure(state='enabled')

        # Checkboxes
        self.gap_corr_frame_labelframe = ttk.Frame(self)
        ttk.Checkbutton(self.gap_corr_frame_labelframe, text='VBM correction', variable=self.vbm_corr_var, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=enable_gap_corr_frame).pack(side='left')
        ttk.Checkbutton(self.gap_corr_frame_labelframe, text='PHS correction', variable=self.phs_corr_var, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=enable_gap_corr_frame).pack(side='right')

        # LabelFrame
        self.gap_corr_frame = ttk.LabelFrame(self.corr_frame, labelwidget=self.gap_corr_frame_labelframe,
                                             labelanchor='n')
        self.gap_corr_frame.grid(row=3, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        self.gap_corr_frame.grid_columnconfigure(1, weight=1)

        # Host Cell B
        ttk.Label(self.gap_corr_frame, text='Host cell (better gap)').grid(row=0, column=0)
        self.host_cell_b_ccb = ttk.Combobox(self.gap_corr_frame, values=self.project.Cells.keys() + ['None'],
                                            textvariable=self.host_cell_b_var, state='readonly')
        self.host_cell_b_var.set('None')
        self.host_cell_b_ccb.grid(row=0, column=1, sticky='we', padx=3, pady=3)

        # VBM & CBM correction frames
        self.vbm_corr_frame = ttk.Frame(self.gap_corr_frame)
        self.vbm_corr_frame.grid(row=1, column=0, columnspan=2)
        self.cbm_corr_frame = ttk.Frame(self.gap_corr_frame)
        self.cbm_corr_frame.grid(row=2, column=0, columnspan=2)

        ttk.Label(self.vbm_corr_frame, text='Addl. corr. to the VBM energy: +').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='Addl. corr. to the CBM energy: +').pack(side='left')

        self.add_de_vbm = ttk.Entry(self.vbm_corr_frame, textvariable=self.de_vbm_input_var, width=6)
        self.add_de_vbm.pack(side='left')
        self.add_de_cbm = ttk.Entry(self.cbm_corr_frame, textvariable=self.de_cbm_input_var, width=6)
        self.add_de_cbm.pack(side='left')

        ttk.Label(self.vbm_corr_frame, text='eV =').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='eV =').pack(side='left')

        ttk.Entry(self.vbm_corr_frame, textvariable=self.tot_de_vbm_var, state='disabled', width=6).pack(side='left')
        ttk.Entry(self.cbm_corr_frame, textvariable=self.tot_de_cbm_var, state='disabled', width=6).pack(side='left')

        ttk.Label(self.vbm_corr_frame, text='eV').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='eV').pack(side='left')

        def get_tot_gap_corr(event):
            """ Retrieve the total VBM correction """
            try:
                host_cell = self.project.Cells[self.host_cell_var.get()]
                host_cell_b = self.project.Cells[self.host_cell_b_var.get()]

                de_vbm = host_cell_b.VBM - host_cell.VBM
                de_cbm = host_cell_b.CBM - host_cell.CBM
            except KeyError:
                de_vbm = 0.0
                de_cbm = 0.0

            try:
                de_vbm_input = self.de_vbm_input_var.get()
                de_cbm_input = self.de_cbm_input_var.get()
            except ValueError:
                de_vbm_input = 0.0
                de_cbm_input = 0.0

            self.tot_de_vbm_var.set(de_vbm + de_vbm_input)
            self.tot_de_cbm_var.set(de_cbm + de_cbm_input)

        self.host_cell_b_ccb.bind('<<ComboboxSelected>>', get_tot_gap_corr)
        self.add_de_vbm.bind('<KeyRelease>', get_tot_gap_corr)  # update the VBM correction when a number is pressed
        self.add_de_cbm.bind('<KeyRelease>', get_tot_gap_corr)  # update the CBM correction when a number is pressed

        # --------------------------------------- POTENTIAL ALIGNMENT CORRECTION ---------------------------------------

        ttk.Checkbutton(self.corr_frame, text='Potential alignment correction', onvalue=True, offvalue=False,
                        variable=self.pa_corr_var, style='Bold.TCheckbutton'
                        ).grid(row=4, column=0, columnspan=2, pady=5)

        # ------------------------------------------ MOSS-BURSTEIN CORRECTION ------------------------------------------

        ttk.Checkbutton(self.corr_frame, text='Moss-Burstein correction', onvalue=True, offvalue=False,
                        variable=self.mb_corr_var, style='Bold.TCheckbutton'
                        ).grid(row=5, column=0, columnspan=2, pady=5)

        # ------------------------------------------- MAKOV-PAYNE CORRECTION -------------------------------------------

        def enable_mp_frame():
            """ Enable the Makov-Payne correction frame if the two checkbuttons are checked
             and disable it if it is not """
            if self.mp_corr_var.get() is True:
                utf.enable_frame(self.mp_frame)
            else:
                utf.disable_frame(self.mp_frame)

        self.mp_frame_label = ttk.Checkbutton(self, text='Makov-Payne correction', variable=self.mp_corr_var,
                                              onvalue=True, offvalue=False, style='Bold.TCheckbutton',
                                              command=enable_mp_frame)
        self.mp_frame = ttk.LabelFrame(self.corr_frame, labelwidget=self.mp_frame_label, labelanchor='n')
        self.mp_frame.grid(row=6, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        self.mp_frame.grid_columnconfigure(0, weight=1)

        # Geometry
        ttk.Label(self.mp_frame, text='Geometry of the host cell').grid(row=0, column=0)
        ttk.Combobox(self.mp_frame, values=['sc', 'fcc', 'bcc', 'hcp', 'other'], textvariable=self.geometry_var,
                     state='readonly', width=5).grid(row=0, column=1)

        # Relative permittivity
        ttk.Label(self.mp_frame, text='Relative permittivity').grid(row=1, column=0)
        ttk.Entry(self.mp_frame, textvariable=self.rel_perm, width=7).grid(row=1, column=1)

        # Makov-Payne correction for e_r=1 and q=1
        self.mp_ratio_image = tk.PhotoImage(data=pydef_images.mp_ratio)
        ttk.Label(self.mp_frame, text='Value of the ratio (eV)', image=self.mp_ratio_image, compound='right'
                  ).grid(row=2, column=0)
        ttk.Entry(self.mp_frame, textvariable=self.mk_1_1_var, width=7).grid(row=2, column=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------- DEFECT STUDIES LIST FRAME ----------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.defect_studies_list_frame = ttk.Frame(self.main_frame)
        self.defect_studies_list_frame.grid(row=3, column=0, sticky='nswe')
        self.defect_studies_list_frame.grid_rowconfigure(0, weight=1)

        self.yscrollbar = ttk.Scrollbar(self.defect_studies_list_frame, orient='vertical')  # scrollbar for the y-axis
        self.defect_studies_list = tk.Listbox(self.defect_studies_list_frame, selectmode='extended', width=40)

        self.yscrollbar.pack(side='right', fill='y')
        self.defect_studies_list.pack(side='left', fill='both', expand=True)

        self.yscrollbar.config(command=self.defect_studies_list.yview)
        self.defect_studies_list.config(yscrollcommand=self.yscrollbar.set)

        self.defect_studies_list.insert(0, *self.project.Defect_Studies)

        def open_defect_study_properties_window(event):
            """ Open the defect study properties window when a defect study is double clicked in the list """
            selection = self.defect_studies_list.curselection()
            if len(selection) != 0:
                defect_study_id = self.defect_studies_list.get(selection[0])
                Defect_Study_Properties_Window(self, self.project.Defect_Studies[defect_study_id])

        self.defect_studies_list.bind('<Double-Button-1>', open_defect_study_properties_window)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------- DEFECT STUDIES FUNCTIONS BUTTONS -------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.button_frame2 = ttk.Frame(self.main_frame)
        self.button_frame2.grid(row=4, column=0, sticky='nswe', padx=10, pady=5)
        self.button_frame2.grid_columnconfigure(0, weight=1, uniform='uni')
        self.button_frame2.grid_columnconfigure(1, weight=1, uniform='uni')

        def plot_dos():
            """ Plot the DOS of each cells in each Defect_Study objects selected in the list """
            selection = self.defect_studies_list.curselection()
            if len(selection) == 0:
                mb.showerror('Error', 'Select a defect study in the list', parent=self)
            else:
                for selected in selection:
                    defect_study_id = self.defect_studies_list.get(selected)
                    defect_study = self.project.Defect_Studies[defect_study_id]
                    defect_study.plot_dos()

        def plot_formation_energy():
            """ Plot the formation energy of each Defect_Study objects selected in the list """
            selection = self.defect_studies_list.curselection()
            if len(selection) == 0:
                mb.showerror('Error', 'Select a defect study in the list', parent=self)
            else:
                for selected in selection:
                    defect_study_id = self.defect_studies_list.get(selected)
                    defect_study = self.project.Defect_Studies[defect_study_id]
                    print(defect_study.ID)
                    try:
                        defect_study.plot_formation_energy()
                    except IndexError:
                        mb.showerror('Error', 'You must indicate at least one defect cell before.'
                                              'To do that, double click on the defect study', parent=self)

        def plot_transition_levels():
            """ Plot the transition levels of each Defect_Study objects selected in the list """
            selection = self.defect_studies_list.curselection()
            if len(selection) == 0:
                mb.showerror('Error', 'Select a defect study in the list', parent=self)
            else:
                for selected in selection:
                    defect_study_id = self.defect_studies_list.get(selected)
                    defect_study = self.project.Defect_Studies[defect_study_id]
                    try:
                        defect_study.plot_transition_levels()
                    except IndexError:
                        mb.showerror('Error', 'You must indicate at least one defect cell before.'
                                              'To do that, double click on the defect study', parent=self)

        def export_results():
            """ Export the results of each Defect_Study object selected in the list """
            selection = self.defect_studies_list.curselection()
            if len(selection) == 0:
                mb.showerror('Error', 'Select a defect study in the list', parent=self)
            else:
                for selected in selection:
                    defect_study_id = self.defect_studies_list.get(selected)
                    defect_study = self.project.Defect_Studies[defect_study_id]
                    ofile = fd.asksaveasfile(parent=self, mode='w', defaultextension='.txt')
                    if ofile is not None:
                        try:
                            defect_study.save_results(ofile)
                        except AttributeError:
                            mb.showerror('Error', 'You must indicate at least one defect cell before.'
                                                  'To do that, double click on the defect study', parent=self)
                    else:
                        continue

        ttk.Button(self.button_frame2, text='Plot DOS', command=plot_dos
                   ).grid(row=1, column=0, sticky='we')
        ttk.Button(self.button_frame2, text='Plot defect formation energy', command=plot_formation_energy
                   ).grid(row=0, column=0, sticky='we')
        ttk.Button(self.button_frame2, text='Plot transition levels', command=plot_transition_levels
                   ).grid(row=0, column=1, sticky='we')
        ttk.Button(self.button_frame2, text='Export results', command=export_results
                   ).grid(row=1, column=1, sticky='we')

        utk.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------- METHODS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------- DEFECT STUDIES -------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def load_defect_study(self, defect_study):
        """ Load a Defect Study object 'defect_study' in the project.
        If the Defect Study object ID is already in the project, ask if overwrite it """

        if defect_study.ID in self.project.Defect_Studies.keys():
            overwrite = mb.askyesno('Warning', 'The defect study loaded has the same ID has another one in the project.'
                                               '\nDo you want to overwrite it?', parent=self)
            if overwrite is True:
                self.project.Defect_Studies[defect_study.ID] = defect_study
                print('Defect Study %s modified' % defect_study.ID)
            else:
                return None
        else:  # load the defect in the project
            self.defect_studies_list.insert(0, defect_study.ID)
            self.project.Defect_Studies[defect_study.ID] = defect_study
            print('Defect %s added' % defect_study.ID)

        # Load the figure and update the figures combobox
        self.figure_window = pfw.Figure_Window(self)
        self.figure_window.load_figure(defect_study.fpp.figure)
        self.figure_window.load_figure(defect_study.tpp.figure)
        self.figure_window.destroy()

    def save_selected_defect_studies(self):
        """ Save the selected Defect Study object(s) in the list"""
        selection = self.defect_studies_list.curselection()
        if len(selection) == 0:
            mb.showwarning('Error', 'Select at least one defect study from the list first', parent=self)
            return None

        for selected in selection:
            defect_study_id = self.defect_studies_list.get(selected)
            defect_study = self.project.Defect_Studies[defect_study_id]
            openfile = fd.asksaveasfile(parent=self, initialdir=self.project.dd_vasp, defaultextension='.pydef',
                                        initialfile=defect_study.ID, mode='wb')
            try:
                pickle.dump(defect_study, openfile, -1)
                openfile.close()
            except AttributeError:
                continue

    def open_saved_defect_studies(self):
        """ Load Defect Study object(s) from one file or many files """
        files = fd.askopenfiles(parent=self, mode='rb', defaultextension='.pydef')
        for f in files:
            defect = pickle.load(f)
            if defect.__class__ is not ds.Defect_Study:
                mb.showerror('Error', 'This file is not a valid file', parent=self)
                continue
            else:
                self.load_defect_study(defect)


class Defect_Study_Properties_Window(tk.Toplevel):
    """ Properties of a defect study object """

    def __init__(self, parent, defect_study):

        tk.Toplevel.__init__(self, parent)

        self.title(defect_study.ID)
        self.bind('<Control-w>', lambda event: self.destroy())

        self.main_window = parent.main_window
        self.project = parent.project
        self.defect_study = defect_study

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.cell_notebook = ttk.Notebook(self)
        self.cell_notebook.pack(fill='both', expand=True)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------- PROPERTIES & DEFECT CELL STUDIES -------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.properties_defect_cell_frame = ttk.Frame(self.cell_notebook)
        self.cell_notebook.add(self.properties_defect_cell_frame, text='Properties')
        self.properties_defect_cell_frame.grid_columnconfigure(0, weight=1)
        self.properties_defect_cell_frame.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------- PROPERTIES ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.properties_frame_label = ttk.Label(self, text='Properties',  font='-weight bold')
        self.properties_frame = ttk.LabelFrame(self.properties_defect_cell_frame,
                                               labelwidget=self.properties_frame_label)
        self.properties_frame.grid(row=0, column=0, sticky='nswe', padx=5, pady=5)

        ttk.Label(self.properties_frame, text='Host cell: %s' % self.defect_study.Host_Cell.ID
                  ).grid(row=0, column=0, sticky='w')
        ttk.Label(self.properties_frame, text='Defects: %s' % ' & '.join([f.ID for f in self.defect_study.DefectS])
                  ).grid(row=1, column=0, sticky='w')
        ttk.Label(self.properties_frame, text='Gaps: %s' % '\n           '.join(
            [f + ': ' + str(self.defect_study.gaps[f]) + ' eV' for f in self.defect_study.gaps.keys()])
                  ).grid(row=2, column=0, sticky='w')

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- CORRECTIONS ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.corrections_frame_label = ttk.Label(self, text='Corrections', font='-weight bold')
        self.corrections_frame = ttk.LabelFrame(self.properties_frame, labelwidget=self.corrections_frame_label)
        self.corrections_frame.grid(row=3, column=0, sticky='nswe', padx=5, pady=5)

        self.phs_corr_var = tk.BooleanVar()
        self.vbm_corr_var = tk.BooleanVar()
        self.mb_corr_var = tk.BooleanVar()
        self.mp_corr_var = tk.BooleanVar()
        self.pa_corr_var = tk.BooleanVar()

        self.phs_corr_var.set(self.defect_study.phs_correction)
        self.vbm_corr_var.set(self.defect_study.vbm_correction)
        self.mb_corr_var.set(self.defect_study.moss_burstein_correction)
        self.mp_corr_var.set(self.defect_study.makov_payne_correction)
        self.pa_corr_var.set(self.defect_study.potential_alignment_correction)

        # ------------------------------------------------ GAP CORRECTION ----------------------------------------------

        # Checkboxes

        self.gap_corr_frame_label_frame = ttk.Frame(self.corrections_frame)
        ttk.Checkbutton(self.gap_corr_frame_label_frame, text='VBM correction', variable=self.vbm_corr_var,
                        onvalue=True, offvalue=False, style='Bold.TCheckbutton',
                        state='disabled').pack(side='left')
        ttk.Checkbutton(self.gap_corr_frame_label_frame, text='PHS correction', variable=self.phs_corr_var,
                        onvalue=True, offvalue=False, style='Bold.TCheckbutton',
                        state='disabled').pack(side='right')

        if self.vbm_corr_var.get() is True or self.phs_corr_var.get() is True:
            self.gap_corr_frame = ttk.LabelFrame(self.corrections_frame, labelwidget=self.gap_corr_frame_label_frame,
                                                 labelanchor='n')
            self.gap_corr_frame.grid(row=0, column=0, sticky='we', padx=5, pady=5)
            self.gap_corr_frame.grid_columnconfigure(1, weight=1)

            # Content
            if self.defect_study.Host_Cell_B != self.defect_study.Host_Cell:
                ttk.Label(self.gap_corr_frame, text='Host cell (better gap): %s' % self.defect_study.Host_Cell_B.ID
                          ).grid(row=0, column=0, sticky='w')
            else:
                ttk.Label(self.gap_corr_frame, text='Host cell (better gap): None'
                          ).grid(row=0, column=0, sticky='w')

            ttk.Label(self.gap_corr_frame, text='Addl. corr. VBM: %s eV' % self.defect_study.DE_VBM_input
                      ).grid(row=1, column=0, sticky='w')
            ttk.Label(self.gap_corr_frame, text='Addl. corr. CBM: %s eV' % self.defect_study.DE_CBM_input
                      ).grid(row=2, column=0, sticky='w')
            ttk.Label(self.gap_corr_frame, text='Tot. corr. VBM: %s eV' % self.defect_study.DE_VBM
                      ).grid(row=3, column=0, sticky='w')
            ttk.Label(self.gap_corr_frame, text='Tot. corr. CBM: %s eV' % self.defect_study.DE_CBM
                      ).grid(row=4, column=0, sticky='w')
        else:
            self.gap_corr_frame_label_frame.grid(row=0, column=0, sticky='we', padx=5, pady=5)

        # --------------------------------------- POTENTIAL ALIGNMENT CORRECTION ---------------------------------------

        ttk.Checkbutton(self.corrections_frame, text='Potential alignment correction', onvalue=True, offvalue=False,
                        variable=self.pa_corr_var, style='Bold.TCheckbutton', state='disabled'
                        ).grid(row=1, column=0, pady=5)

        # ------------------------------------------ MOSS-BURSTEIN CORRECTION ------------------------------------------

        ttk.Checkbutton(self.corrections_frame, text='Moss-Burstein correction', onvalue=True, offvalue=False,
                        variable=self.mb_corr_var, style='Bold.TCheckbutton', state='disabled'
                        ).grid(row=2, column=0, pady=5)

        # ------------------------------------------- MAKOV-PAYNE CORRECTION -------------------------------------------
        if self.mp_corr_var.get() is True:
            self.mp_frame_label = ttk.Checkbutton(self, text='Makov-Payne correction', variable=self.mp_corr_var,
                                                  onvalue=True, offvalue=False, style='Bold.TCheckbutton',
                                                  state='disabled')

            self.mp_frame = ttk.LabelFrame(self.corrections_frame, labelwidget=self.mp_frame_label, labelanchor='n')
            self.mp_frame.grid(row=3, column=0, sticky='we', padx=5, pady=5)

            ttk.Label(self.mp_frame, text='Geometry: %s' % self.defect_study.geometry
                      ).grid(row=0, column=0, sticky='w')
            ttk.Label(self.mp_frame, text='Relative permittivity: %s' % self.defect_study.e_r
                      ).grid(row=1, column=0, sticky='w')

            # Ratio
            self.ratio_frame = ttk.Frame(self.mp_frame)
            self.ratio_frame.grid(row=2, column=0, sticky='nswe')
            self.mp_ratio_image = tk.PhotoImage(data=pydef_images.mp_ratio)
            ttk.Label(self.ratio_frame, text='Value of the ratio', image=self.mp_ratio_image, compound='right'
                      ).pack(side='left')
            ttk.Label(self.ratio_frame, text=': %s eV' % self.defect_study.mk_1_1
                      ).pack(side='left')

        else:
            ttk.Checkbutton(self.corrections_frame, text='Makov-Payne correction', variable=self.mp_corr_var,
                            onvalue=True, offvalue=False, style='Bold.TCheckbutton', state='disabled'
                            ).grid(row=3, column=0, pady=5)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- DEFECT CELL STUDY --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.defect_cell_frame_label = ttk.Label(self, text='Defect cells', font='-weight bold')
        self.defect_cell_frame = ttk.LabelFrame(self.properties_defect_cell_frame,
                                                labelwidget=self.defect_cell_frame_label)
        self.defect_cell_frame.grid(row=0, column=1, sticky='nswe', padx=5, pady=5)
        self.defect_cell_frame.grid_columnconfigure(1, weight=1)

        self.defect_cell_var = tk.StringVar()
        self.radius_var = tk.DoubleVar()
        self.radius_var.set(5.0)

        ttk.Label(self.defect_cell_frame, text='Defect cell').grid(row=0, column=0, padx=5, pady=3)
        self.defect_cell_ccb = ttk.Combobox(self.defect_cell_frame, textvariable=self.defect_cell_var, state='readonly')
        self.defect_cell_ccb.grid(row=0, column=1, sticky='we', padx=5, pady=3)
        self.populate_defect_cells_ccb()

        # PHS correction
        if self.defect_study.phs_correction is True:
            ttk.Label(self.defect_cell_frame, text='Nb electrons in CB').grid(row=1, column=0, padx=5, pady=3)
            ttk.Label(self.defect_cell_frame, text='Nb holes in VB').grid(row=2, column=0, padx=5, pady=3)

            self.z_e_spinb = tk.Spinbox(self.defect_cell_frame, from_=0, to=99)
            self.z_e_spinb.grid(row=1, column=1, sticky='we', padx=5, pady=3)
            self.z_h_spinb = tk.Spinbox(self.defect_cell_frame, from_=0, to=99)
            self.z_h_spinb.grid(row=2, column=1, sticky='we', padx=5, pady=3)

        # Potential alignment
        if self.defect_study.potential_alignment_correction is True:
            ttk.Label(self.defect_cell_frame, text=u'Spheres radius (\u212B)').grid(row=3, column=0, padx=5, pady=3)
            ttk.Entry(self.defect_cell_frame, textvariable=self.radius_var).grid(row=3, column=1, sticky='we',
                                                                                 padx=5, pady=3)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------- DEFECT CELL STUDY BUTTONS ----------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.button_frame = ttk.Frame(self.defect_cell_frame)
        self.button_frame.grid(row=5, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        def add_defect_cell_study():
            """ Add the Defect Cell Study to the Defect Study object"""

            # Defect Cell
            defect_cell_id = self.defect_cell_var.get()
            if defect_cell_id == '':
                mb.showerror('Error', 'Select a cell', parent=self)
                return None
            else:
                defect_cell = self.project.Cells[defect_cell_id]

            # Number of qp in bands
            if self.defect_study.phs_correction is True:
                z_e = float(self.z_e_spinb.get())
                z_h = float(self.z_h_spinb.get())
            else:
                z_e = None
                z_h = None

            if self.defect_study.potential_alignment_correction is True:
                radius = self.radius_var.get()
            else:
                radius = None

            try:
                defect_cell_study = ds.Defect_Cell_Study(defect_study.Host_Cell, defect_cell, defect_study.DefectS,
                                                         radius, z_e, z_h, defect_study.geometry, defect_study.e_r,
                                                         defect_study.mk_1_1, defect_study.DE_VBM, defect_study.DE_CBM,
                                                         defect_study.potential_alignment_correction,
                                                         defect_study.moss_burstein_correction,
                                                         defect_study.phs_correction, defect_study.vbm_correction,
                                                         defect_study.makov_payne_correction)
            except bf.PydefDefectCellError:
                mb.showerror('Error', 'Attention, the selected defect cell has not the same cristal parameters has '
                                      'the host cell')
                return None

            if defect_cell.ID in self.defect_study.defect_cell_studies.keys():
                overwrite = mb.askyesno('Attention', 'A defect cell with the same ID has already been added '
                                                     'to this study\nDo you want to overwrite it?', parent=self)
                if overwrite is True:
                    self.defect_study.defect_cell_studies[defect_cell.ID] = defect_cell_study
                    print('Defect Cell Study "%s" created' % defect_cell.ID)
                else:
                    return None
            else:
                self.defect_study.defect_cell_studies[defect_cell.ID] = defect_cell_study
                self.defect_cells_list.insert(0, defect_cell.ID)
                print('Defect Cell Study "%s" created' % defect_cell.ID)

        def remove_defect_cell_study():
            """ Remove the Defect Cell Study object ID selected from the Defect Study object"""
            selected = self.defect_cells_list.curselection()
            if len(selected) == 0:
                mb.showerror('Error', 'Select a defect cell from the list', parent=self)
            else:
                defect_cell_id = self.defect_cells_list.get(selected[0])
                self.defect_cells_list.delete(selected[0])
                self.defect_study.defect_cell_studies.pop(defect_cell_id)
                print('Defect Study "%s" removed' % defect_cell_id)

        ttk.Button(self.button_frame, text='Add defect cell', command=add_defect_cell_study).grid(row=0, column=0)
        ttk.Button(self.button_frame, text='Remove defect cell', command=remove_defect_cell_study).grid(row=0, column=1)

        # ---------------------------------------------- POTENTIAL ALIGNMENT -------------------------------------------

        if self.defect_study.potential_alignment_correction is True:
            self.plot_pot_al_frame = ttk.LabelFrame(self.defect_cell_frame, text='Potential alignment')
            self.plot_pot_al_frame.grid(row=6, column=0, columnspan=2, sticky='we', padx=5, pady=5)
            self.plot_pot_al_frame.grid_columnconfigure(0, weight=1)
            self.plot_pot_al_frame.grid_columnconfigure(1, weight=1)

            self.display_atom_labels = tk.BooleanVar()
            self.display_atom_labels.set(False)

            ttk.Checkbutton(self.plot_pot_al_frame, text='Display atoms names', onvalue=True, offvalue=False,
                            variable=self.display_atom_labels).grid(row=0, column=0, columnspan=2)

            def plot_potential_alignment():
                """ Plot the potential alignment of the selected defect cell study object """

                selected = self.defect_cells_list.curselection()
                if len(selected) == 0:
                    mb.showerror('Error', 'Selected a defect cell in the list')
                else:
                    defect_cell_study_id = self.defect_cells_list.get(selected)
                    defect_cell_study = self.defect_study.defect_cell_studies[defect_cell_study_id]
                    defect_cell_study.plot_potential_alignment(self.display_atom_labels.get())

            ttk.Button(self.plot_pot_al_frame, text='Plot potential alignment', command=plot_potential_alignment
                       ).grid(row=1, column=0, columnspan=2)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------ DEFECT CELL LIST --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.defect_cells_list_frame = ttk.Frame(self.defect_cell_frame)
        self.defect_cells_list_frame.grid(row=4, column=0, columnspan=2, sticky='nswe')
        self.defect_cells_list_frame.grid_rowconfigure(0, weight=1)

        self.yscrollbar = ttk.Scrollbar(self.defect_cells_list_frame, orient='vertical')  # scrollbar for the y-axis
        self.defect_cells_list = tk.Listbox(self.defect_cells_list_frame, selectmode='extended', width=40)

        self.yscrollbar.pack(side='right', fill='y')
        self.defect_cells_list.pack(side='left', fill='both', expand=True)

        self.yscrollbar.config(command=self.defect_cells_list.yview)
        self.defect_cells_list.config(yscrollcommand=self.yscrollbar.set)

        self.defect_cells_list.insert(0, *self.defect_study.defect_cell_studies.keys())

        def open_defect_cell_study_parameters_window(event):
            """ Open the defect cell study parameters window """
            selection = self.defect_cells_list.curselection()
            if len(selection) != 0:
                defect_cell_study = self.defect_cells_list.get(selection[0])
                Defect_Cell_Study_Parameters_Window(self, self.defect_study.defect_cell_studies[defect_cell_study])

        self.defect_cells_list.bind('<Double-Button-1>', open_defect_cell_study_parameters_window)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- PLOT PARAMETERS  ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.plot_param_frame = ttk.Frame(self.cell_notebook)
        self.cell_notebook.add(self.plot_param_frame, text='Plot parameters')
        self.plot_param_frame.grid_columnconfigure(0, weight=1)
        self.plot_param_frame.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------- DOS PLOT PARAMETERS --------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.dpp_frame_label = ttk.Label(self, text='DOS', font='-weight bold')
        self.dpp_frame = ttk.LabelFrame(self.plot_param_frame, labelwidget=self.dpp_frame_label)
        self.dpp_frame.grid(row=0, column=0, sticky='nswe', padx=5, pady=5)
        self.dpp_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- ENERGY RANGE -----------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.dpp_energy_range_frame = ttk.Frame(self.dpp_frame)
        self.dpp_energy_range_frame.grid(row=0, column=0, sticky='we', pady=3)

        self.dpp_e_low_var = tk.DoubleVar()
        self.dpp_e_high_var = tk.DoubleVar()
        self.dpp_e_low_var.set(self.defect_study.dpp.E_range[0])
        self.dpp_e_high_var.set(self.defect_study.dpp.E_range[1])

        ttk.Label(self.dpp_energy_range_frame, text='Energy: from').pack(side='left')
        ttk.Entry(self.dpp_energy_range_frame, textvariable=self.dpp_e_low_var, width=5).pack(side='left')
        ttk.Label(self.dpp_energy_range_frame, text='eV to').pack(side='left')
        ttk.Entry(self.dpp_energy_range_frame, textvariable=self.dpp_e_high_var, width=5).pack(side='left')
        ttk.Label(self.dpp_energy_range_frame, text='eV').pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- DOS RANGE ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.dpp_dos_range_frame = ttk.Frame(self.dpp_frame)
        self.dpp_dos_range_frame.grid(row=1, column=0, sticky='we', pady=3)

        self.dpp_dos_low_var = tk.DoubleVar()
        self.dpp_dos_high_var = tk.DoubleVar()
        self.dpp_dos_low_var.set(self.defect_study.dpp.DOS_range[0])
        self.dpp_dos_high_var.set(self.defect_study.dpp.DOS_range[1])

        ttk.Label(self.dpp_dos_range_frame, text='DOS: from').pack(side='left')
        ttk.Entry(self.dpp_dos_range_frame, textvariable=self.dpp_dos_low_var, width=5).pack(side='left')
        ttk.Label(self.dpp_dos_range_frame, text='states/eV to').pack(side='left')
        ttk.Entry(self.dpp_dos_range_frame, textvariable=self.dpp_dos_high_var, width=5).pack(side='left')
        ttk.Label(self.dpp_dos_range_frame, text='states/eV').pack(side='left')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------- FORMATION ENERGY PARAMETERS -----------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.fpp_frame_label = ttk.Label(self, text='Formation energy', font='-weight bold')
        self.fpp_frame = ttk.LabelFrame(self.plot_param_frame, labelwidget=self.fpp_frame_label)
        self.fpp_frame.grid(row=0, column=1, rowspan=2, sticky='nswe', padx=5, pady=5)
        self.fpp_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------- FORMATION ENERGY PLOT PARAMETERS -------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.fpp_plot_frame_label = ttk.Label(self, text='Plot')
        self.fpp_plot_frame = ttk.LabelFrame(self.fpp_frame, labelwidget=self.fpp_plot_frame_label)
        self.fpp_plot_frame.grid(row=0, column=0, sticky='nswe', padx=5, pady=5)
        self.fpp_plot_frame.grid_columnconfigure(0, weight=1)

        # ------------------------------------------------- ENERGY RANGE -----------------------------------------------

        self.fpp_energy_range_frame = ttk.Frame(self.fpp_plot_frame)
        self.fpp_energy_range_frame.grid(row=0, column=0, sticky='we', pady=3)

        self.fpp_e_low_var = tk.DoubleVar()
        self.fpp_e_high_var = tk.DoubleVar()
        self.fpp_e_low_var.set(self.defect_study.fpp.E_range[0])
        self.fpp_e_high_var.set(self.defect_study.fpp.E_range[1])

        ttk.Label(self.fpp_energy_range_frame, text='Energy: from').pack(side='left')
        ttk.Entry(self.fpp_energy_range_frame, textvariable=self.fpp_e_low_var, width=5).pack(side='left')
        ttk.Label(self.fpp_energy_range_frame, text='eV to').pack(side='left')
        ttk.Entry(self.fpp_energy_range_frame, textvariable=self.fpp_e_high_var, width=5).pack(side='left')
        ttk.Label(self.fpp_energy_range_frame, text='eV').pack(side='left')

        # --------------------------------------------- FORMATION ENERGY RANGE -----------------------------------------

        self.fpp_for_range_frame = ttk.Frame(self.fpp_plot_frame)
        self.fpp_for_range_frame.grid(row=1, column=0, sticky='we', pady=3)

        self.fpp_for_low_var = tk.StringVar()
        self.fpp_for_high_var = tk.StringVar()
        self.fpp_for_low_var.set(self.defect_study.fpp.for_range[0])
        self.fpp_for_high_var.set(self.defect_study.fpp.for_range[1])

        ttk.Label(self.fpp_for_range_frame, text='Formation energy: from').pack(side='left')
        ttk.Entry(self.fpp_for_range_frame, textvariable=self.fpp_for_low_var, width=5).pack(side='left')
        ttk.Label(self.fpp_for_range_frame, text='eV to').pack(side='left')
        ttk.Entry(self.fpp_for_range_frame, textvariable=self.fpp_for_high_var, width=5).pack(side='left')
        ttk.Label(self.fpp_for_range_frame, text='eV').pack(side='left')

        # ------------------------------------------- DISPLAY TRANSITION LEVELS ----------------------------------------

        self.fpp_display_tr_lvls = tk.BooleanVar()
        self.fpp_display_tr_lvls.set(self.defect_study.fpp.display_transition_levels)

        ttk.Checkbutton(self.fpp_plot_frame, text='Display transition levels', onvalue=True, offvalue=False,
                        variable=self.fpp_display_tr_lvls).grid(row=2, column=0, pady=3)

        # -------------------------------------------- DISPLAY CHARGES LABELS ------------------------------------------

        self.fpp_display_charges = tk.BooleanVar()
        self.fpp_display_charges.set(self.defect_study.fpp.display_charges)

        ttk.Checkbutton(self.fpp_plot_frame, text='Display charges labels', onvalue=True, offvalue=False,
                        variable=self.fpp_display_charges).grid(row=3, column=0, pady=3)

        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------- FORMATION ENERGY FIGURE PARAMETERS ------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.fpp_fig_frame_label = ttk.Label(self, text='Figure')
        self.fpp_fig_frame = ttk.LabelFrame(self.fpp_frame, labelwidget=self.fpp_fig_frame_label)
        self.fpp_fig_frame.grid(row=1, column=0, sticky='nswe', padx=5, pady=5)
        self.fpp_fig_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- FIGURE -------------------------------------------------

        self.fpp_figure_frame = ttk.Frame(self.fpp_fig_frame)
        self.fpp_figure_frame.grid(row=0, column=0)

        self.fpp_figure_var = tk.StringVar()
        self.fpp_figure_var.set(self.defect_study.fpp.figure.name)

        def create_figure():
            """ Create a Figure_Window object """
            self.fpp_figure_window = pfw.Figure_Window(self)
            self.fpp_figure_window.grab_set()
            self.wait_window(self.fpp_figure_window)
            self.fpp_figure_window.grab_release()

        def delete_figure():
            """ Delete the current selected figure in the combobox """
            figures_window = pfw.Figure_Window(self)
            figures_window.delete_figure(self.fpp_figure_var)
            figures_window.destroy()

        ttk.Button(self.fpp_figure_frame, text='Create Figure', command=create_figure).grid(row=1, column=0,
                                                                                            padx=5, pady=3)
        ttk.Button(self.fpp_figure_frame, text='Delete Figure', command=delete_figure).grid(row=1, column=1,
                                                                                            padx=5, pady=3)

        self.fpp_fig_combobox = ttk.Combobox(self.fpp_figure_frame, values=self.project.Figures.keys(), width=15,
                                             textvariable=self.fpp_figure_var, state='readonly')
        self.fpp_fig_combobox.grid(row=0, column=0, columnspan=2, padx=5, pady=3)

        self.fpp_fig_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_fpp_subplot_nb())

        # --------------------------------------------------- SUBPLOT NB -----------------------------------------------

        self.fpp_subplot_nb_var = tk.IntVar()
        self.fpp_subplot_nb_var.set(self.defect_study.fpp.subplot_nb)

        self.fpp_subplot_frame = ttk.Frame(self.fpp_fig_frame)
        self.fpp_subplot_frame.grid(row=2, column=0)

        def open_subplot_nb_choice_window_tpp():
            """ Open the Subplot_Number_Choice_Window """
            subplot_window = pfw.Subplot_Number_Choice_Window(self, self.defect_study,
                                                              self.project.Figures[self.fpp_figure_var.get()],
                                                              self.fpp_subplot_nb_var)
            subplot_window.grab_set()
            self.wait_window(subplot_window)
            subplot_window.grab_release()

        ttk.Button(self.fpp_subplot_frame, text='Plot position', command=open_subplot_nb_choice_window_tpp
                   ).pack(side='left', padx=5, pady=3)
        ttk.Entry(self.fpp_subplot_frame, textvariable=self.fpp_subplot_nb_var, width=2, state='readonly'
                  ).pack(side='left', padx=5, pady=3)

        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------- FORMATION ENERGY LABELS PARAMETERS ------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.fpp_labels_frame_label = ttk.Label(self, text='Labels')
        self.fpp_labels_frame = ttk.LabelFrame(self.fpp_frame, labelwidget=self.fpp_labels_frame_label)
        self.fpp_labels_frame.grid(row=2, column=0, sticky='nswe', padx=5, pady=5)
        self.fpp_labels_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- TITLE --------------------------------------------------

        self.fpp_title_var = tk.StringVar()
        self.fpp_title_var.set(self.defect_study.fpp.title)

        self.fpp_title_frame = ttk.Frame(self.fpp_labels_frame)
        self.fpp_title_frame.grid(row=3, column=0, sticky='we', padx=5, pady=3)

        ttk.Label(self.fpp_title_frame, text='Title').pack(side='left')
        ttk.Entry(self.fpp_title_frame, textvariable=self.fpp_title_var).pack(side='left', fill='x', expand=True)

        # --------------------------------------------------- TEXT SIZE ------------------------------------------------

        self.fpp_text_size_var = tk.IntVar()
        self.fpp_text_size_var.set(self.defect_study.fpp.text_size)

        self.fpp_text_size_frame = ttk.Frame(self.fpp_labels_frame)
        self.fpp_text_size_frame.grid(row=4, column=0, padx=5, pady=3)

        ttk.Label(self.fpp_text_size_frame, text='Text size').pack(side='left')
        tk.Spinbox(self.fpp_text_size_frame, from_=10, to=100, textvariable=self.fpp_text_size_var, width=3
                   ).pack(side='left')

        # -------------------------------------------------- AXIS LABELS -----------------------------------------------

        self.fpp_label_display_var = tk.BooleanVar()
        self.fpp_xlabel_display_var = tk.BooleanVar()
        self.fpp_ylabel_display_var = tk.BooleanVar()
        self.fpp_common_ylabel_display_var = tk.BooleanVar()
        self.fpp_xticklabels_display_var = tk.BooleanVar()
        self.fpp_yticklabels_display_var = tk.BooleanVar()

        self.fpp_label_display_var.set(self.defect_study.fpp.label_display)
        self.fpp_xlabel_display_var.set(self.defect_study.fpp.xlabel_display)
        self.fpp_ylabel_display_var.set(self.defect_study.fpp.ylabel_display)
        self.fpp_common_ylabel_display_var.set(self.defect_study.fpp.common_ylabel_display)
        self.fpp_xticklabels_display_var.set(self.defect_study.fpp.xticklabels_display)
        self.fpp_yticklabels_display_var.set(self.defect_study.fpp.yticklabels_display)

        def enable_axis_label():
            """ Enable the projected dos frame is the checkbutton is checked and disable it if it is not """
            if self.fpp_label_display_var.get() is True:
                utk.enable_frame(self.fpp_axis_label_frame)
            elif self.fpp_label_display_var.get() is False:
                utk.disable_frame(self.fpp_axis_label_frame)

        self.fpp_auto_label_frame = ttk.Frame(self)
        ttk.Label(self.fpp_auto_label_frame, text='Axis labelling').grid(row=0, column=0, columnspan=2)
        ttk.Radiobutton(self.fpp_auto_label_frame, variable=self.fpp_label_display_var, value=True, text='Personalised',
                        command=enable_axis_label).grid(row=1, column=0)
        ttk.Radiobutton(self.fpp_auto_label_frame, variable=self.fpp_label_display_var, value=False, text='Auto',
                        command=enable_axis_label).grid(row=1, column=1)

        self.fpp_axis_label_frame = ttk.LabelFrame(self.fpp_labels_frame, labelwidget=self.fpp_auto_label_frame)
        self.fpp_axis_label_frame.grid(row=5, column=0, padx=5, pady=5)

        ttk.Checkbutton(self.fpp_axis_label_frame, text='X axis label',
                        variable=self.fpp_xlabel_display_var).grid(row=0, column=0)
        ttk.Checkbutton(self.fpp_axis_label_frame, text='Y axis label',
                        variable=self.fpp_ylabel_display_var).grid(row=1, column=0)
        ttk.Checkbutton(self.fpp_axis_label_frame, text='Common Y axis label',
                        variable=self.fpp_common_ylabel_display_var).grid(row=2, column=0)
        ttk.Checkbutton(self.fpp_axis_label_frame, text='X axis ticks labels',
                        variable=self.fpp_xticklabels_display_var).grid(row=3, column=0)
        ttk.Checkbutton(self.fpp_axis_label_frame, text='Y axis ticks labels',
                        variable=self.fpp_yticklabels_display_var).grid(row=4, column=0)

        enable_axis_label()  # initiate the state of the frame

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------- TRANSITION LEVELS PARAMETERS -----------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.tpp_frame_label = ttk.Label(self, text='Transition levels', font='-weight bold')
        self.tpp_frame = ttk.LabelFrame(self.plot_param_frame, labelwidget=self.tpp_frame_label)
        self.tpp_frame.grid(row=1, column=0, sticky='nswe', padx=5, pady=5)
        self.tpp_frame.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------- TRANSITION LEVELS PLOT PARAMETERS -------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.tpp_plot_frame_label = ttk.Label(self, text='Plot')
        self.tpp_plot_frame = ttk.LabelFrame(self.tpp_frame, labelwidget=self.tpp_plot_frame_label)
        self.tpp_plot_frame.grid(row=0, column=0, sticky='nswe', padx=5, pady=5)
        self.tpp_plot_frame.grid_columnconfigure(0, weight=1)

        # ------------------------------------------------- ENERGY RANGE -----------------------------------------------

        self.tpp_energy_range_frame = ttk.Frame(self.tpp_plot_frame)
        self.tpp_energy_range_frame.grid(row=0, column=0, sticky='we', pady=3)

        self.tpp_e_low_var = tk.DoubleVar()
        self.tpp_e_high_var = tk.DoubleVar()
        self.tpp_e_low_var.set(self.defect_study.tpp.E_range[0])
        self.tpp_e_high_var.set(self.defect_study.tpp.E_range[1])

        ttk.Label(self.tpp_energy_range_frame, text='Energy: from').pack(side='left')
        ttk.Entry(self.tpp_energy_range_frame, textvariable=self.tpp_e_low_var, width=5).pack(side='left')
        ttk.Label(self.tpp_energy_range_frame, text='eV to').pack(side='left')
        ttk.Entry(self.tpp_energy_range_frame, textvariable=self.tpp_e_high_var, width=5).pack(side='left')
        ttk.Label(self.tpp_energy_range_frame, text='eV').pack(side='left')

        # -------------------------------------------------- GAP CHOICE ------------------------------------------------

        self.tpp_gap_choice_frame = ttk.Frame(self.tpp_plot_frame)
        self.tpp_gap_choice_frame.grid(row=1, column=0, sticky='we', pady=3)

        self.tpp_gap_choice_var = tk.StringVar()
        self.tpp_gap_choice_var.set(self.defect_study.tpp.gap_choice)

        ttk.Label(self.tpp_gap_choice_frame, text='Gap displayed').pack(side='left', padx=5)
        ttk.Combobox(self.tpp_gap_choice_frame, values=self.defect_study.gaps.keys(),
                     textvariable=self.tpp_gap_choice_var, state='readonly').pack(side='left', padx=5)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------- TRANSITION LEVELS FIGURE PARAMETERS ------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.tpp_fig_frame_label = ttk.Label(self, text='Figure')
        self.tpp_fig_frame = ttk.LabelFrame(self.tpp_frame, labelwidget=self.tpp_fig_frame_label)
        self.tpp_fig_frame.grid(row=1, column=0, sticky='nswe', padx=5, pady=5)
        self.tpp_fig_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- FIGURE -------------------------------------------------

        self.tpp_figure_frame = ttk.Frame(self.tpp_fig_frame)
        self.tpp_figure_frame.grid(row=0, column=0)

        self.tpp_figure_var = tk.StringVar()
        self.tpp_figure_var.set(self.defect_study.tpp.figure.name)

        def create_figure():
            """ Create a Figure_Window object """
            self.tpp_figure_window = pfw.Figure_Window(self)
            self.tpp_figure_window.grab_set()
            self.wait_window(self.tpp_figure_window)
            self.tpp_figure_window.grab_release()

        def delete_figure():
            """ Delete the current selected figure in the combobox """
            figures_window = pfw.Figure_Window(self)
            figures_window.delete_figure(self.tpp_figure_var)
            figures_window.destroy()

        ttk.Button(self.tpp_figure_frame, text='Create Figure', command=create_figure).grid(row=1, column=0,
                                                                                            padx=5, pady=3)
        ttk.Button(self.tpp_figure_frame, text='Delete Figure', command=delete_figure).grid(row=1, column=1,
                                                                                            padx=5, pady=3)

        self.tpp_fig_combobox = ttk.Combobox(self.tpp_figure_frame, values=self.project.Figures.keys(), width=15,
                                             textvariable=self.tpp_figure_var, state='readonly')
        self.tpp_fig_combobox.grid(row=0, column=0, columnspan=2, padx=5, pady=3)
        self.tpp_fig_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_tpp_subplot_nb())

        # --------------------------------------------------- SUBPLOT NB -----------------------------------------------

        self.tpp_subplot_nb_var = tk.IntVar()
        self.tpp_subplot_nb_var.set(self.defect_study.tpp.subplot_nb)

        self.tpp_subplot_frame = ttk.Frame(self.tpp_fig_frame)
        self.tpp_subplot_frame.grid(row=2, column=0)

        def open_subplot_nb_choice_window_tpp():
            """ Open the Subplot_Number_Choice_Window """
            subplot_window = pfw.Subplot_Number_Choice_Window(self, self.defect_study,
                                                              self.project.Figures[self.tpp_figure_var.get()],
                                                              self.tpp_subplot_nb_var)
            subplot_window.grab_set()
            self.wait_window(subplot_window)
            subplot_window.grab_release()

        ttk.Button(self.tpp_subplot_frame, text='Plot position', command=open_subplot_nb_choice_window_tpp
                   ).pack(side='left', padx=5, pady=3)
        ttk.Entry(self.tpp_subplot_frame, textvariable=self.tpp_subplot_nb_var, width=2, state='readonly'
                  ).pack(side='left', padx=5, pady=3)

        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------- TRANSITION LEVELS LABELS PARAMETERS ------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.tpp_labels_frame_label = ttk.Label(self, text='Labels')
        self.tpp_label_frame = ttk.LabelFrame(self.tpp_frame, labelwidget=self.tpp_labels_frame_label)
        self.tpp_label_frame.grid(row=2, column=0, sticky='nswe', padx=5, pady=5)
        self.tpp_label_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- TITLE --------------------------------------------------

        self.tpp_title_var = tk.StringVar()
        self.tpp_title_var.set(self.defect_study.tpp.title)

        self.tpp_title_frame = ttk.Frame(self.tpp_label_frame)
        self.tpp_title_frame.grid(row=3, column=0, sticky='we', pady=3)

        ttk.Label(self.tpp_title_frame, text='Title').pack(side='left')
        ttk.Entry(self.tpp_title_frame, textvariable=self.tpp_title_var).pack(side='left', fill='x', expand=True)

        # --------------------------------------------------- TEXT SIZE ------------------------------------------------

        self.tpp_text_size_var = tk.IntVar()
        self.tpp_text_size_var.set(self.defect_study.tpp.text_size)

        self.tpp_text_size_frame = ttk.Frame(self.tpp_label_frame)
        self.tpp_text_size_frame.grid(row=4, column=0, pady=3)

        ttk.Label(self.tpp_text_size_frame, text='Text size').pack(side='left')
        tk.Spinbox(self.tpp_text_size_frame, from_=10, to=100, textvariable=self.tpp_text_size_var, width=3
                   ).pack(side='left')

        # -------------------------------------------------- AXIS LABELS -----------------------------------------------

        self.tpp_label_display_var = tk.BooleanVar()
        self.tpp_ylabel_display_var = tk.BooleanVar()
        self.tpp_common_ylabel_display_var = tk.BooleanVar()
        self.tpp_yticklabels_display_var = tk.BooleanVar()

        self.tpp_label_display_var.set(self.defect_study.tpp.label_display)
        self.tpp_ylabel_display_var.set(self.defect_study.tpp.ylabel_display)
        self.tpp_common_ylabel_display_var.set(self.defect_study.tpp.common_ylabel_display)
        self.tpp_yticklabels_display_var.set(self.defect_study.tpp.yticklabels_display)

        def enable_axis_label():
            """ Enable the projected dos frame is the checkbutton is checked and disable it if it is not """
            if self.tpp_label_display_var.get() is True:
                utk.enable_frame(self.tpp_axis_label_frame)
            elif self.tpp_label_display_var.get() is False:
                utk.disable_frame(self.tpp_axis_label_frame)

        self.tpp_auto_label_frame = ttk.Frame(self)
        ttk.Label(self.tpp_auto_label_frame, text='Axis labelling').grid(row=0, column=0, columnspan=2)
        ttk.Radiobutton(self.tpp_auto_label_frame, variable=self.tpp_label_display_var, value=True, text='Personalised',
                        command=enable_axis_label).grid(row=1, column=0)
        ttk.Radiobutton(self.tpp_auto_label_frame, variable=self.tpp_label_display_var, value=False, text='Auto',
                        command=enable_axis_label).grid(row=1, column=1)

        self.tpp_axis_label_frame = ttk.LabelFrame(self.tpp_label_frame, labelwidget=self.tpp_auto_label_frame)
        self.tpp_axis_label_frame.grid(row=5, column=0, padx=5, pady=5)

        ttk.Checkbutton(self.tpp_axis_label_frame, text='Y axis label',
                        variable=self.tpp_ylabel_display_var).grid(row=1, column=0)
        ttk.Checkbutton(self.tpp_axis_label_frame, text='Common Y axis label',
                        variable=self.tpp_common_ylabel_display_var).grid(row=2, column=0)
        ttk.Checkbutton(self.tpp_axis_label_frame, text='Y axis ticks labels',
                        variable=self.tpp_yticklabels_display_var).grid(row=4, column=0)

        enable_axis_label()  # initiate the state of the frame

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------- MAIN BUTTONS -------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.main_buttons_frame = ttk.Frame(self)
        self.main_buttons_frame.pack(expand=True, fill='both')

        def save_parameters():
            """ Save the parameters in the Defect_Study object """

            # ----------------------------------------- DOS PLOT PARAMETERS --------------------------------------------

            self.defect_study.dpp.E_range = [self.dpp_e_low_var.get(), self.dpp_e_high_var.get()]
            self.defect_study.dpp.DOS_range = [self.dpp_dos_low_var.get(), self.dpp_dos_high_var.get()]

            # ---------------------------------- FORMATION ENERGY PLOT PARAMETERS --------------------------------------

            # Plot parameters
            self.defect_study.fpp.E_range = [self.fpp_e_low_var.get(), self.fpp_e_high_var.get()]
            self.defect_study.fpp.for_range = [self.fpp_for_low_var.get(), self.fpp_for_high_var.get()]
            self.defect_study.fpp.display_transition_levels = self.fpp_display_tr_lvls.get()
            self.defect_study.fpp.display_charges = self.fpp_display_charges.get()

            # Figure parameters
            self.defect_study.fpp.figure = self.project.Figures[self.fpp_figure_var.get()]
            self.defect_study.fpp.subplot_nb = self.fpp_subplot_nb_var.get()
            self.defect_study.fpp.title = self.fpp_title_var.get()
            self.defect_study.fpp.text_size = self.fpp_text_size_var.get()

            self.defect_study.fpp.label_display = self.fpp_label_display_var.get()
            self.defect_study.fpp.xlabel_display = self.fpp_xlabel_display_var.get()
            self.defect_study.fpp.ylabel_display = self.fpp_ylabel_display_var.get()
            self.defect_study.fpp.common_ylabel_display = self.fpp_common_ylabel_display_var.get()
            self.defect_study.fpp.xticklabels_display = self.fpp_xticklabels_display_var.get()
            self.defect_study.fpp.yticklabels_display = self.fpp_yticklabels_display_var.get()

            # ---------------------------------- TRANSITION LEVELS PLOT PARAMETERS -------------------------------------

            # Plot parameters
            self.defect_study.tpp.E_range = [self.tpp_e_low_var.get(), self.tpp_e_high_var.get()]
            self.defect_study.tpp.gap_choice = self.tpp_gap_choice_var.get()

            # Figure parameters
            self.defect_study.tpp.figure = self.project.Figures[self.tpp_figure_var.get()]
            self.defect_study.tpp.subplot_nb = self.tpp_subplot_nb_var.get()
            self.defect_study.tpp.title = self.tpp_title_var.get()
            self.defect_study.tpp.text_size = self.tpp_text_size_var.get()

            self.defect_study.tpp.label_display = self.tpp_label_display_var.get()
            self.defect_study.tpp.ylabel_display = self.tpp_ylabel_display_var.get()
            self.defect_study.tpp.common_ylabel_display = self.tpp_common_ylabel_display_var.get()
            self.defect_study.tpp.yticklabels_display = self.tpp_yticklabels_display_var.get()

            self.destroy()

        ttk.Button(self.main_buttons_frame, text='Save', command=save_parameters).pack(side='right', padx=5, pady=3)
        ttk.Button(self.main_buttons_frame, text='Cancel', command=self.destroy).pack(side='right', padx=5, pady=3)

        utk.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------- METHODS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def update_fpp_subplot_nb(self):
        """ Set the subplot number to 1 if it is outside its possible values set """
        figure = self.project.Figures[self.fpp_figure_var.get()]
        if self.fpp_subplot_nb_var.get() > figure.nb_rows * figure.nb_cols:
            self.fpp_subplot_nb_var.set(1)

    def update_tpp_subplot_nb(self):
        """ Set the subplot number to 1 if it is outside its possible values set """
        figure = self.project.Figures[self.tpp_figure_var.get()]
        if self.tpp_subplot_nb_var.get() > figure.nb_rows * figure.nb_cols:
            self.tpp_subplot_nb_var.set(1)

    def populate_defect_cells_ccb(self):
        """ Populate the defect cells combobox """

        def check_compatibility(host_cell, defect_cell, defects):
            """ Check if a Cell is compatible with the Host Cell and the Defects of the study by comparing the
            number of atoms of each atomic species """

            cc.normalise_composition(host_cell, defect_cell)
            [cc.normalise_composition(host_cell, f) for f in defects]
            [cc.normalise_composition(defect_cell, f) for f in defects]

            for key in host_cell.population.keys():
                if host_cell.population[key] != defect_cell.population[key] + sum([f.population[key] for f in defects]):
                    return False
            return True

        self.defect_cell_ccb['values'] = [key for key in self.project.Cells.keys() if check_compatibility(
                                          self.defect_study.Host_Cell, self.project.Cells[key],
                                          self.defect_study.DefectS)]


class Defect_Cell_Study_Parameters_Window(tk.Toplevel):
    """ Give the value of each correction for a given defect cell """

    def __init__(self, parent, defect_cell_study):

        tk.Toplevel.__init__(self, parent)

        self.title(defect_cell_study.Defect_Cell.ID)
        self.resizable(False, False)
        self.bind('<Control-w>', lambda event: self.destroy())

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')

        ttk.Label(self.main_frame, text=u'Correction of the VBM q*\u0394E_{V,corr} = '
                  ).grid(row=0, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.vbm_corr, 5)) + ' eV'
                  ).grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(self.main_frame, text=u'Correction of the PHS \u0394E_{PHS} = '
                  ).grid(row=1, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.phs_corr[0], 5)) + ' eV (h) & ' +
                  str(np.round(defect_cell_study.phs_corr[1], 5)) + ' eV (e)'
                  ).grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(self.main_frame, text=u'Potential alignment q*\u0394V = '
                  ).grid(row=2, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.pa_corr, 5)) + 'eV (' +
                                        str(np.round(defect_cell_study.spheres_radius, 3)) + ' \u212B)'
                  ).grid(row=2, column=1, padx=5, pady=3)

        ttk.Label(self.main_frame, text=u'Moss-Burstein correction \u0394E_{MB} = '
                  ).grid(row=3, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.mb_corr[0], 5)) + ' eV (h) & ' +
                  str(np.round(defect_cell_study.mb_corr[1], 5)) + ' eV (e)'
                  ).grid(row=3, column=1, padx=5, pady=3)

        ttk.Label(self.main_frame, text=u'Makov-Payne correction 2008 \u0394E_{MP} = '
                  ).grid(row=4, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.mp_corr, 5)) + ' eV'
                  ).grid(row=4, column=1, padx=5, pady=3)

        ttk.Label(self.main_frame, text='Defect formation energy at E_F = 0: E_for = '
                  ).grid(row=5, column=0, padx=5, pady=3)
        ttk.Label(self.main_frame, text=str(np.round(defect_cell_study.E_for_0, 5)) + ' eV'
                  ).grid(row=5, column=1, padx=5, pady=3)

        utk.centre_window(self)


class Gap_Input_Window(tk.Toplevel):
    """ Window for experimental and theoretical gaps input """

    def __init__(self, parent, gap_input_var):

        tk.Toplevel.__init__(self, parent)
        self.title('Gaps')
        self.resizable(False, False)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- INPUT --------------------------------------------------

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=0, column=0, sticky='nswe', padx=3, pady=3)
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.name_var = tk.StringVar()
        self.value_var = tk.DoubleVar()
        self.name_var.set('Experimental gap')

        ttk.Label(self.input_frame, text='Name').grid(row=0, column=0)
        ttk.Entry(self.input_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='we')

        ttk.Label(self.input_frame, text='Value (eV)').grid(row=1, column=0)
        ttk.Entry(self.input_frame, textvariable=self.value_var).grid(row=1, column=1, sticky='we')

        # ---------------------------------------------------- BUTTONS -------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, padx=3, pady=3)

        def add_gap():
            """ Add the gap to the listbox """
            gap_name = self.name_var.get()
            if ';' in gap_name:
                mb.showwarning('Warning', 'The name of the gap can not contains the character ";"')
            else:
                try:
                    gap_value = self.value_var.get()
                except ValueError:
                    mb.showerror('Error', 'The gap value must be a number')
                    return None
                gap_id = gap_name + ' (' + str(gap_value) + ' eV)'
                if gap_id not in self.list_content.get():
                    self.listbox.insert('end', gap_id)

        def remove_gap():
            """ Remove the selected gap from the listbox """
            selection = self.listbox.curselection()
            if len(selection) != 0:
                self.listbox.delete(selection[0])

        ttk.Button(self.button_frame, text='Add gap', command=add_gap).grid(row=0, column=0)
        ttk.Button(self.button_frame, text='Remove gap', command=remove_gap).grid(row=0, column=1)

        # ------------------------------------------------------ LIST --------------------------------------------------

        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.grid(row=2, column=0, sticky='nswe')

        self.list_content = tk.StringVar()

        self.listbox = tk.Listbox(self.list_frame, listvariable=self.list_content)
        if gap_input_var.get().split(';') != ['']:
            [self.listbox.insert(0, f) for f in gap_input_var.get().split(';')]

        self.yscrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.listbox.yview)
        self.yscrollbar.pack(side='right', fill='y')

        self.listbox.configure(yscrollcommand=self.yscrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)

        # ------------------------------------------------- MAIN BUTTONS -----------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=3, column=0, padx=3, pady=3)

        def validate():
            """ Save the content of the list and close the window """
            content = list(self.listbox.get(0, 'end'))
            gap_input_var.set(';'.join(content))
            self.destroy()

        ttk.Button(self.main_button_frame, text='OK', command=validate).grid(row=0, column=0)
        ttk.Button(self.main_button_frame, text='Cancel', command=self.destroy).grid(row=0, column=1)

        self.bind('<Control-w>', lambda event: self.destroy())

        utf.centre_window(self)
