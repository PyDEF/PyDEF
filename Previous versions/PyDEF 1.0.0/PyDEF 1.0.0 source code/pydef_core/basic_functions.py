"""
    Ensemble of various basic functions used in PyDEF
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import numpy as np
import fractions

# -------------------------------------------------- PYDEF EXCEPTIONS --------------------------------------------------


class PydefImportError(Exception):
    """ Error raised when there is an error when importing the data """
    pass


class PydefOutcarError(Exception):
    """ Error raised when the given OUTCAR file is not a valid OUTCAR file """
    pass


class PydefDoscarError(Exception):
    """ Error raised when the given DOSCAR file is not consistent with the OUTCAR file """
    pass


class PydefDefectCellError(Exception):
    """ Error raised when the given defect cell is not consistent with the host cell """
    pass


# ------------------------------------------------------ FUNCTIONS -----------------------------------------------------


def read_file(filename):
    """ Return the content of a file as a list of strings, each corresponding to a line
    :param filename: string: location and name of the file
    :return: content of filename
    """

    ofile = open(filename, 'r')
    content = ofile.read().splitlines()
    ofile.close()
    return content


def grep(content, string1, line_nb=False, string2=False, data_type='str', nb_found=None):
    """
    :param content: list of strings
    :param string1: string after which the data is located
    :param line_nb: amongst the lines which contains 'thing', number of the line to be considered
    :param string2: string before which the data is located
    :param data_type: type of the data to be returned
    :param nb_found: exact number of 'string1' to be found
    """

    found = [[f, g] for f, g in zip(content, range(len(content))) if string1 in f]

    if len(found) == 0:
        return None  # Return None if nothing was found

    if isinstance(nb_found, int):
        if len(found) != nb_found:
            raise PydefImportError('Data are not consistent')

    if line_nb is False:
        # print('%s elements found' % len(found))
        return found
    else:
        line = found[line_nb][0]

        if string2 is False:
            value = line[line.find(string1) + len(string1):]
        else:
            value = line[line.find(string1) + len(string1): line.find(string2)]

        if data_type == 'float':
            return float(value)
        if data_type == 'int':
            return int(value)
        if data_type == 'str':
            return value.strip()


def get_common_values(alist):
    """ Retrieve the common values of a set of list in 'alist' and sort them in increasing order

    :param alist: list of lists
    :return: list of common elements in the lists sorted in increasing order
    """

    common_values = range(np.max(np.concatenate(alist))+1)
    for i in alist:
        common_values = list(set(common_values) & set(i))
    return list(np.sort(common_values))


def get_gcd(alist):
    """ Compute the GCD of the elements of a list

    :param alist: list of integers
    :return: GCD of the integers
    """

    gcd = fractions.gcd(alist[0], alist[1])
    for f in range(2, len(alist)):
        gcd = fractions.gcd(gcd, alist[f])
    return gcd


def plot_sphere(radius, center, ax, lstyle='-'):
    """
    :param radius: radius of the sphere (float or int)
    :param center: position of the center of the sphere in 3D space (list or array)
    :param ax: ax in which the sphere must be plotted (mpl_toolkits.mplot3d.axes3d.Axes3D)
    :param lstyle: style of the lines of the sphere (matplotlib.lines.lineStyles)
    :return: Draw a sphere using matplotlib
    """
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 40)

    x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
    y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]

    ax.plot_surface(x, y, z, rstride=4, cstride=4, color='g', alpha=0.1, linestyle=lstyle)


def distance(point1, point2):
    """ Return the distance between 2 points in space
    :param point1: list or array of float
    :param point2: list or array of float
    :return: distance between point1 and point2
    """

    return np.sqrt(np.sum([(f - g)**2 for f, g in zip(point1, point2)]))


def heaviside(x):
    """ Heaviside function
    :param x: float or int
    :return: 0 if x < 0, 0.5 if x = 0 and 1.0 if x > 0
    """

    return 0.5 * np.sign(x) + 0.5


def float_to_str(number):
    """
    :param number: any number
    :return:
    """

    if number > 0:
        integer_str = '+' + str(int(number))
    else:
        integer_str = str(int(number))
    return integer_str


def get_screen_size():
    """ Retrieve the screen size in inches """
    import Tkinter as tk
    root = tk.Tk()
    width = root.winfo_screenmmwidth() * 0.0393701
    height = root.winfo_screenmmheight() * 0.0393701
    root.destroy()
    return [width, height]
