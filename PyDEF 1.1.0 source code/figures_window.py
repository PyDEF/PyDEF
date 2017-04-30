"""
    version: DevB1
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import ttk
import Tkinter as tk
import pydef_core.figure as pf
import tkMessageBox as mb

import cells_window as cw
import defect_studies_window as dsw
import utility_tkinter_functions as ukf


class Figure_Window(tk.Toplevel):
    """ Window for PyDEF Figure object creation """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('Create a new figure')
        self.resizable(False, False)
        self.bind('<Control-w>', lambda event: self.destroy())

        self.main_window = parent.main_window
        self.parent = parent
        self.project = parent.project

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)  # main ttk frame
        self.main_frame.pack(expand=True, fill='both')

        # Variables
        self.figure_name_var = tk.StringVar()
        self.nb_rows_var = tk.IntVar()
        self.nb_cols_var = tk.IntVar()

        self.figure_name_var.set('my figure')
        self.nb_rows_var.set(1)
        self.nb_cols_var.set(1)

        # ------------------------------------------------- FIGURE NAME ------------------------------------------------

        self.figure_name_frame = ttk.Frame(self.main_frame)
        self.figure_name_frame.grid(row=0, padx=3, pady=3)

        ttk.Label(self.figure_name_frame, text='Figure name').pack(side='left', padx=3)
        ttk.Entry(self.figure_name_frame, textvariable=self.figure_name_var, width=30).pack(side='left', padx=3)

        # ---------------------------------------------- NB ROWS & COLUMNS ---------------------------------------------

        self.subplot_frame = ttk.Frame(self.main_frame)
        self.subplot_frame.grid(row=1, padx=3, pady=3)

        ttk.Label(self.subplot_frame, text='Number of rows').pack(side='left', padx=3)
        ttk.Entry(self.subplot_frame, textvariable=self.nb_rows_var, width=3).pack(side='left', padx=3)
        ttk.Label(self.subplot_frame, text='Number of columns').pack(side='left', padx=3)
        ttk.Entry(self.subplot_frame, textvariable=self.nb_cols_var, width=3).pack(side='left', padx=3)

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2, padx=3, pady=3)

        ttk.Button(self.button_frame, text='OK', command=self.create_figure).pack(side='left', padx=5)
        ttk.Button(self.button_frame, text='Cancel', command=self.destroy).pack(side='left', padx=5)

        ukf.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------- METHODS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def create_figure(self):
        """ Create a PyDEF Figure object and load it to the project """

        figure_name = self.figure_name_var.get()
        new_figure = pf.Figure(self.nb_rows_var.get(), self.nb_cols_var.get(), figure_name)
        self.load_figure(new_figure)
        self.destroy()

    def load_figure(self, figure):
        """ Load a Figure object 'figure' in the project.
        If the Figure object is already in the project, ask if overwrite it """

        if figure.name in self.project.Figures.keys():
            if (figure.nb_rows != self.project.Figures[figure.name].nb_rows) or \
                    (figure.nb_cols != self.project.Figures[figure.name].nb_cols):

                overwrite = mb.askyesno('Warning', 'A figure with the same name but with a different number of rows or columns'
                                                   'is already in this project\nDo you want to overwrite it?', parent=self)
                if overwrite is True:
                    self.project.Figures[figure.name] = figure
                    print('Figure "%s" replaced' % figure.name)
                else:
                    return None
        else:
            self.project.Figures[figure.name] = figure  # add the figure to the project
            print('Figure "%s" created' % figure.name)

        self.update_figures()

    def update_figures(self):
        """ Update the figure combobox of each cell properties frames and defect study properties frame """

        try:
            cell_properties_windows = [child for child in self.main_window.cells_window.winfo_children()
                                       if child.__class__ is cw.Cell_Properties_Window]
            for window in cell_properties_windows:
                try:
                    window.b_fig_combobox['values'] = self.project.Figures.keys()
                    window.update_b_subplot_nb()
                except AttributeError:
                    pass
                try:
                    window.fig_combobox['values'] = self.project.Figures.keys()
                    window.update_subplot_nb()
                except AttributeError:
                    pass
        except AttributeError:
            pass

        try:
            defect_study_properties_windows = [child for child in
                                               self.main_window.defect_studies_window.winfo_children()
                                               if child.__class__ is dsw.Defect_Study_Properties_Window]
            for window in defect_study_properties_windows:
                window.fpp_fig_combobox['values'] = self.project.Figures.keys()
                window.update_fpp_subplot_nb()
                window.tpp_fig_combobox['values'] = self.project.Figures.keys()
                window.update_tpp_subplot_nb()
        except AttributeError:
            pass

    def delete_figure(self, figure_var):
        """ Given the ID figure_var, remove the associated Figure object from the project and from the combobox of all
        windows open. If a Cell or a Defect_Study object have the Figure object in their attributes, it is replaced
        by the default Figure object 'New Figure' """

        figure_id = figure_var.get()  # current selected figure ID
        if figure_id == 'New Figure':
            mb.showerror('Error', 'This figure can not be deleted', parent=self)
            return None
        else:
            self.project.Figures.pop(figure_id)  # remove the corresponding Figure object from the project

        # If a Cell object or a Defect_Study object has the same Figure object in its attribute, this latter
        # is replaced by the default Figure object 'New Figure'
        for cell in self.project.Cells.values():
            if cell.dpp.figure.name == figure_id:
                cell.dpp.figure = self.project.Figures['New Figure']
                cell.dpp.subplot_nb = 1

        for defect_study in self.project.Defect_Studies.values():
            if defect_study.fpp.figure.name == figure_id:
                defect_study.fpp.figure = self.project.Figures['New Figure']
                defect_study.fpp.subplot_nb = 1
            if defect_study.tpp.figure.name == figure_id:
                defect_study.tpp.figure = self.project.Figures['New Figure']
                defect_study.tpp.subplot_nb = 1

        # For all Defect_Study_Properties_Window and Cell_Properties_Window object, update the combobox, and if the
        # selected ID is the same as the one deleted, set the new selected ID to 'New Figure'
        try:
            cell_properties_windows = [child for child in self.main_window.cells_window.winfo_children()
                                       if child.__class__ is cw.Cell_Properties_Window]
            for window in cell_properties_windows:
                window.fig_combobox['values'] = self.project.Figures.keys()
                if window.fig_combobox.get() == figure_id:
                    window.fig_combobox.set('New Figure')
                    window.subplot_nb_var.set(1)
        except AttributeError:
            pass
        try:
            defect_study_properties_windows = [child for child in
                                               self.main_window.defect_studies_window.winfo_children()
                                               if child.__class__ is dsw.Defect_Study_Properties_Window]
            for window in defect_study_properties_windows:
                window.fpp_fig_combobox['values'] = self.project.Figures.keys()
                if window.fpp_fig_combobox.get() == figure_id:
                    window.fpp_fig_combobox.set('New Figure')
                    window.fpp_subplot_nb_var.set(1)
                window.tpp_fig_combobox['values'] = self.project.Figures.keys()
                if window.tpp_fig_combobox.get() == figure_id:
                    window.tpp_fig_combobox.set('New Figure')
                    window.tpp_subplot_nb_var.set(1)
        except AttributeError:
            pass


class Subplot_Number_Choice_Window(tk.Toplevel):
    """ Window for choosing a subplot number """

    def __init__(self, parent, pydef_object, figure, init_subplot_nb):
        """
        :param parent: parent window
        :param pydef_object: a Cell or Defect_Study object
        :param figure: a PyDEF Figure object
        :param init_subplot_nb: a Tkinter IntVar object"""

        tk.Toplevel.__init__(self, parent)

        self.title('Position of "%s" in figure "%s"' % (pydef_object.ID, figure.name))
        self.resizable(False, False)

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------- SUBPLOTS --------------------------------------------------

        self.subplot_frame = ttk.Frame(self.main_frame)
        self.subplot_frame.grid(row=0, column=0, sticky='nswe')

        self.subplot_nb = tk.IntVar()
        self.subplot_nb.set(init_subplot_nb.get())

        for f in range(1, figure.nb_rows + 1):
            for g in range(1, figure.nb_cols + 1):
                frame = ttk.LabelFrame(self.subplot_frame, width=100, height=100)
                frame.grid(row=f, column=g, padx=10)
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_rowconfigure(0, weight=1)
                frame.grid_propagate(False)
                ttk.Radiobutton(frame, text=(f-1) * figure.nb_cols + g,
                                variable=self.subplot_nb, value=(f-1) * figure.nb_cols + g).grid(sticky='ns')

        [self.subplot_frame.grid_columnconfigure(g, weight=1) for g in range(1, figure.nb_cols + 1)]

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, pady=10)

        def save_subplot_nb():
            """Save the subplot number chosen to the init_subplot_nb variable """
            init_subplot_nb.set(self.subplot_nb.get())
            self.destroy()

        ttk.Button(self.button_frame, text='Cancel', command=self.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(self.button_frame, text='OK', command=save_subplot_nb).grid(row=0, column=1, padx=5)

        self.bind('<Control-w>', lambda event: self.destroy())

        ukf.centre_window(self)
