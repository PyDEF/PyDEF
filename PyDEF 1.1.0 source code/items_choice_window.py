""" Simple window with two listbox for choosing elements in and out
    version: 1.0.0
    author: Emmanuel Pean
    e-mail: emmanuel.pean@gmail.com
"""

import ttk
import Tkinter as tk
import tkMessageBox as mb

import utility_tkinter_functions as ukf


class Items_Choice_Window(tk.Toplevel):
    """ Window consisting of two listbox. The listbox on the rights contains elements which are returned
     The list on the left contains elements which are not returned"""

    def __init__(self, parent, items, items_on, output_var, label_on, label_off):
        """
        :param parent: parent window
        :param items: list of all items
        :param items_on: list of items which are used
        :param output_var: Tkinter StringVar
        :param label_on: label for the list of used items
        :param label_off: label for the list of non used items
        """

        tk.Toplevel.__init__(self, parent)
        self.title('Select items')
        self.resizable(False, False)
        self.bind('<Control-w>', lambda event: cancel())

        self.parent = parent

        self.icon = parent.icon
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        self.main_frame = ttk.Frame(self)  # Main ttk frame
        self.main_frame.pack(expand=True, fill='both')

        # DOS type choice from previous window
        items_off = list(set(items) - set(items_on))

        # ------------------------------------------------- ITEMS ON ---------------------------------------------------

        self.on_frame = ttk.LabelFrame(self.main_frame, text=label_on)
        self.on_frame.grid(row=0, column=0)

        self.list_on = tk.Listbox(self.on_frame, width=20)
        self.yscrollbar_on = ttk.Scrollbar(self.on_frame, orient='vertical')

        self.list_on.pack(side='left', fill='both', expand=True)
        self.yscrollbar_on.pack(side='right', fill='y')

        self.list_on.config(yscrollcommand=self.yscrollbar_on.set)
        self.yscrollbar_on.config(command=self.list_on.yview)

        [self.list_on.insert('end', f) for f in items_on]

        # -------------------------------------------------- ITEMS OFF -------------------------------------------------

        self.frame_off = ttk.LabelFrame(self.main_frame, text=label_off)
        self.frame_off.grid(row=0, column=2)

        self.list_off = tk.Listbox(self.frame_off, width=20)  # list containing element non plotted
        self.yscrollbar_off = ttk.Scrollbar(self.frame_off, orient='vertical')

        self.list_off.pack(side='left', fill='both', expand=True)
        self.yscrollbar_off.pack(side='right', fill='y')

        self.list_off.config(yscrollcommand=self.yscrollbar_off.set)
        self.yscrollbar_off.config(command=self.list_off.yview)

        [self.list_off.insert('end', f) for f in items_off]

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=1, padx=5)

        def remove_selection():
            """ Remove selected elements in the 'on' list and add them to the 'off' list """
            selection = self.list_on.curselection()
            if len(selection) != 0:
                for selected in selection:
                    items_ids = self.list_on.get(selected)
                    self.list_off.insert(0, items_ids)
                    self.list_on.delete(selected)

        def add_selection():
            """ Add selected elements to the 'on' list and remove them from the 'off' list """
            selection = self.list_off.curselection()
            if len(selection) != 0:
                for selected in selection:
                    items_ids = self.list_off.get(selected)
                    self.list_on.insert(0, items_ids)
                    self.list_off.delete(selected)

        def add_all():
            """ Add all items to the 'on' list and remove them from the 'off' list """
            self.list_off.delete(0, 'end')
            self.list_on.delete(0, 'end')
            [self.list_on.insert(0, f) for f in items]

        def remove_all():
            """ Remove all items from the 'on' list and add them to the 'off' list """
            self.list_on.delete(0, 'end')
            self.list_off.delete(0, 'end')
            [self.list_off.insert(0, f) for f in items]

        ttk.Button(self.button_frame, text='>', command=remove_selection).pack(side='top')
        ttk.Button(self.button_frame, text='>>', command=remove_all).pack(side='top')
        ttk.Button(self.button_frame, text='<', command=add_selection).pack(side='top')
        ttk.Button(self.button_frame, text='<<', command=add_all).pack(side='top')

        def add_selected(event):
            """ Add the selected item to the 'on' list and remove it from the 'off' list when "event" happens """
            widget = event.widget
            widget.curselection()
            add_selection()

        def remove_selected(event):
            """ Add the selected item to the 'off' list and remove it from the 'on' list when "event" happens """
            widget = event.widget
            widget.curselection()
            remove_selection()

        self.list_on.bind('<Double-Button-1>', remove_selected)  # remove element when double-clicked
        self.list_off.bind('<Double-Button-1>', add_selected)  # add item when double-clicked

        # ------------------------------------------------ MAIN BUTTONS ------------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=1, column=0, columnspan=3)

        def save():
            """ Save the choice and close the window """
            choice = list(self.list_on.get(0, 'end'))
            if len(choice) == 0:
                mb.showerror('Error', 'Select at least one item', parent=self)
                return None
            else:
                output_var.set(','.join(choice))
                print(output_var.get())
            self.destroy()

        def cancel():
            """ Save the initial items on and close the window """
            output_var.set(','.join(items_on))
            self.destroy()

        ttk.Button(self.main_button_frame, text='OK', command=save).pack(side='left')
        ttk.Button(self.main_button_frame, text='Cancel', command=cancel).pack(side='right')

        self.protocol('WM_DELETE_WINDOW', cancel)

        ukf.centre_window(self)
