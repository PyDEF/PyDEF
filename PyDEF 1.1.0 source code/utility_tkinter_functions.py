""" Set of useful functions for Tkinter and ttk
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import ttk


def disable_frame(frame):
    """ Disable all child widgets of frame and all child widgets of its subframes """
    for child in frame.winfo_children():
        if child.__class__ is ttk.Frame:
            disable_frame(child)
        else:
            child.configure(state='disable')


def enable_frame(frame):
    """ Enable all child widgets of frame and all child widgets of its subframes """
    for child in frame.winfo_children():
        if child.__class__ is ttk.Frame:
            enable_frame(child)
        else:
            child.configure(state='enable')


def centre_window(window):
    """ Centre the window 'window' """

    window.update_idletasks()

    # Screen
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()

    # Window
    ww = window.winfo_width()
    wh = window.winfo_height()

    window.geometry('%dx%d%+d%+d' % (ww, wh, (sw - ww)/2, (wh - sh)/2))
