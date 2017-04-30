"""
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""


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
