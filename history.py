import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import sqlite3 as sq
import pathlib
from PIL import Image, ImageTk

# importing the required module
import matplotlib
import matplotlib.pyplot as plt

mod_path = pathlib.Path(__file__).parent

# Need to use this if no interactive window.
matplotlib.use('Agg')


# Plots the Calorie history bar chart along with the 3 lines showing the maintain, slow weight loss, and fast weight
# loss targets.
class CalorieHistoryPlotter:
    def __init__(self, max_plot_points):
        matplotlib.pyplot.rcParams["savefig.format"] = 'jpg'
        self.max_plot_points = max_plot_points
        self.label_increment = 1

    def plot_save(self, calorie_history, maintain, slow_loss, fast_loss, file_name):

        # print("plotting")
        x_data = []
        y_data = []

        # Build X/Y data
        for key in calorie_history:
            x_data.append(key)
            y_data.append(int(calorie_history[key]))

        # Trim to the max history
        x_data = x_data[-self.max_plot_points:]
        y_data = y_data[-self.max_plot_points:]

        # Set up the plot
        fig, ax = plt.subplots(figsize=(6.25, 4))

        # Bar Plot

        plt.axhline(y=maintain, linewidth=1, color='r')
        plt.axhline(y=slow_loss, linewidth=1, color='y')
        plt.axhline(y=fast_loss, linewidth=1, color='g')

        bar_graph = ax.bar(x_data, y_data)
        ax.bar_label(bar_graph)

        # rotate and align the tick labels so they look better
        fig.autofmt_xdate()

        # naming the x axis
        matplotlib.pyplot.xlabel('Date')
        # naming the y axis
        matplotlib.pyplot.ylabel('Calorie History')

        # giving a title to my graph
        matplotlib.pyplot.title('Calorie History')

        matplotlib.pyplot.savefig(file_name)


# Class to manage the updating of the history graph.
class HistoryGrapher(tk.Frame):
    def __init__(self, frame):
        tk.Frame.__init__(self, frame)
        img = ImageTk.PhotoImage(Image.open('calorie_history_graph.jpg'))
        self.graph_label = tk.Label(frame, image=img)
        self.graph_label.image = img
        self.graph_label.grid(column=0, row=0)
        #self.update_graph()

    # Update the graph as it changes over time.
    def update_graph(self):
        img = ImageTk.PhotoImage(Image.open('calorie_history_graph.jpg'))
        self.graph_label.configure(image=img)
        self.graph_label.image = img
        self.after(60*1000, self.update_graph) # Update after 10 minutes


# Class to create the Calorie History
class CalorieHistoryFrame(tk.Frame):
    def __init__(self, db_con, frame):
        tk.Frame.__init__(self, frame)

        self.history_db_con = db_con
        self.frame = frame

        temp_label = tk.Label(self.frame, text="Temp", fg="Black", font=("Helvetica", 15))
        temp_label.grid(column=0, row=0)

        # Create the Food Data Tree
        history_tree_frame = tk.Frame(self.frame)
        self.create_calorie_history_tree(history_tree_frame)
        history_tree_frame.grid(column=0, row=0)

    def create_calorie_history_tree(self, history_tree_frame):

        #temp_label = tk.Label(history_tree_frame, text="Temp", fg="Black", font=("Helvetica", 15))
        #temp_label.grid(column=1, row=0)
        # Set up frame to have 2 columns
        history_tree_frame.columnconfigure(0, weight=4)
        history_tree_frame.columnconfigure(1, weight=1)
        history_tree_frame.columnconfigure(2, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.history_tree = ttk.Treeview(history_tree_frame, columns=('db_id','Date', 'Weight', 'kCal'),
                                           show='headings', height=18)

        self.history_tree["displaycolumns"] = ('Date', 'kCal')

        self.history_tree.column('Date', anchor=tk.CENTER, width=100)
        # self.history_tree.column('Weight', anchor=tk.CENTER, width=80)
        self.history_tree.column('kCal', anchor=tk.E, width=50)

        self.history_tree.heading('Date', text="Date")
        self.history_tree.heading('kCal', text="kCal")

        self.history_tree.grid(column=0, row=0)
        sb = ttk.Scrollbar(history_tree_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.history_tree.config(yscrollcommand=sb.set)
        sb.config(command=self.history_tree.yview)

    # Populate the history Tree View. search_date is used to get the information for that date.
    def populate_history(self, search_date=None):
        self.history_tree.delete(*self.history_tree.get_children())

        with self.history_db_con:
            if search_date is None:
                print("search is None")
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History")
            else:
                #Search for today's calories
                print(f"Search String {search_date}")
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History"
                    " WHERE Date LIKE ?",(search_date,))

        # Group the data per date and calculate total calories per date
        calorie_history = {}

        for item in history_data:
            print(item[1][:10], item[3])

            key = item[1][5:10]
            if key in calorie_history.keys():
                calorie_history[key] = calorie_history[key] + item[3]
            else:
                calorie_history[key] = item[3]

        for key in calorie_history:
            print("Totals:", key, calorie_history[key])

        # Plot the last 2 weeks
        print("updating graph")
        calorie_plotter = CalorieHistoryPlotter(14)
        calorie_plotter.plot_save(calorie_history, 2300, 2100, 1800, 'calorie_history_graph.jpg')

        self.history_tree.tag_configure('odd', font=("default",12), background='light grey')
        self.history_tree.tag_configure('even', font=("default",12))

        index =0
        self.todays_calories = 0

        for key in calorie_history:
            if index %2:
                self.history_tree.insert(parent='', index=index, values=(0, key, 0, calorie_history[key]),
                                         tags=('even'))
            else:
                self.history_tree.insert(parent='', index=index, values=(0, key, 0, calorie_history[key]),
                                         tags=('odd'))
            index = index + 1

            #self.todays_calories = self.todays_calories + int(item[3])
            #print(self.todays_calories)

        # self.todays_calories_value_label.configure(text = (f"{self.todays_calories:.0f} kCal"))
        self.after(60*1000, self.populate_history) # Update once an hour - to ensure the day change gets included


# Class to manaage the history frame of the Application.
class HistoryFrame():

    def __init__(self, frame):
        self.master_frame = frame

        #history_label = tk.Label(self.master_frame, text="History", fg="Black", font=("Helvetica", 15))
        # Connection into the history data
        self.history_db_con = sq.connect(f'{mod_path}/history.db')

        # There are two frames - table of calorie history and a graph of that data.
        self.calorie_history_frame = tk.Frame(self.master_frame)
        self.graph_frame = tk.Frame(self.master_frame)

        # Object for the Calorie History.
        self.calorie_history = CalorieHistoryFrame(self.history_db_con, self.calorie_history_frame)
        self.calorie_history.populate_history()

        #temp_label = tk.Label(self.calorie_history_frame, text="Temp", fg="Black", font=("Helvetica", 15))
        #temp_label.grid(column=0, row=0)

        #history_label.grid(column=0, row=0)
        #history_label.grid(column=0, row=0)

        history_grapher = HistoryGrapher(self.graph_frame)
        time.sleep(15)
        history_grapher.update_graph()

        self.calorie_history_frame.grid(column=0, row=0)
        self.graph_frame.grid(column=1, row=0)


