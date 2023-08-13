import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from datetime import datetime
import pathlib
from PIL import Image, ImageTk
import bathroom_scale_if

# importing the required module
import matplotlib
import matplotlib.pyplot as plt

import logging

logger = logging.getLogger("scaleLogger")
mod_path = pathlib.Path(__file__).parent

# Need to use this if no interactive window.
matplotlib.use('Agg')

bathroom_scale_if_ip_port = ("255.255.255.255", 6000)


# Plots the Body Weight history bar chart along with a line showing start weight and target
class WeightHistoryPlotter:
    def __init__(self, max_plot_points):
        matplotlib.pyplot.rcParams["savefig.format"] = 'jpg'
        self.max_plot_points = max_plot_points
        self.label_increment = 1

    # Saves the plot to a file. Makes it available for use by the application or for sending out.
    def plot_save(self, body_weight_history, start_weight, target_weight, file_name):
        # print("plotting")
        x_data = []
        y_data = []

        # Build X/Y data
        for record in body_weight_history:
            x_data.append(datetime.strptime(record[1][:10], '%Y-%m-%d').date())
            y_data.append(float(record[3]))

        # Trim to the max history
        x_data = x_data[-self.max_plot_points:]
        y_data = y_data[-self.max_plot_points:]

        # Set up the plot
        fig, ax = plt.subplots(figsize=(6.25, 4))

        # Bar Plot

        plt.axhline(y=start_weight, linewidth=1, color='r')
        plt.axhline(y=target_weight, linewidth=1, color='y')

        ax.plot(x_data, y_data, 'bx')

        # xfmt = dates.DateFormatter('%d-%m-%y')
        # ax.xaxis.set_major_formatter(xfmt)

        # ax.locator_params(axis='x', nbins=2)

        # rotate and align the tick labels so they look bette
        fig.autofmt_xdate()

        # naming the x axis
        matplotlib.pyplot.xlabel('Date')
        # naming the y axis
        matplotlib.pyplot.ylabel('Body Weight')

        # giving a title to my graph
        matplotlib.pyplot.title('Body Weight')

        # ymax = round(start_weight+10, -1)
        # ymin = round(target_weight -30, -1)

        # matplotlib.pyplot.ylim ([ymin,ymax])

        matplotlib.pyplot.savefig(file_name)

        # Close the plot to reduce memory usage.
        matplotlib.pyplot.close()


# Class to manage the updating of the history graph.
class HistoryGrapher(tk.Frame):
    def __init__(self, frame):
        tk.Frame.__init__(self, frame)
        img = ImageTk.PhotoImage(Image.open('weight_history_graph.jpg'))
        self.graph_label = tk.Label(frame, image=img)
        self.graph_label.image = img
        self.graph_label.grid(column=0, row=0)
        # self.update_graph()

    # Update the graph as it changes over time.
    def update_graph(self):
        img = ImageTk.PhotoImage(Image.open('weight_history_graph.jpg'))
        self.graph_label.configure(image=img)
        self.graph_label.image = img
        self.after(60 * 1000 * 1, self.update_graph)  # Update after 13 minutes


# Class to create the Weight History
class WeightHistoryFrame(tk.Frame):
    def __init__(self, frame):
        tk.Frame.__init__(self, frame)

        self.history_tree = None
        self.frame = frame

        # Create the Food Data Tree
        history_tree_frame = tk.Frame(self.frame)
        self.create_weight_history_tree(history_tree_frame)
        history_tree_frame.grid(column=0, row=0)
        self.last_weight_history = None

        delete_btn = tk.Button(self.master, text="Del", command=self.del_entry, font=("Helvetica", 15), width=5)
        delete_btn.grid(column=0, row=1)

        self.bathroom_scale_if = bathroom_scale_if.BathroomScaleIF(bathroom_scale_if_ip_port)
        self.bathroom_scale_if.daemon = True
        self.bathroom_scale_if.start()

    # Deletes the entry requested - usually to clean up a poor measurement for some reason.
    def del_entry(self):
        # print("delete")
        selected = self.history_tree.selection()
        # print(selected)
        if len(selected) != 0:
            chosen_entry = self.history_tree.item(selected[0])
            # print(chosen_entry)
            db_id, date, user, weight = chosen_entry["values"]
            # print(self.weight)
            # print(db_id, date, user, weight)

            # Confirm the user wants to delete the record.
            confirm = messagebox.askyesno(title='Confirm Deletion',
                                          message=f'Delete Selected Record {date[:10]} {weight}kg?')

            # Delete the selected item from the database
            if confirm == True:
                self.bathroom_scale_if.delete_entry(db_id)
            else:
                print("Did not delete recourd")

    # Create the tree view object.
    def create_weight_history_tree(self, history_tree_frame):

        # temp_label = tk.Label(history_tree_frame, text="Temp", fg="Black", font=("Helvetica", 15))
        # temp_label.grid(column=1, row=0)
        # Set up frame to have 2 columns
        history_tree_frame.columnconfigure(0, weight=4)
        history_tree_frame.columnconfigure(1, weight=1)
        history_tree_frame.columnconfigure(2, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.history_tree = ttk.Treeview(history_tree_frame, columns=('db_id', 'Date', 'User', 'Weight'),
                                         show='headings', height=16)

        self.history_tree["displaycolumns"] = ('Date', 'Weight')

        self.history_tree.column('Date', anchor=tk.W, width=110)
        # self.history_tree.column('Weight', anchor=tk.CENTER, width=80)
        self.history_tree.column('User', anchor=tk.E, width=50)
        self.history_tree.column('Weight', anchor=tk.E, width=50)

        self.history_tree.heading('Date', text="Date")
        self.history_tree.heading('User', text="User")
        self.history_tree.heading('Weight', text="Weight")

        self.history_tree.grid(column=0, row=0)
        sb = ttk.Scrollbar(history_tree_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.history_tree.config(yscrollcommand=sb.set)
        sb.config(command=self.history_tree.yview)

    # Populate the history Tree View. search_date is used to get the information for that date.
    def populate_history(self):
        self.history_tree.delete(*self.history_tree.get_children())

        weight_history = self.bathroom_scale_if.return_records()

        # print(weight_history)

        # Plot the last 6 months
        if self.last_weight_history is None or self.last_weight_history != weight_history:
            weight_plotter = WeightHistoryPlotter(180)
            weight_plotter.plot_save(weight_history, 94, 80, 'weight_history_graph.jpg')

        self.history_tree.tag_configure('odd', font=("fixedsys", 12), background='light grey')
        self.history_tree.tag_configure('even', font=("fixedsys", 12))

        index = 0

        for record in weight_history:
            if index % 2:
                self.history_tree.insert(parent='', index=index, values=(record[0], record[1], record[2], record[3]),
                                         tags='even')
            else:
                self.history_tree.insert(parent='', index=index, values=(record[0], record[1], record[2], record[3]),
                                         tags='odd')
            index = index + 1

        self.last_weight_history = weight_history

        # self.todays_calories_value_label.configure(text = (f"{self.todays_calories:.0f} kCal"))
        self.after(60 * 1000 * 7,
                   self.populate_history)  # Update every 7 minutes - to ensure the day change gets included


# Class to manaage the history frame of the Application.
class BodyWeightFrame:

    def __init__(self, frame):
        self.master_frame = frame

        # There are two frames - table of weight history and a graph of that data.
        self.weight_history_frame = tk.Frame(self.master_frame)
        self.graph_frame = tk.Frame(self.master_frame)

        # Object for the Weight History.
        self.weight_history = WeightHistoryFrame(self.weight_history_frame)
        self.weight_history.populate_history()

        history_grapher = HistoryGrapher(self.graph_frame)
        history_grapher.update_graph()

        self.weight_history_frame.grid(column=0, row=0)
        self.graph_frame.grid(column=1, row=0)

        logger.info("Body Weight Handling")
