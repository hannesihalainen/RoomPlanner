import tkinter as tk

class DialogBase(tk.Toplevel):

    def __init__(self, parent, title):
        super().__init__(parent)

        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.result = None

        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def cancel(self):
        self.result = None
        self.destroy()
