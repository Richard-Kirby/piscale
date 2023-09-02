import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import sqlite3 as sq
import pathlib
import numpy
from PIL import Image, ImageTk
import configparser

# importing the required module
import matplotlib
import matplotlib.pyplot as plt

import logging.config

logging.config.fileConfig('logging.conf')
hlogger = logging.getLogger('historyLogger')
hlogger.setLevel(logging.INFO)

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

    def plot_save(self, calorie_history, file_name):
        # print(data[0])

        # Trim to the max history
        calorie_history = calorie_history[-self.max_plot_points:]

        x_data = []
        y_consumed_data = []
        y_expended_data = []
        y_moving_average_in = []
        y_moving_average_out = []


        for i in range(len(calorie_history)):
            x_data.append(calorie_history[i][1])
            y_consumed_data.append(calorie_history[i][2])
            y_expended_data.append(round(calorie_history[i][3]))
            y_moving_average_in.append(round(calorie_history[i][4]))
            y_moving_average_out.append(round(calorie_history[i][5]))

        # print(x_data, y_consumed_data)
        plt.style.use('dark_background')

        # Set up the plot
        fig, ax = plt.subplots(figsize=(6.25, 4))

        # Bar Plot

        # ax.plot(x_data, y_data)
        width = 0.40

        x = numpy.arange(len(x_data))  # the label locations
        # print(x)

        # Turn the grid on.
        #matplotlib.pyplot.grid(True, axis ='y', linestyle=':', color ='0.8')

        bar_graph1 = ax.bar(x - width / 2, y_consumed_data, width, label='kCal In', color='#000000',
                            edgecolor='#23A2DC', zorder =0)
        bar_graph2 = ax.bar(x + width / 2, y_expended_data, width, label='kCal Out', color='#000000',
                            edgecolor='#DC5D23', zorder =0)

        #plt.plot(x, y_consumed_data)
        #plt.plot(x, y_expended_data)
        plt.plot(x, y_moving_average_in, label='kCal Moving Avg In', linewidth=3, color='#46DC23', zorder =5)
        plt.plot(x, y_moving_average_out, label='kCal Moving Avg Out', linewidth=3, color='#B923DC', zorder =5)

        ax.bar_label(bar_graph1, rotation='vertical', padding=3, color = 'w', zorder =10)
        ax.bar_label(bar_graph2, rotation='vertical', padding=3, color = 'w', zorder =10)

        ax.legend(loc='lower left')
        ax.set_xticks(x, x_data)

        # rotate and align the tick labels so they look better
        fig.autofmt_xdate()
        # fig.tight_layout()

        # naming the x axis
        matplotlib.pyplot.xlabel('Date')

        # naming the y axis
        matplotlib.pyplot.ylabel('Calorie History', )
        matplotlib.pyplot.ylim(0, 3000)

        # giving a title to my graph
        matplotlib.pyplot.title('Calorie History')

        matplotlib.pyplot.savefig(file_name)

        # Close the plot to reduce memory usage.
        matplotlib.pyplot.close()

    # Sorter for history date - by date.
    @staticmethod
    def history_sort(record):
        return record['date']


# Class to manage the updating of the history graph.
class HistoryGrapher(ttk.Frame):
    def __init__(self, frame):
        ttk.Frame.__init__(self, frame)
        img = ImageTk.PhotoImage(Image.open('calorie_history_graph.jpg'))
        self.graph_label = ttk.Label(frame, image=img)
        self.graph_label.image = img
        self.graph_label.grid(column=0, row=0)
        # self.update_graph()

    # Update the graph as it changes over time.
    def update_graph(self):
        img = ImageTk.PhotoImage(Image.open('calorie_history_graph.jpg'))
        self.graph_label.configure(image=img)
        self.graph_label.image = img
        self.after(60 * 1000 * 13, self.update_graph)  # Update after 13 minutes


# Class to create the Calorie History
class CalorieHistoryFrame(ttk.Frame):
    def __init__(self, db_con, frame, moving_averge_days, google_fit_if):
        ttk.Frame.__init__(self, frame)

        self.history_tree = None
        self.history_db_con = db_con
        self.frame = frame
        self.moving_average_days = int(moving_averge_days)

        # Set up reference to the Google Fit Interface, which has the data of spent calories.
        self.google_fit_if = google_fit_if

        temp_label = ttk.Label(self.frame, text="Temp", style = 'piscale.TButton')
        temp_label.grid(column=0, row=0)

        # Create the Food Data Tree
        history_tree_frame = ttk.Frame(self.frame)
        self.create_calorie_history_tree(history_tree_frame)
        history_tree_frame.grid(column=0, row=0)
        self.last_calorie_history = None
        self.todays_calories = 0
        self.calorie_plotter = CalorieHistoryPlotter(14)
        self.prev_history_datetime = None
        self.prev_expended_datetime = None

        # Connect to the DB.
        self.calories_in_out_db = sq.connect(f'{mod_path}/calories_in_out.db', check_same_thread=False)

        # Create the Calorie Spent DB table if not already created. This table stores the calories expended by the
        # user through exercise and normal body functions such as breathing.
        with self.calories_in_out_db:

            # create cursor object - this part is to create the initial table if it doesn't exist yet.
            cur = self.calories_in_out_db.cursor()

            list_of_tables = cur.execute(
                """SELECT name FROM sqlite_master WHERE type='table'
                AND name='CaloriesInOut'; """).fetchall()

            # print(list_of_tables)
            if list_of_tables == []:
                print("Table not found, creating CaloriesInOut")

                # Create the table as it wasn't found.
                self.calories_in_out_db.execute(""" CREATE TABLE CaloriesInOut(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        rec_date TEXT,
                        epoch_time TEXT, 
                        CaloriesIn INTEGER,
                        CaloriesOut INTEGER, 
                        CaloriesInMovingAverage INTEGER,
                        CaloriesOutMovingAverage INTEGER
                        );
                    """)

    # Create the tree view object.
    def create_calorie_history_tree(self, history_tree_frame):

        # temp_label = tk.Label(history_tree_frame, text="Temp", fg="Black", font=("Helvetica", 15))
        # temp_label.grid(column=1, row=0)
        # Set up frame to have 2 columns
        history_tree_frame.columnconfigure(0, weight=4)
        history_tree_frame.columnconfigure(1, weight=1)
        history_tree_frame.columnconfigure(2, weight=1)
        history_tree_frame.columnconfigure(3, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.history_tree = ttk.Treeview(history_tree_frame, columns=('db_id', 'Date', 'Weight', 'kCal In', 'kCal Out'),
                                         show='headings', height=18)

        self.history_tree["displaycolumns"] = ('Date', 'kCal In', 'kCal Out')

        self.history_tree.column('Date', anchor=tk.W, width=80)
        # self.history_tree.column('Weight', anchor=tk.CENTER, width=80)
        self.history_tree.column('kCal In', anchor=tk.E, width=40)
        self.history_tree.column('kCal Out', anchor=tk.E, width=40)

        self.history_tree.heading('Date', text="Date")
        self.history_tree.heading('kCal In', text="kCal In")
        self.history_tree.heading('kCal Out', text="kCal Out")

        self.history_tree.grid(column=0, row=0)
        sb = ttk.Scrollbar(history_tree_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.history_tree.config(yscrollcommand=sb.set)
        sb.config(command=self.history_tree.yview)

    # Populate the history Tree View.
    def populate_history(self):

        # Get the last record for the consumed meals.
        last_history_datetime = self.history_db_con.execute('SELECT * FROM History ORDER BY id DESC LIMIT 1').fetchone()[1]
        last_calorie_expended_datetime = self.google_fit_if.return_records(num_records=1)[0][3]
        # print(f"{last_history_datetime} {last_calorie_expended_datetime}")

        # Only update the history information if it has changed. See if it changed by checking he last records
        # against what was previously processed.
        hlogger.info(f"Previous data {last_history_datetime} {self.prev_history_datetime}"
                    f"{last_calorie_expended_datetime} {self.prev_expended_datetime}")

        # Only update the history information if it has changed. See if it changed by checking he last records
        # against what was previously processed.
        # print(f"Previous data {last_history_datetime} {self.prev_history_datetime}"
        #      f"{last_calorie_expended_datetime} {self.prev_expended_datetime}")

        if last_calorie_expended_datetime != self.prev_expended_datetime or \
                last_history_datetime != self.prev_history_datetime:

            hlogger.info(f"Updating history table {last_history_datetime} {self.prev_history_datetime}"
                        f"{last_calorie_expended_datetime} {self.prev_expended_datetime}")

            self.history_tree.delete(*self.history_tree.get_children())

            # Get the history of calorie consumption from the database.
            with self.history_db_con:
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History")

            # Group the data per date and calculate total calories per date
            calorie_history = {}

            for item in history_data:
                date = datetime.strptime(item[1][:10], "%Y-%m-%d").strftime('%Y-%m-%d')

                day_date = datetime.strptime(item[1][:10], "%Y-%m-%d").strftime('%a %d/%m/%y')

                # print(calorie_history.keys())
                if day_date in calorie_history.keys():
                    calorie_history[day_date]['calories consumed'] = calorie_history[day_date]['calories consumed'] \
                                                                     + item[3]
                else:
                    history_rec = {'date': date, 'calories consumed': item[3], 'calories expended': 0}
                    # print(history_rec)
                    calorie_history[day_date] = history_rec

            # Get the data for calories expended and add to the dictionary array. If no data of consumed calories, then
            # set to zero.
            calories_expended = self.google_fit_if.return_records()
            for item in calories_expended:
                # print(item)
                date = datetime.strptime(item[3][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                day_date = datetime.strptime(item[3][:10], '%Y-%m-%d').strftime('%a %d/%m/%y')

                if day_date in calorie_history.keys():
                    calorie_history[day_date]['calories expended'] = calorie_history[day_date]['calories expended'] \
                                                                     + item[5]
                    #hlogger.debug(f"Building Calories Expended {day_date} {item[5]} "
                    #             f"{calorie_history[day_date]['calories expended']}")
                else:
                    history_rec = {'date': date, 'calories consumed': 0, 'calories expended': item[5]}
                    # print(history_rec)
                    calorie_history[day_date] = history_rec

            # Sorting is needed as out of order records may have been added.
            sorted_data = []

            # Build X/Y data
            for key in calorie_history:
                record = [calorie_history[key]['date'], key, calorie_history[key]['calories consumed'],
                          round(calorie_history[key]['calories expended'])]
                # print(record)
                sorted_data.append(record)
            sorted_data.sort()

            hlogger.debug(f"Sorted Data {sorted_data} processing")

            # Plot the last 2 weeks
            # calorie_history.sort(key = self.history_sort())

            # if self.last_calorie_history is None or self.last_calorie_history != calorie_history:

            self.history_tree.tag_configure('odd', font=("fixedsys", 8), background='gray30')
            self.history_tree.tag_configure('even', font=("fixedsys", 8))

            index = 0

            with self.calories_in_out_db:

                # Delete all the records in the DB - it will be repopulated below.
                self.calories_in_out_db.execute("DELETE FROM CaloriesInOut;")

                moving_average_kcals_in_list = []
                moving_average_kcals_in = 0

                moving_average_kcals_out_list = []
                moving_average_kcals_out = 0

                # Create the table for viewing and also create the temporary database of in/out/moving averages.
                for i in sorted_data:
                    insert_data = [0, i[1], 0, i[2], i[3]]

                    # Building up the table.
                    if index % 2:
                        self.history_tree.insert(parent='', index=index,
                                                 values=insert_data,
                                                 tags='even')
                    else:
                        self.history_tree.insert(parent='', index=index,
                                                 values=insert_data,
                                                 tags='odd')
                    index = index + 1

                    # Calculate the moving average by changing the window under consideration and dividing by the
                    # length of the window. 0 calorie days are ignored as they may occur if user hasn't entered
                    # any values.
                    if i[2] > 0:
                        length = len(moving_average_kcals_in_list)
                        if length  == self.moving_average_days:
                            moving_average_kcals_in_list.pop(0)
                            moving_average_kcals_in_list.append(i[2])
                        else:
                            moving_average_kcals_in_list.append(i[2])
                            length = len(moving_average_kcals_in_list)

                        if length > 0:
                            moving_average_kcals_in = int(sum(moving_average_kcals_in_list)/length)

                        # print(f"{length} {moving_average_kcals_in} {moving_average_kcals_in_list}")

                    # Calculate the moving average by changing the window under consideration and dividing by the
                    # length of the window. 0 calorie days are ignored as they may occur if user hasn't entered
                    # any values.
                    if i[3] > 0:
                        length = len(moving_average_kcals_out_list)
                        if length  == self.moving_average_days:
                            moving_average_kcals_out_list.pop(0)
                            moving_average_kcals_out_list.append(i[3])
                        else:
                            moving_average_kcals_out_list.append(i[3])
                            length = len(moving_average_kcals_out_list)

                        if length > 0:
                            moving_average_kcals_out = int(sum(moving_average_kcals_out_list)/length)

                        # print(f"{length} {moving_average_kcals_out} {moving_average_kcals_out_list}")
                    i.append(moving_average_kcals_in)
                    i.append(moving_average_kcals_out)

                    # Translate date to epoch seconds
                    epoch_time = time.mktime(time.strptime(i[0], "%Y-%m-%d"))
                    # print(epoch_time)
                    # Update database, which isn't used in the GUI, but can be accessed for additional
                    # analysis or graphing.
                    self.calories_in_out_db.execute(
                        "INSERT INTO CaloriesInOut (rec_date, epoch_time, CaloriesIn, CaloriesOut, "
                        "CaloriesInMovingAverage, CaloriesOutMovingAverage) values(?, ?, ?, ?, ?, ?)"
                        , [i[0], epoch_time, i[2], i[3], moving_average_kcals_in, moving_average_kcals_out])

                    # print(f"{self.calories_in_out_db} {i[0]} {i[1]} {i[2]} {i[3]}")

                self.calories_in_out_db.commit()

                # print(f"{sorted_data}")

                self.calorie_plotter.plot_save(sorted_data, 'calorie_history_graph.jpg')

            # Set up previous values that will be compared against.
            # self.last_calorie_history = calorie_history
            self.prev_history_datetime = last_history_datetime
            self.prev_expended_datetime = last_calorie_expended_datetime

        # self.todays_calories_value_label.configure(text = (f"{self.todays_calories:.0f} kCal"))
        self.after(60 * 1000 * 3,
                   self.populate_history)  # Update every 7 minutes - to ensure the day change gets included


# Class to manaage the history frame of the Application.
class HistoryFrame:

    def __init__(self, frame, google_fit_if):
        self.master_frame = frame

        config = configparser.ConfigParser()
        config.read('piscale.ini')

        # history_label = tk.Label(self.master_frame, text="History", fg="Black", font=("Helvetica", 15))
        # Connection into the history data
        self.history_db_con = sq.connect(f'{mod_path}/history.db')

        # There are two frames - table of calorie history and a graph of that data.
        self.calorie_history_frame = ttk.Frame(self.master_frame)
        self.graph_frame = ttk.Frame(self.master_frame)

        # Object for the Calorie History.
        self.calorie_history = CalorieHistoryFrame(self.history_db_con, self.calorie_history_frame,
                                                   int(config['calorie_history']['moving_average_days']), google_fit_if)
        self.calorie_history.populate_history()

        history_grapher = HistoryGrapher(self.graph_frame)
        history_grapher.update_graph()

        self.calorie_history_frame.grid(column=0, row=0)
        self.graph_frame.grid(column=1, row=0)
