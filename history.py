import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import sqlite3 as sq
import pathlib
import numpy
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

        data = []
        # Build X/Y data
        for key in calorie_history:
            record = [calorie_history[key]['date'], key, calorie_history[key]['calories consumed'],
                        calorie_history[key]['calories expended']]
            #print(record)
            data.append(record)
        data.sort()

        #print(data[0])

        # Trim to the max history
        data = data[-self.max_plot_points:]

        x_data=[]
        y_consumed_data=[]
        y_expended_data=[]

        for i in range(len(data)):
            x_data.append(data[i][1])
            y_consumed_data.append(data[i][2])
            y_expended_data.append(data[i][3])

        print(x_data, y_consumed_data)

        # Set up the plot
        fig, ax = plt.subplots(figsize=(6.25, 4))

        # Bar Plot

        plt.axhline(y=maintain, linewidth=1, color='r')
        plt.axhline(y=slow_loss, linewidth=1, color='y')
        plt.axhline(y=fast_loss, linewidth=1, color='g')

        #ax.plot(x_data, y_data)
        width = 0.35

        x = numpy.arange(len(x_data))  # the label locations

        bar_graph1 = ax.bar(x_data, y_consumed_data, width, label='Consumed')
        bar_graph2 = ax.bar(x_data, y_expended_data, width, label='Expended')
        ax.bar_label(bar_graph1)
        ax.bar_label(bar_graph2)

        # rotate and align the tick labels so they look better
        fig.autofmt_xdate()

        # naming the x axis
        matplotlib.pyplot.xlabel('Date')
        # naming the y axis
        matplotlib.pyplot.ylabel('Calorie History')

        # giving a title to my graph
        matplotlib.pyplot.title('Calorie History')

        matplotlib.pyplot.savefig(file_name)

    # Sorter for history date - by date.
    def history_sort(self, record):
        return record['date']


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
        self.after(60*1000*1, self.update_graph) # Update after 13 minutes


# Class to create the Calorie History
class CalorieHistoryFrame(tk.Frame):
    def __init__(self, db_con, frame, google_fit_if):
        tk.Frame.__init__(self, frame)

        self.history_db_con = db_con
        self.frame = frame

        # Set up reference to the Google Fit Interface, which has the data of spent calories.
        self.google_fit_if = google_fit_if

        temp_label = tk.Label(self.frame, text="Temp", fg="Black", font=("Helvetica", 15))
        temp_label.grid(column=0, row=0)

        # Create the Food Data Tree
        history_tree_frame = tk.Frame(self.frame)
        self.create_calorie_history_tree(history_tree_frame)
        history_tree_frame.grid(column=0, row=0)
        self.last_calorie_history = None
        self.todays_calories = 0
        self.calorie_plotter = CalorieHistoryPlotter(14)

    # Create the tree view object.
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

        self.history_tree.column('Date', anchor=tk.W, width=110)
        # self.history_tree.column('Weight', anchor=tk.CENTER, width=80)
        self.history_tree.column('kCal', anchor=tk.E, width=50)

        self.history_tree.heading('Date', text="Date")
        self.history_tree.heading('kCal', text="kCal")

        self.history_tree.grid(column=0, row=0)
        sb = ttk.Scrollbar(history_tree_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.history_tree.config(yscrollcommand=sb.set)
        sb.config(command=self.history_tree.yview)

    # Populate the history Tree View.
    def populate_history(self):
        self.history_tree.delete(*self.history_tree.get_children())

        # Get the history of calorie consumption from the database.
        with self.history_db_con:
            history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History")

        # Group the data per date and calculate total calories per date
        calorie_history = {}

        for item in history_data:
            date = datetime.strptime(item[1][:10],"%Y-%m-%d").strftime('%Y-%m-%d')
            print(date)

            day_date = datetime.strptime(item[1][:10],"%Y-%m-%d").strftime('%a %d %b')

            # print(calorie_history.keys())
            if day_date in calorie_history.keys():
                calorie_history[day_date]['calories consumed'] = calorie_history[day_date]['calories consumed']+ item[3]
            else:
                history_rec = {'date':date, 'calories consumed': item[3],'calories expended': 0}
                #print(history_rec)
                calorie_history[day_date] = history_rec

        # Get the data for calories expended and add to the dictionary array. If no data of consumed calories, then
        # set to zero.
        calories_expended = self.google_fit_if.return_records()
        for item in calories_expended:
            #print(item)
            date = datetime.strptime(item[3][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
            day_date = datetime.strptime(item[3][:10], '%Y-%m-%d').strftime('%a %d %b')

            if day_date in calorie_history.keys():
                calorie_history[day_date]['calories expended'] = calorie_history[day_date]['calories expended']+ item[5]
            else:
                history_rec = {'date':date, 'calories consumed': 0,'calories expended': item[5]}
                #print(history_rec)
                calorie_history[day_date] = history_rec

        # Plot the last 2 weeks
        #calorie_history.sort(key = self.history_sort())

        if self.last_calorie_history is None or self.last_calorie_history != calorie_history:
            #print("updating graph")

            self.calorie_plotter.plot_save(calorie_history, 2300, 2100, 1800, 'calorie_history_graph.jpg')

        self.history_tree.tag_configure('odd', font=("fixedsys",12), background='light grey')
        self.history_tree.tag_configure('even', font=("fixedsys",12))

        index =0

        for key in calorie_history:
            if index %2:
                self.history_tree.insert(parent='', index=index,
                                         values=(0, key, 0, calorie_history[key]['calories consumed']),
                                         tags='even')
            else:
                self.history_tree.insert(parent='', index=index,
                                         values=(0, key, 0, calorie_history[key]['calories consumed']),
                                         tags='odd')
            index = index + 1

            #self.todays_calories = self.todays_calories + int(item[3])
            ##print(self.todays_calories)

        self.last_calorie_history = calorie_history

        # self.todays_calories_value_label.configure(text = (f"{self.todays_calories:.0f} kCal"))
        self.after(60*1000*1, self.populate_history) # Update every 7 minutes - to ensure the day change gets included


# Class to manaage the history frame of the Application.
class HistoryFrame:

    def __init__(self, frame, google_fit_if):
        self.master_frame = frame

        #history_label = tk.Label(self.master_frame, text="History", fg="Black", font=("Helvetica", 15))
        # Connection into the history data
        self.history_db_con = sq.connect(f'{mod_path}/history.db')

        # There are two frames - table of calorie history and a graph of that data.
        self.calorie_history_frame = tk.Frame(self.master_frame)
        self.graph_frame = tk.Frame(self.master_frame)

        # Object for the Calorie History.
        self.calorie_history = CalorieHistoryFrame(self.history_db_con, self.calorie_history_frame, google_fit_if)
        self.calorie_history.populate_history()

        #temp_label = tk.Label(self.calorie_history_frame, text="Temp", fg="Black", font=("Helvetica", 15))
        #temp_label.grid(column=0, row=0)

        #history_label.grid(column=0, row=0)
        #history_label.grid(column=0, row=0)

        history_grapher = HistoryGrapher(self.graph_frame)
        history_grapher.update_graph()

        self.calorie_history_frame.grid(column=0, row=0)
        self.graph_frame.grid(column=1, row=0)


