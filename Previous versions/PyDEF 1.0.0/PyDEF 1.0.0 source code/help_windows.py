# -*- coding: utf-8 -*-
""" Help menu
    version: DevB1
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""


import Tkinter as tk
import ttk
import tkFileDialog as fd
import utility_tkinter_functions as ukf
import pydef_images


class About_Window(tk.Toplevel):
    """ Give general information on the current PyDEF version """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)

        self.title('About')
        self.bind('<Control-w>', lambda event: self.destroy())
        self.resizable(False, False)

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')

        self.ribbon_image = tk.PhotoImage(data=pydef_images.ribbon)
        self.ribbon = tk.Label(self.main_frame, image=self.ribbon_image)
        self.ribbon.grid(row=0)

        ttk.Label(self.main_frame, text='Python for Defect Energy Formation 1.0.0\n',
                  font="-size 20 -weight bold"
                  ).grid(row=1)
        ttk.Label(self.main_frame, text=u'Original idea from: Dr. Stéphane Jobic, Dr. Camille Latouche & Emmanuel Péan'
                  ).grid(row=2)
        ttk.Label(self.main_frame, text=u'Developer: Emmanuel Péan'
                  ).grid(row=3)
        ttk.Label(self.main_frame, text='Logo design: Josselin Gesrel'
                  ).grid(row=4)
        ttk.Label(self.main_frame, text='Testers: Dr. Julien Vidal & Dr. Camille Latouche\n'
                  ).grid(row=5)
        ttk.Label(self.main_frame, text='Disclaimer', font='-weight bold'
                  ).grid(row=6)
        ttk.Label(self.main_frame, text='This software is free of use and, although its development was made with care,\n'
                                        'the authors can not guaranty the quality of its outputs\n '
                                        'and will not be liable for any damage caused by it.\n', justify=tk.CENTER
                  ).grid(row=7)
        ttk.Label(self.main_frame, text='A question, a recommendation, or anything else?\n'
                                        'send us an e-mail at pydef.dev@gmail.com', justify=tk.CENTER
                  ).grid(row=8)

        ukf.centre_window(self)


class Parameters_Window(tk.Toplevel):
    """ Parameters window """

    def __init__(self, parent):

        tk.Toplevel.__init__(self, parent)
        self.title('Parameters')
        self.bind('<Control-w>', lambda event: self.destroy())

        self.project = parent.project

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self)  # Main ttk frame
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1, pad=20)
        self.main_frame.grid_rowconfigure(0, weight=1, pad=5)

        # --------------------------------------------- DEFAULT DIRECTORIES --------------------------------------------

        self.dd_input_frame = ttk.Frame(self.main_frame)  # Frame for default directories input
        self.dd_input_frame.grid(row=0, column=0, sticky='nswe')
        self.dd_input_frame.grid_columnconfigure(1, weight=1)

        def choose_vasp_dd():
            """ Open a window to choose the default directory of the VASP data """
            directory = fd.askdirectory(parent=self, initialdir=self.project.dd_vasp)
            if directory != '':
                self.dd_vasp_var.set(directory)

        def choose_pydef_dd():
            """ Open a window to choose the default directory of the PyDEF data  """
            directory = fd.askdirectory(parent=self, initialdir=self.project.dd_pydef)
            if directory != '':
                self.dd_pydef_var.set(directory)

        # Labels
        ttk.Button(self.dd_input_frame, text='VASP data default directory',  command=choose_vasp_dd
                   ).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(self.dd_input_frame, text='PyDEF data default directory', command=choose_pydef_dd
                   ).grid(row=1, column=0, padx=5, pady=3)

        # Variables
        self.dd_vasp_var = tk.StringVar()  # default directory of the VASP data
        self.dd_pydef_var = tk.StringVar()  # default directory of the PyDEF saves

        self.dd_vasp_var.set(self.project.dd_vasp)  # default values are retrieved from the current project
        self.dd_pydef_var.set(self.project.dd_pydef)  # default values are retrieved from the current project

        # Entry fields
        ttk.Entry(self.dd_input_frame, textvariable=self.dd_vasp_var, width=40
                  ).grid(row=0, column=1, sticky='we', padx=5, pady=3)
        ttk.Entry(self.dd_input_frame, textvariable=self.dd_pydef_var, width=40
                  ).grid(row=1, column=1, sticky='we', padx=5, pady=3)

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)  # Frame for the OK and Cancel buttons
        self.button_frame.grid(row=1, column=0)
        self.button_frame.grid_columnconfigure(0, weight=1)

        def save_parameters():
            """ Save the default directories as attributes of the project """
            self.project.dd_vasp = self.dd_vasp_var.get()
            self.project.dd_pydef = self.dd_pydef_var.get()
            self.destroy()

        ttk.Button(self.button_frame, text='OK', command=save_parameters).pack(side='left', padx=5, pady=3)
        ttk.Button(self.button_frame, text='Cancel', command=self.destroy).pack(side='left', padx=5, pady=3)

        ukf.centre_window(self)
