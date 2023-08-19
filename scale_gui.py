#!/usr/bin python3

import sys
import tkinter as tk
from tkinter import ttk
import pathlib
from PIL import Image, ImageTk


# HX711 library for the scale interface.
import HX711 as HX

import logging.config

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('scaleLogger')
logger.setLevel(logging.DEBUG)

# Import the history frame classes
import history
import daily

# Import the Body Weight classes
import body_weight
import google_fit_if
import daily
import config  # some globals to use.

mod_path = pathlib.Path(__file__).parent

class Weight:
    def __init__(self):
        self.weight = None

        # Connect to the scale and zero it out.
        # create a SimpleHX711 object using GPIO pin 14 as the data pin,
        # GPIO pin 15 as the clock pin, -370 as the reference unit, and
        # -367471 as the offset
        # This will likely have to change if using a different scale.
        self.hx = HX.SimpleHX711(14, 15, int(-370 / 1.244 / 1.00314), -367471)
        self.hx.zero()

    # Zero out the scale
    def zero(self):
        self.hx.zero()

    # Update the weight display - do this regular.
    def update_weight(self):
        # Get the current weight on the scale
        weight_str = str(self.hx.weight(5))
        # print(weight_str)
        self.weight = float(weight_str[:-2])

        # Ignore any negative weight greater than 2g - avoids flicker of -ve sign.
        if 2 > self.weight > -2:
            self.weight = 0

    def get_weight(self):
        return self.weight


class App(tk.Frame):
    def __init__(self, master=None):

        tk.Frame.__init__(self, master)
        self.selected_item_cal_label = None
        self.weight = Weight()

        self.master = master
        # Initialise the old weight. Old weight is used to determine if display update is needed.
        self.old_weight_display = None

        # Update the weight, which will happen regularly after this call.
        self.weight_disp = tk.Label(text="", fg="Red", font=("Helvetica", 30))
        self.weight.update_weight()

        # Notebook creation
        notebook = ttk.Notebook(root)
        notebook.pack(expand=True)

        # create frames
        daily_frame = tk.Frame(notebook)
        history_frame = tk.Frame(notebook)
        body_weight_frame = tk.Frame(notebook)

        daily_frame.grid(column=0, row=0)

        style = ttk.Style()
        # print(style.theme_names())
        style.theme_use("alt")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")

        # Configures a specialist scrollbar for windows that have a lot of scrolling. Inherits from Vertical.TScrolbar
        # duet to naming convention.
        style.configure("wide_scroll.Vertical.TScrollbar", arrowsize=24)

        style.configure('TNotebook.Tab', font=config.widget_font)
        #style.configure("Vertical.TScrollbar", arrowsize=24)
        notebook.add(daily_frame, text='Daily')
        notebook.add(history_frame, text='History')
        notebook.add(body_weight_frame, text='Weight')
        notebook.grid(column=0, row=1, columnspan=4, pady=0)

        # Widgets that are part of the main application
        zero_btn = tk.Button(self.master, text="Zero", command=self.weight.zero, font=config.widget_font, width=5)
        exit_btn = tk.Button(self.master, text="Exit", command=self.exit, font=config.widget_font, width=5)

        logo_img = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/logo-no-background.png').resize((280, 40)))
        # logo_img = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/logo-no-background.png'))
        logo = tk.Label(self.master, image=logo_img)
        logo.grid(column=2, row=0, sticky='sw')
        logo.image = logo_img

        self.weight_disp.grid(column=0, row=0, columnspan=1, sticky='e')
        zero_btn.grid(column=1, row=0, sticky='w')
        # self.time_label.grid(column=2, row=0, sticky='e')
        exit_btn.grid(column=3, row=0, sticky='e')

        # The daily frame has all the stuff to measure food, etc.
        self.daily_frame = daily.DailyFrame(daily_frame, self.weight)

        # Binds Return key to running the search function.
        self.master.bind('<Return>', self.daily_frame.food_data_frame.search_food_data)

        # Create the Google Fit If Object, which connects to Google Fit to get calories expended data.
        google_fit_if_obj = google_fit_if.GoogleFitIf(sys.argv)
        google_fit_if_obj.daemon = True
        google_fit_if_obj.start()

        # Create the calorie history and body weight frames.

        # Calorie history includes the Google Fit Object as it has the data for expended calories.
        self.history_frame_hdl = history.HistoryFrame(history_frame, google_fit_if_obj)

        # Body weight frame contains the measurements for the body weight from the bathroom scale.
        self.body_weight_frame_hdl = body_weight.BodyWeightFrame(body_weight_frame)

        self.update_weight_display()

    def update_weight_display(self):

        self.weight.update_weight()
        weight_display = f"{float(self.weight.get_weight()):03.0f}g"

        # Update the weight display only if it has changed.
        if self.old_weight_display is None or weight_display != self.old_weight_display:
            logger.debug(f"Updating weight display {weight_display}")
            self.weight_disp.configure(text=weight_display)
            self.old_weight_display = weight_display

        self.after(500, self.update_weight_display)


    # Exit function
    @staticmethod
    def exit():
        quit()



root = tk.Tk()

app = App(root)
root.wm_title("Piscale Calorie Minder - a Richard Kirby project")
logger.info("Start Up GUI")

root.attributes('-fullscreen', True)
# app.update_clock()
root.mainloop()
