"""

    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import figure as pf

class Pydef_Project:

    def __init__(self, name):

        self.Cells = {}  # dictionary containing VASP calculations results
        self.Defects = {}  # dictionary containing defects labels
        self.Defect_Studies = {}  # dictionary containing defect studies
        self.Material_Studies = {}  # dictionary containing material studies
        self.Figures = {'New Figure': pf.Figure(1, 1, 'New Figure')}  # dictionary containing pydef figures

        self.name = name  # name of the project

        self.dd_vasp = ''  # VASP data default directory
        self.dd_pydef = ''  # PyDED data default directory
