"""
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import string
import pydef_core.basic_functions as bf
import matplotlib.pyplot as plt

class Figure:
    """ Object containing data on figures to be plotted """

    def __init__(self, nb_rows, nb_cols, name):
        """
        :param nb_rows: number of rows
        :param nb_cols: number of columns
        :param name: name of the figure
        """

        self.nb_rows = nb_rows
        self.nb_cols = nb_cols
        self.name = name


def new_figure(name):
    """ Create a new figure named name if it do not exist yet and return the object """

    width, height = bf.get_screen_size()
    if name == 'New Figure':
        fig = plt.figure(figsize=(width, height-3.2))
    else:
        fig = plt.figure(name, figsize=(width, height-3.2))
    return fig


def convert_string_to_pymath(strin):
    """ Convert a string to a 'math' format """

    return '$' + strin.replace(' ', '\ ') + '$'


def subplot_title_indexing(subplot_nb, nb_cols, nb_rows):
    """
    :param subplot_nb: number of the subplot
    :param nb_cols: number of columns in the figure object
    :param nb_rows: number of rows in the figure object
    """

    if nb_rows == 1 and nb_cols == 1:
        return ''
    else:
        return [' ' + f + ')' for f in list(string.ascii_lowercase)][subplot_nb - 1]

