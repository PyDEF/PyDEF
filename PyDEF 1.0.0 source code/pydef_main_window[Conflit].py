""" PyDEF main window
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import Tkinter as tk
import tkFileDialog as fd
import tkMessageBox as mb
import FileDialog  # (for compilation)
import ttk
import pickle
import traceback
import webbrowser
import sys
import os

import pydef_core.pydef_project as pp

import cells_window as cw
import defects_window as dw
import defect_studies_window as dsw
import pydef_images
import help_windows as hw
import utility_tkinter_functions as ukf


class Main_Window(tk.Tk):
    """ Main window of PyDEF """

    def __init__(self):

        tk.Tk.__init__(self)
        tk.Tk.report_callback_exception = self.show_error  # display errors in a window

        self.icon = tk.PhotoImage(data=pydef_images.icon)
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.resizable(False, False)

        # Styles
        s = ttk.Style()
        s.configure('my.TButton', font=('', 18), justify=tk.CENTER)

        self.columnconfigure(0, weight=1, uniform='uni')
        self.columnconfigure(1, weight=1, uniform='uni')
        self.columnconfigure(2, weight=1, uniform='uni')
        self.rowconfigure(0, weight=1, uniform='uni')
        self.rowconfigure(1, weight=1, uniform='uni')

        # New blank project
        self.load_project(pp.Pydef_Project('New project'))

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- MENUBAR --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.menubar = tk.Menu(self)

        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label='New PyDEF project', command=self.create_new_project, accelerator='Ctrl+N')
        self.file_menu.add_command(label='Open PyDEF project', command=self.open_saved_project, accelerator='Ctrl+O')
        self.file_menu.add_command(label='Save PyDEF project', command=self.save_project, accelerator='Ctrl+S')
        self.menubar.add_cascade(label='File', menu=self.file_menu)

        # Help menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label='About', command=self.open_about_window, accelerator='Shift+Ctrl+A')
        self.help_menu.add_command(label='User Guide', command=self.open_user_guide, accelerator='Shift+Ctrl+D')
        self.help_menu.add_command(label='Parameters', command=self.open_parameters_window, accelerator='Shift+Ctrl+P')
        self.menubar.add_cascade(label='Help', menu=self.help_menu)

        self.config(menu=self.menubar)

        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------- KEYBOARD SHORCUTS ---------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.bind_all('<Control-q>', lambda event: self.quit_pydef())
        self.protocol('WM_DELETE_WINDOW', self.quit_pydef)

        self.bind('<Control-n>', lambda event: self.create_new_project())
        self.bind('<Control-o>', lambda event: self.open_saved_project())
        self.bind('<Control-s>', lambda event: self.save_project())

        self.bind_all('<Shift-Control-a>', lambda event: self.open_about_window())
        self.bind_all('<Shift-Control-d>', lambda event: self.open_user_guide())
        self.bind_all('<Shift-Control-p>', lambda event: self.open_parameters_window())

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- RIBBON ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.ribbon_image = tk.PhotoImage(data=pydef_images.ribbon)
        self.ribbon = tk.Label(self, image=self.ribbon_image)
        self.ribbon.grid(row=0, column=0, columnspan=3)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- BUTTONS --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        # Images
        self.si_image = tk.PhotoImage(data=pydef_images.VASP_logo)
        self.defects_image = tk.PhotoImage(data=pydef_images.defects)
        self.defect_study_image = tk.PhotoImage(data=pydef_images.Substitution_cell)
        self.mat_study_image = tk.PhotoImage(data=pydef_images.Vacancy_Substitution_cell)
        self.diagram_image = tk.PhotoImage(data=pydef_images.chem_pot_diagram)
        self.defect_conc = tk.PhotoImage(data=pydef_images.defect_conc)

        # Buttons
        self.cell_button = ttk.Button(self, text='Import VASP\ncalculations', command=self.open_cells_window,
                                      style='my.TButton', image=self.si_image, padding=20,
                                      compound='bottom')

        self.defect_button = ttk.Button(self, text='Defect labels', command=self.open_defects_window,
                                        style='my.TButton', image=self.defects_image,
                                        compound='bottom')

        self.defect_study_button = ttk.Button(self, text='Defect Studies', command=self.open_defect_studies_window,
                                              style='my.TButton', image=self.defect_study_image,
                                              compound='bottom')

        self.mat_study_button = ttk.Button(self, text='Material studies', command=self.show_message,
                                           style='my.TButton', image=self.mat_study_image, padding=10,
                                           compound='bottom')

        self.chem_pot_button = ttk.Button(self, text='Chemical potential\ncalculation', command=self.show_message,
                                          style='my.TButton', image=self.diagram_image, padding=10,
                                          compound='bottom')

        self.defect_conc_button = ttk.Button(self, text='Defect concentration\ncalculation', command=self.show_message,
                                             style='my.TButton', padding=10, image=self.defect_conc,
                                             compound='bottom')

        self.cell_button.grid(row=1, column=0, padx=7, pady=7, sticky='nswe')
        self.defect_button.grid(row=1, column=1, padx=7, pady=7, sticky='nswe')
        self.defect_study_button.grid(row=1, column=2, padx=7, pady=7, sticky='nswe')
        self.mat_study_button.grid(row=2, column=0, padx=7, pady=7, sticky='nswe')
        self.chem_pot_button.grid(row=2, column=1, padx=7, pady=7, sticky='nswe')
        self.defect_conc_button.grid(row=2, column=2, padx=7, pady=7, sticky='nswe')

        self.mat_study_button.configure(state='disabled')
        self.chem_pot_button.configure(state='disabled')
        self.defect_conc_button.configure(state='disabled')

        ukf.centre_window(self)

    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------- METHODS ----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ WINDOW MANAGEMENT -----------------------------------------------

    def quit_pydef(self):
        """ Close the main window """
        if mb.askokcancel('Quit', 'Do you really wish to quit PyDEF?', parent=self):
            self.quit()
        else:
            return None

    def open_cells_window(self):
        """ Open the VASP import window and disable the corresponding button while the window is open """
        self.cell_button.configure(state='disabled')
        self.cells_window = cw.Cells_Window(self)
        self.cells_window.protocol('WM_DELETE_WINDOW', self.close_cells_window)

    def open_defects_window(self):
        """ Open the Defect label window and disable the corresponding button while the window is open """
        self.defect_button.configure(state='disabled')
        self.defects_window = dw.Defect_Window(self)
        self.defects_window.protocol('WM_DELETE_WINDOW', self.close_defects_window)

    def open_defect_studies_window(self):
        """ Open the Defect Study window and disable the corresponding button while the window is open """
        self.defect_study_button.configure(state='disabled')
        self.defect_studies_window = dsw.Defect_Study_Window(self)
        self.defect_studies_window.protocol('WM_DELETE_WINDOW', self.close_defect_studies_window)

    def show_message(self):
        """ Display a simple message for non available feature """
        mb.showinfo('', 'Feature not available yet', parent=self)

    def close_cells_window(self):
        """ Close the 'Cells Window' if it is opened and remove any reference to it """
        try:
            self.cells_window.destroy()
            self.cell_button.configure(state='normal')
            del self.cells_window
        except AttributeError:
            pass

    def close_defects_window(self):
        """ Close the 'Defects Window' if it is opened and remove any reference to it """
        try:
            self.defects_window.destroy()
            self.defect_button.configure(state='normal')
            del self.defects_window
        except AttributeError:
            pass

    def close_defect_studies_window(self):
        """ Close the 'Defect Studies Window' if it is opened and remove any reference to it """
        try:
            self.defect_studies_window.destroy()
            self.defect_study_button.configure(state='normal')
            del self.defect_studies_window
        except AttributeError:
            pass

    # ----------------------------------------------- PROJECT MANAGEMENT -----------------------------------------------

    def create_new_project(self):
        """ Create and load a Pydef_Project object """
        self.new_project_window = New_Project_Window(self)

    def open_saved_project(self):
        """ Open and load a Pydef Project object from a file """

        ofile = fd.askopenfile(parent=self, initialdir=self.project.dd_pydef,
                               filetypes=[('PyDEF files', '*.pydef')], mode='rb')
        if ofile is None:
            print('operation "open saved pydef project" canceled')
            return None  # stop the process if the user click on 'cancel'

        project = pickle.load(ofile)  # read the file
        if project.__class__ is not pp.Pydef_Project:
            # display an error message if the class of the object is not a Pydef_Project
            mb.showerror('Error', 'This file is not a valid PyDEF project', parent=self)
        else:
            self.load_project(project)  # load the project in PyDEF
            ofile.close()

    def load_project(self, aPydef_Project):
        """ Load a Pydef_Project object in PyDEF """

        self.close_cells_window()
        self.close_defects_window()
        self.close_defect_studies_window()

        self.project = aPydef_Project  # set the current project as the one loaded
        self.title('PyDEF - ' + aPydef_Project.name)  # change the name of the window

        print('Project "%s" loaded' % aPydef_Project.name)

    def save_project(self):
        """ Save the current Pydef_Project object """

        ofile = fd.asksaveasfile(parent=self, initialfile=self.project.name, defaultextension='.pydef',
                                 initialdir=self.project.dd_pydef, mode='wb')  # open a file
        if ofile is None:
            print('operation "save pydef project" canceled')
            return None

        pickle.dump(self.project, ofile, -1)  # save the project in the file
        ofile.close()  # close the file

    # --------------------------------------------------- HELP MENU ----------------------------------------------------

    def open_parameters_window(self):
        """ Open the 'parameters' window """
        hw.Parameters_Window(self)

    def open_about_window(self):
        """ Open the 'About' window """
        hw.About_Window(self)

    def open_user_guide(self):
        """ Open the user guide using the web browser """
        if sys.platform == "win32":
            user_guide_loc = 'file://' + os.path.dirname(sys.path[0]) + '/PyDEF_user_guide.pdf'
        else:
            user_guide_loc = 'file://' + sys.path[0] + '/PyDEF_user_guide.pdf'
        webbrowser.open(user_guide_loc, new=2)

    # ---------------------------------------------------- OTHER ------------------------------------------------------

    def show_error(self, *args):
        """ Display a message when an error occurs """
        err = traceback.format_exception(*args)
        mb.showerror('Exception', err)


class New_Project_Window(tk.Toplevel):
    """ Pop-up window for Pydef_Project object creation """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)
        self.title('New project')
        self.grid_columnconfigure(0, weight=1)
        self.resizable(False, False)

        self.main_window = parent

        self.main_frame = ttk.Frame(self)  # main ttk frame
        self.main_frame.pack(expand=True, fill='both')

        # ------------------------------------------------ PROJECT NAME ------------------------------------------------

        self.project_name = tk.StringVar()

        ttk.Label(self.main_frame, text='Name').grid(row=0)
        ttk.Entry(self.main_frame, textvariable=self.project_name, width=40).grid(row=1, sticky='we')

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        def create_new_project():
            """ Create a new Pydef_Project object and close the window """
            project_name = self.project_name.get()
            if project_name == '':
                mb.showwarning('Error', 'The name of the project is blank', parent=self)
            else:
                new_project = pp.Pydef_Project(project_name)  # create the new project with the given name
                parent.load_project(new_project)  # load the new project
                self.destroy()  # close the window

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2)

        ttk.Button(self.button_frame, text='OK', command=create_new_project).pack(side='left')
        ttk.Button(self.button_frame, text='Cancel', command=self.destroy).pack(side='left')

        ukf.centre_window(self)


if __name__ == '__main__':
    GUI = Main_Window()
    GUI.mainloop()
