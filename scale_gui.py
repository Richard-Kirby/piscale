import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import sqlite3 as sq
import pathlib
from PIL import Image, ImageTk

mod_path = pathlib.Path(__file__).parent
# print(mod_path)

import HX711 as HX

class App(tk.Frame):
    def __init__(self, master=None):

        tk.Frame.__init__(self, master)
        self.master = master

        style = ttk.Style()
        print(style.theme_names())
        style.theme_use("alt")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")


        # Create a photoimage object of the image in the path
        #fave_img = PhotoImage(file="</home/pi/images/fave.png>")

        # Resize image to fit on button
        # photoimage = photo.subsample(1, 2)

        # Connect to the scale and zero it out.
        # create a SimpleHX711 object using GPIO pin 14 as the data pin,
        # GPIO pin 15 as the clock pin, -370 as the reference unit, and
        # -367471 as the offset
        self.hx = HX.SimpleHX711(14, 15, int(-370 / 1.244), -367471)
        self.hx.zero()

        # Update the weight, which will happen regularly after this call.
        self.weight_disp = tk.Label(text="", fg="Red", font=("Helvetica", 30))
        self.update_weight()


        # Configure the grid for all the widgets.
        root.columnconfigure(0, weight=2)
        root.columnconfigure(1, weight=2)
        root.columnconfigure(2, weight=1)
        root.columnconfigure(3, weight=2)
        root.columnconfigure(4, weight=2)
        root.columnconfigure(5, weight=2)
        root.columnconfigure(6, weight=2)

        # Connection to database of food.
        self.db_con = sq.connect(f'{mod_path}/food_data.db')
        self.history_db_con = sq.connect(f'{mod_path}/history.db')

        self.time_label = tk.Label(text="", fg="Black", font=("Helvetica", 18))

        self.zero_btn = tk.Button(self.master, text="Zero", command=self.zero)
        self.exit_btn = tk.Button(self.master, text="Exit", command=self.exit)
        self.add_to_meal_btn = tk.Button(self.master, text="->", command=self.add_to_meal)

        # Create the Food Data Tree
        self.food_data_frame = tk.Frame(master)
        self.create_food_data_tree(self.food_data_frame)

        self.meal_frame = tk.Frame(master)
        # Create the Food Data Tree
        self.create_meal_tree(self.meal_frame)

        self.calorie_history_frame = tk.Frame(master)
        # Create the Food Data Tree
        self.create_calorie_history_tree(self.calorie_history_frame)

        # Intialise the mawl to 0 caories.
        self.meal_total_calories = 0

        self.meal_kcal_label = tk.Label(text="Meal kCal", font=("Helvetica", 15))
        self.meal_kcal_display = tk.Label(text="0", fg="Red", font=("Helvetica", 15))

        self.favorite_radio_sel = tk.IntVar()

        all_radio = tk.Radiobutton(self.master,
                       text="All",
                       variable=self.favorite_radio_sel,
                       command=self.radio_sel,
                       value=1)

        fave_radio = tk.Radiobutton(self.master,
                       text="Fav",
                       variable=self.favorite_radio_sel,
                       command=self.radio_sel,
                       value=0)

        # Populate all the data from the Database of information
        self.populate_food_data()
        self.populate_history()

        # Button to Remove something from the meal.
        self.remove_from_meal_btn = tk.Button(self.master, text="<-", command=self.remove_from_meal)

        # Buttons to toggle whether a food is a favourite or not, to enable filtering.
        fave_image = ImageTk.PhotoImage(Image.open('/home/kirbypi/piscale/images/star.jpg').resize((20,20)))

        fave_label=tk.Label(image=fave_image)

        self.search_str = tk.StringVar()
        self.search_box = ttk.Entry(
            self.master,
            textvariable= self.search_str
        )
        self.search_button = ttk.Button(self.master, text='Search', command=self.search_food_data)

        # print("Entry is ", self.search_box.get())


        self.toggle_favourite_btn = tk.Button(self.master,
                                              #image=fave_image,
                                              text='F',
                                              command=self.toggle_favourite)

        self.add_to_history_button = tk.Button(self.master,
                                              #image=fave_image,
                                              text='Add',
                                              command=self.add_to_history)

        # Widget placements
        self.time_label.grid(column=3, row=0, columnspan=3, sticky='e')

        self.exit_btn.grid(column=6, row=0, sticky ='e')

        self.weight_disp.grid(column=1, row=0, columnspan=1, sticky='e')
        self.zero_btn.grid(column=2, row=0, sticky='w')

        self.search_box.grid(column=0, row=2, sticky='we', columnspan=2)
        self.search_button.grid(column=2, row=2, sticky='w')
        fave_label.grid(column=2, row=2)

        self.food_data_frame.grid(column=0, row=3, columnspan=3, rowspan=21)

        self.toggle_favourite_btn.grid(column=3, row=3)

        fave_radio.grid(column=3, row=4, sticky='w')
        all_radio.grid(column=3, row=5, sticky='w')

        self.add_to_meal_btn.grid(column=3, row=7)
        self.remove_from_meal_btn.grid(column=3, row=8)

        self.meal_frame.grid(column=4, row=3, columnspan=3, rowspan=15)

        self.add_to_history_button.grid(column=4, row=19)

        self.calorie_history_frame.grid(column=4, row=20, columnspan=3, rowspan=10)

        self.meal_kcal_display.grid(column=6, row=19)
        self.meal_kcal_label.grid(column=5, row=19)

    # Creates the Food Data Tree for selecting food. Puts it into a frame.
    def create_food_data_tree(self, food_data_frame):

        # Setting Style

        # Set up frame to have 2 columns
        food_data_frame.columnconfigure(0, weight=4)
        food_data_frame.columnconfigure(1, weight=1)

        # List of food and their characteristics.
        self.food_tree_view = ttk.Treeview(food_data_frame, columns=('db_id', 'FoodName', 'kCal', 'Fave'),
                                           show='headings', height=18)

        self.food_tree_view["displaycolumns"]=('FoodName', 'kCal', 'Fave')
        self.food_tree_view.column('FoodName', anchor=tk.W, width=320)
        self.food_tree_view.column('kCal', anchor=tk.E, width=90)
        self.food_tree_view.column('Fave', anchor=tk.CENTER, width=20)
        self.food_tree_view.heading('FoodName', text="Food Name")
        self.food_tree_view.heading('kCal', text="kCal/100g")
        self.food_tree_view.heading('Fave', text="Fave")
        self.food_tree_view.grid(column=0, row=0)

        sb = ttk.Scrollbar(food_data_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.food_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.food_tree_view.yview)

    def search_food_data(self):
        search_str = self.search_str.get()
        print(search_str)
        self.populate_food_data(search=search_str)

    # Creates the meal Tree for showing the meal. Puts it into a frame.
    def create_meal_tree(self, meal_frame):

        # Set up frame to have 2 columns
        meal_frame.columnconfigure(0, weight=4)
        meal_frame.columnconfigure(1, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.meal_tree_view = ttk.Treeview(meal_frame, columns=('FoodName', 'Weight', 'kCal'),
                                           show='headings', height=10)
        self.meal_tree_view.column('FoodName', anchor=tk.CENTER, width=100)
        self.meal_tree_view.column('Weight', anchor=tk.CENTER, width=80)
        self.meal_tree_view.column('kCal', anchor=tk.CENTER, width=80)

        self.meal_tree_view.heading('FoodName', text="Food Name")
        self.meal_tree_view.heading('kCal', text="kCal")
        self.meal_tree_view.heading('Weight', text="grams")

        self.meal_tree_view.grid(column=0, row=0)
        sb = ttk.Scrollbar(meal_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.meal_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.meal_tree_view.yview)

    # Creates the calorie history tree for showing the consumed calories. Puts it into a frame.
    def create_calorie_history_tree(self, calorie_history_frame):

        # Set up frame to have 2 columns
        calorie_history_frame.columnconfigure(0, weight=4)
        calorie_history_frame.columnconfigure(1, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.calorie_history_view = ttk.Treeview(calorie_history_frame, columns=('db_id','Date', 'Weight', 'kCal'),
                                           show='headings', height=5)

        self.calorie_history_view["displaycolumns"] = ('Date', 'kCal')

        self.calorie_history_view.column('Date', anchor=tk.CENTER, width=180)
        # self.calorie_history_view.column('Weight', anchor=tk.CENTER, width=80)
        self.calorie_history_view.column('kCal', anchor=tk.CENTER, width=80)

        self.calorie_history_view.heading('Date', text="Date")
        self.calorie_history_view.heading('kCal', text="kCal")
        #self.calorie_history_view.heading('Weight', text="grams")

        self.calorie_history_view.grid(column=0, row=0)
        sb = ttk.Scrollbar(calorie_history_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.calorie_history_view.config(yscrollcommand=sb.set)
        sb.config(command=self.calorie_history_view.yview)


    # Grab the data from the Database and add it to the TreeView table.
    def populate_food_data(self, search= None):
        self.food_tree_view.delete(*self.food_tree_view.get_children())

        print(f"Search String {search}")

        with self.db_con:
            #print(self.favorite_radio_sel.get())
            if self.favorite_radio_sel.get() == 1:
                if search is None:
                    print("search is None")
                    food_data = self.db_con.execute("SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData")
                else:
                    search = f"%{search}%"
                    print(f"Search String 2 {search}")
                    food_data = self.db_con.execute(
                        "SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData WHERE FoodName LIKE ?",(search,))
            else:
                food_data = self.db_con.execute("SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData"
                                                " WHERE Favourite=1")

        self.food_tree_view.tag_configure('odd', font=("default",12), background='light grey')
        self.food_tree_view.tag_configure('even', font=("default",12))

        index =0
        for food in food_data:
            # print(food)
            if index %2:
                self.food_tree_view.insert(parent='', index = food[0], values=(food[0], food[2], food[3], food[4]),
                                           tags=('even'))
            else:
                self.food_tree_view.insert(parent='', index = food[0], values=(food[0], food[2], food[3], food[4]),
                                           tags=('odd'))
            index = index + 1

    def populate_history(self, search = None):
        self.calorie_history_view.delete(*self.calorie_history_view.get_children())

        print(f"Search String {search}")

        with self.history_db_con:
            #print(self.favorite_radio_sel.get())
            if search is None:
                print("search is None")
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History")
            else:
                #Search goes here
                pass

        self.calorie_history_view.tag_configure('odd', font=("default",12), background='light grey')
        self.calorie_history_view.tag_configure('even', font=("default",12))

        index =0
        for item in history_data:
            if index %2:
                self.calorie_history_view.insert(parent='', index = item[0], values=(item[0], item[1], item[2], item[3]),
                                           tags=('even'))
            else:
                self.calorie_history_view.insert(parent='', index = item[0], values=(item[0], item[1], item[2], item[3]),
                                           tags=('odd'))
            index = index + 1

    def update_clock(self):
        # now = time.strftime("%a %b %Y %H:%M:%S")
        now = datetime.now().replace(microsecond=0)
        self.time_label.configure(text=now)
        self.after(800, self.update_clock)

    # Zero out the scale
    def zero(self):
        self.hx.zero()

    # Exit function
    def exit(self):
        quit()

    def update_weight(self):
        # Get the current weight on the scale
        weight_str = str(self.hx.weight(10))
        # print(weight_str)
        self.weight = float(weight_str[:-2])

        # Ignore any negative weight greater than 2g - avoids flicker of -ve sign.
        if self.weight < 0 and self.weight > -2:
            self.weight = 0
        weight_display = (f"{float(self.weight):03.0f}g")

        #print(weight)
        self.weight_disp.configure(text = weight_display)
        self.after(1000, self.update_weight)

    def update_meal_calories(self):
        self.meal_kcal_display.configure(text = (f"{self.meal_total_calories:.0f} kCal"))

    # Add an item to the meal calculating total meal calories.
    def add_to_meal(self):
        selected = self.food_tree_view.selection()
        chosenfood = self.food_tree_view.item(selected[0])
        print(chosenfood)
        id, food_name, calories_per_100, fave = chosenfood["values"]
        print(self.weight)
        food_weight = self.weight
        print(food_name, calories_per_100)
        food_calories = float(calories_per_100) * self.weight/100
        if food_calories < 0:
            food_calories = 0

        # Add the food item to the end of the meal list.
        self.meal_tree_view.insert(parent='',index = tk.END,values=(food_name, food_weight, (f"{food_calories:.0f}")))
        self.meal_total_calories = self.meal_total_calories + food_calories
        self.update_meal_calories()

        # Zero out the scale, so it is ready for additional food
        self.hx.zero()

    # Remove an item from the meal
    def remove_from_meal(self):
        print("remove from meal")
        selected = self.meal_tree_view.selection()
        print("*", selected)

        if len(selected) > 0:
            remove_food = (self.meal_tree_view.item(selected[0]))
            print(remove_food)
            remove_food_name, weight, calories = remove_food["values"]

            print(remove_food_name, weight, calories)

            # Remove the food item to the end of the meal list.
            self.meal_tree_view.delete(selected[0])
            self.meal_total_calories = self.meal_total_calories - calories
            self.update_meal_calories()

    def radio_sel(self):
        # print(str(self.favorite_radio_sel.get()))
        self.populate_food_data()

    def toggle_favourite(self):
        selected = self.food_tree_view.selection()

        for sel_item in selected:
            #print(sel_item)
            id = self.food_tree_view.item(selected[0])["values"][0]

            if self.food_tree_view.item(selected[0])["values"][3] == 0:
                Favourite = 1
            else:
                Favourite = 0

            # Update the selected item with the new favourite setting
            with self.db_con:
                self.db_con.execute("UPDATE FoodData SET Favourite = ? where id= ?", [Favourite , id])

        time.sleep(0)
        self.populate_food_data()

    # This adds to the history of meals
    def add_to_history(self):
        now = datetime.now().replace(microsecond=0)
        now.replace(second=0)
        with self.history_db_con:
            self.history_db_con.execute("INSERT INTO History (Date, KCALS, Weight) values(?, ?, ?)",
                                        [now, 0, int(self.meal_total_calories)])
        # Update the history tree
        self.populate_history()

        # Clear the meal tree and total calories as it is now part of history.
        self.meal_tree_view.delete(*self.meal_tree_view.get_children())
        self.meal_total_calories = 0
        self.update_meal_calories()

root = tk.Tk()
app=App(root)
root.wm_title("Fatman Scale")



root.attributes('-fullscreen', True)
root.after(1000, app.update_clock)
root.mainloop()
