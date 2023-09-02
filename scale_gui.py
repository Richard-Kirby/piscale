#!/usr/bin python3

import sys
import tkinter as tk
from tkinter import ttk
import pathlib
from PIL import Image, ImageTk
import cProfile

# HX711 library for the scale interface.
import HX711 as HX

# Import the history frame classes
import history

# Import the Body Weight classes
import body_weight
import google_fit_if
import daily
import config  # some globals to use.
import logging.config

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('scaleLogger')
logger.setLevel(logging.DEBUG)

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

# Main Application for the Scale GUI
class App(ttk.Frame):
    def __init__(self, master=None):

        style = ttk.Style()
        style.theme_use("awdark")

        ttk.Frame.__init__(self, master)

        self.selected_item_cal_label = None
        self.weight = Weight()

        self.master = master

        main_frame = ttk.Frame()


        # Initialise the old weight. Old weight is used to determine if display update is needed.
        self.old_weight = None

        # Update the weight, which will happen regularly after this call.
        style.configure('piscale.TLabel', font=('Helvetica', 10))
        style.configure('piscale_weight.TLabel', font=('Helvetica', 20))

        self.weight_disp = ttk.Label(main_frame, text="", style='piscale_weight.TLabel')

        self.weight.update_weight()

        # Notebook creation
        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True)

        # create frames
        daily_frame = ttk.Frame(notebook)
        history_frame = ttk.Frame(notebook)
        body_weight_frame = ttk.Frame(notebook)

        daily_frame.grid(column=0, row=0)

        # print(f"{style.theme_names()}")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")

        style.configure('piscale.TButton', font=('Helvetica', 12))


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
        zero_btn = ttk.Button(main_frame, text="Zero", command=self.weight.zero, style = 'piscale.TButton', width=5)
        exit_btn = ttk.Button(main_frame, text="Exit", command=self.exit, style = 'piscale.TButton', width=5)

        logo_img = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/logo-no-background.png').resize((280, 40)))
        # logo_img = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/logo-no-background.png'))
        logo = ttk.Label(main_frame, image=logo_img)
        logo.grid(column=2, row=0, sticky='sw')
        logo.image = logo_img

        self.weight_disp.grid(column=0, row=0, columnspan=1, sticky='e')
        zero_btn.grid(column=1, row=0, sticky='w')
        # self.time_label.grid(column=2, row=0, sticky='e')
        exit_btn.grid(column=3, row=0, sticky='e')

        main_frame.grid(column=0, row=0)

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

    # Update the display of the weight - happens regularly.
    def update_weight_display(self):

        self.weight.update_weight()
        curr_weight = self.weight.get_weight()

        # Update the weight display only if it has changed.
        if self.old_weight is None or abs(self.old_weight - curr_weight) > 2.0:
            weight_display = f"{float(curr_weight):03.0f}g"
            logger.debug(f"Updating weight display {weight_display} used to be {self.old_weight}")
            self.weight_disp.configure(text=weight_display)
            self.old_weight = curr_weight

        self.after(600, self.update_weight_display)

    # Exit function
    @staticmethod
    def exit():
        quit()


root = tk.Tk()

root.tk.call('lappend', 'auto_path', f'{mod_path}/themes/awthemes-10.4.0')
root.tk.call('package', 'require', 'awdark')

#root.winfo_rgb()

style = ttk.Style().theme_use("awdark")

# cProfile.run('app = App(root)', 'piscale_profile.log')
app = App(master = root)
root.wm_title("Piscale Calorie Minder - a Richard Kirby project")
logger.info("Start Up GUI")

root.attributes('-fullscreen', True)
# app.update_clock()
root.mainloop()
