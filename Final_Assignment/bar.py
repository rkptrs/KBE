import tkinter as tk
from tkinter.ttk import Progressbar
from tkinter import ttk


class bar:
    def __init__(self):
        self.parent = tk.Tk()
        self.parent.title("Calculating...")
        self.parent.geometry('500x22')
        self.style = ttk.Style()
        self.style.configure("black.Horizontal.TProgressbar", background='green')
        self.bar = Progressbar(self.parent, length=500, style='black.Horizontal.TProgressbar')
        self.bar.grid(column=0, row=0)

    def update(self, value):
        self.bar['value'] = value
        self.parent.update()

    def kill(self):
        self.parent.withdraw()

