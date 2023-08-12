import subprocess
import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import sqlite3 as sq
import pathlib
from PIL import Image, ImageTk
import config

import logging

logger = logging.getLogger("scaleLogger")
logger.setLevel(logging.INFO)

mod_path = pathlib.Path(__file__).parent
favorite_radio_sel = None

# FoodDataFrame Contains all the food data from the database and the search mechanism.
class FoodDataFrame(tk.Frame):
    def __init__(self, frame, weight):
        tk.Frame.__init__(self, frame)

        self.weight = weight

        self.food_tree_view = None
        self.main_food_frame = frame

        self.food_data_db_con = sq.connect(f'{mod_path}/food_data.db')

        # Create the Food Data Tree
        self.food_data_tree_frame = tk.Frame(self.main_food_frame)
        self.create_food_data_tree(self.food_data_tree_frame)

        # Keyboard icon preparation
        kb_image = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/keyboard.png').resize((32, 32)))
        # Button that opens an onscreen keyboard
        self.keyb_button = tk.Button(self.main_food_frame, image=kb_image, command=self.keyb, font=config.widget_font,
                                     width=60)
        self.keyb_button.image = kb_image

        # Search entry box
        self.search_str = tk.StringVar()
        self.search_box = ttk.Entry(
            self.main_food_frame,
            textvariable=self.search_str,
            font=config.widget_font
        )

        # Calculates and displays the calorie content of the selected itme given the weight.
        self.selected_item_cal_label = tk.Label(self.main_food_frame, text="Selected")  # , font=("Helvetica", 11))

        # Call to the update calories for the selected item. Should update once in a while after that.
        self.update_item_calories()

        self.search_box.grid(column=0, row=0, sticky='we')
        self.keyb_button.grid(column=1, row=0, sticky='e')
        self.food_data_tree_frame.grid(column=0, row=1, columnspan=2)
        self.selected_item_cal_label.grid(column=0, row=2, columnspan=2)

        self.populate_food_data()

    # Creates the Food Data Tree for selecting food. Puts it into a frame.
    def create_food_data_tree(self, food_data_tree_frame):

        # Set up frame to have 2 columns
        food_data_tree_frame.columnconfigure(0, weight=4)
        food_data_tree_frame.columnconfigure(1, weight=1)

        # List of food and their characteristics.
        self.food_tree_view = ttk.Treeview(food_data_tree_frame,
                                           columns=('db_id', 'FoodCode', 'FoodName', 'kCal', 'Fave'),
                                           show='headings', height=16)

        self.food_tree_view["displaycolumns"] = ('FoodName', 'kCal')
        self.food_tree_view.column('FoodName', anchor=tk.W, width=380)
        self.food_tree_view.column('kCal', anchor=tk.E, width=40)
        self.food_tree_view.column('Fave', anchor=tk.CENTER, width=20)
        self.food_tree_view.heading('FoodName', text="Food Name")
        self.food_tree_view.heading('FoodCode', text="Food Code")
        self.food_tree_view.heading('kCal', text="kCal/100g")
        self.food_tree_view.heading('Fave', text="Fave")
        self.food_tree_view.grid(column=0, row=0)

        sb = ttk.Scrollbar(food_data_tree_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='nsew')

        self.food_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.food_tree_view.yview)

    # Search the database based on the entry.
    def search_food_data(self, event):
        search_str = self.search_str.get()
        print(search_str, event)
        self.populate_food_data(search=search_str)

    # Bring onscreen keyboard up.
    def keyb(self):
        # print("keyboard function")
        self.search_box.focus_set()
        # os.system(self.keyb_sh_cmd)
        subprocess.Popen('onboard')

    # Grab the data from the Database and add it to the TreeView table.
    def populate_food_data(self, search=None):
        self.food_tree_view.delete(*self.food_tree_view.get_children())

        # print(f"Search String {search}")

        with self.food_data_db_con:
            # print(self.favorite_radio_sel.get())
            if favorite_radio_sel.get() == 1:
                if search is None:
                    # print("search is None")
                    food_data = self.food_data_db_con.execute(
                        "SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData")
                else:
                    search = f"%{search}%"
                    # print(f"Search String 2 {search}")
                    food_data = self.food_data_db_con.execute(
                        "SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData WHERE FoodName LIKE ?",
                        (search,))
            else:
                food_data = self.food_data_db_con.execute(
                    "SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData"
                    " WHERE Favourite=1")

        self.food_tree_view.tag_configure('odd', font=config.data_font, background='light grey')
        self.food_tree_view.tag_configure('even', font=config.data_font)
        self.food_tree_view.tag_configure('odd_fave', font=config.data_font, foreground='red', background='light grey')
        self.food_tree_view.tag_configure('even_fave', font=config.data_font, foreground='red')

        # TODO: Can't get images to work with the tree view.
        # small_fave_image = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/fave.png').resize((32, 32)))

        index = 0

        # Adding food to the food view tree. This is where user selects food.
        for food in food_data:
            if food[3] == 'N' or food[3] == 'Tr' or food[3] == '':
                k_cal = '0'
            else:
                k_cal = int(food[3])

            if food[4] == 1:  # Check to see if a favourite - if it is a favourite, the formatting is different.
                if index % 2:
                    self.food_tree_view.insert(parent='', index=food[0],
                                               values=(food[0], food[1], food[2], k_cal, food[4]),
                                               tags='even_fave')
                else:
                    self.food_tree_view.insert(parent='', index=food[0],
                                               values=(food[0], food[1], food[2], k_cal, food[4]),
                                               tags='odd_fave')
            else:
                if index % 2:
                    self.food_tree_view.insert(parent='', index=food[0],
                                               values=(food[0], food[1], food[2], k_cal, food[4]),
                                               tags='even')
                else:
                    self.food_tree_view.insert(parent='', index=food[0],
                                               values=(food[0], food[1], food[2], k_cal, food[4]),
                                               tags='odd')
            index = index + 1

    # update the string of the selected item
    def update_item_calories(self):
        selected = self.food_tree_view.selection()
        # print(selected)
        if len(selected) != 0:
            chosenfood = self.food_tree_view.item(selected[0])
            # print(chosenfood)
            db_id, food_code, food_name, kcalories_per_100, fave = chosenfood["values"]
            # print(self.weight)
            food_calories = float(kcalories_per_100) * self.weight.get_weight() / 100
            if food_calories < 0:
                food_calories = 0
            # print(f"{food_name} {food_calories}kCal")
            self.selected_item_cal_label.configure(text=f"{food_name[:60]} {food_calories:.0f} kCal")

        self.after(2 * 1000, self.update_item_calories)


# Meal Frame includes the meal frame, which has all the components of meals, the history frame that
# has the history, which shows today's meals and total calories for the day.
class MealFrame(tk.Frame):
    def __init__(self, meal_frame, weight):
        tk.Frame.__init__(self, meal_frame)

        self.weight = weight
        # Create a connection to the history database.
        self.history_db_con = sq.connect(f'{mod_path}/history.db')
        self.food_data_db_con = sq.connect(f'{mod_path}/food_data.db')
        self.meal_history_db_con = sq.connect(f'{mod_path}/meal_history.db')

        # Create the Food Data Tree
        self.meal_tree_view = None
        self.todays_calories = None
        self.calorie_history_view = None
        meal_tree_frame = tk.Frame(meal_frame)
        self.create_meal_tree(meal_tree_frame)

        # Entry box Food Name for adhoc meal
        self.adhoc_meal_name = tk.StringVar()
        adhoc_meal_name_box = ttk.Entry(
            meal_frame,
            textvariable=self.adhoc_meal_name,
            font=config.data_font, width=12
        )
        adhoc_meal_name_box.grid(column=0, row=0)

        # Entry box kCal for adhoc meal
        self.adhoc_meal_kcal = tk.IntVar()
        self.adhoc_meal_kcal_box = ttk.Entry(
            meal_frame,
            textvariable=self.adhoc_meal_kcal,
            font=config.data_font, width=6
        )
        self.adhoc_meal_kcal_box.grid(column=1, row=0)

        self.adhoc_meal_btn = tk.Button(meal_frame, text="Adhoc", command=self.adhoc_meal, font=config.widget_font,
                                        width=3)
        self.adhoc_meal_btn.grid(column=2, row=0)

        # Entry box Food Name for adhoc meal
        self.adhoc_meal_name = tk.StringVar()
        self.adhoc_meal_box = ttk.Entry(
            meal_frame,
            textvariable=self.adhoc_meal_name,
            font=config.data_font, width=12
        )

        self.adhoc_meal_box.grid(column=0, row=0)

        # Today's calorie counts.
        todays_calories_label = tk.Label(meal_frame, text="Today's kCal", font=config.data_font)
        self.todays_calories_value_label = tk.Label(meal_frame, text="0", fg="red", font=config.data_font)

        calorie_history_frame = tk.Frame(meal_frame)

        # Create the Calorie History Tree
        self.create_calorie_history_tree(calorie_history_frame)

        # Intialise the mawl to 0 caories.
        self.meal_total_calories = 0

        meal_kcal_label = tk.Label(meal_frame, text="Meal kCal", font=config.data_font)
        self.meal_kcal_display = tk.Label(meal_frame, text="0", fg="Red", font=config.data_font)

        add_to_history_image = ImageTk.PhotoImage(Image.open
                                                  (f'{mod_path}/images/8665197_circle_arrow_down_icon.png')
                                                  .resize((32, 32)))

        # This button moves a meal to history.
        add_to_history_button = tk.Button(meal_frame, image=add_to_history_image,
                                          command=self.add_to_history, width=40)

        add_to_history_button.image = add_to_history_image

        meal_tree_frame.grid(column=0, row=1, columnspan=3)
        add_to_history_button.grid(column=0, row=2, sticky='e')
        calorie_history_frame.grid(column=0, row=3, columnspan=3)

        meal_kcal_label.grid(column=1, row=2)
        self.meal_kcal_display.grid(column=2, row=2)

        todays_calories_label.grid(column=0, row=4)
        self.todays_calories_value_label.grid(column=1, row=4)
        self.populate_history()

    # Creates the meal Tree for showing the meal. Puts it into a frame.
    def create_meal_tree(self, meal_frame):

        # Set up frame to have 2 columns
        meal_frame.columnconfigure(0, weight=4)
        meal_frame.columnconfigure(1, weight=1)

        # Create the meal TreeView, which tracks the meal
        self.meal_tree_view = ttk.Treeview(meal_frame,
                                           columns=('db_id', 'FoodCode', 'FoodName', 'Weight', 'kCal'),
                                           show='headings', height=6)
        self.meal_tree_view.column('FoodName', anchor=tk.CENTER, width=160)
        self.meal_tree_view.column('Weight', anchor=tk.CENTER, width=50)
        self.meal_tree_view.column('kCal', anchor=tk.CENTER, width=50)
        self.meal_tree_view["displaycolumns"] = ('FoodName', 'Weight', 'kCal')

        self.meal_tree_view.heading('FoodName', text="Food Name")
        self.meal_tree_view.heading('kCal', text="kCal")
        self.meal_tree_view.heading('Weight', text="g")

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
        self.calorie_history_view = ttk.Treeview(calorie_history_frame, columns=('db_id', 'Time', 'Weight', 'kCal'),
                                                 show='headings', height=7)

        self.calorie_history_view["displaycolumns"] = ('Time', 'kCal')

        self.calorie_history_view.column('Time', anchor=tk.CENTER, width=180)
        self.calorie_history_view.column('kCal', anchor=tk.E, width=80)

        self.calorie_history_view.heading('Time', text="Time")
        self.calorie_history_view.heading('kCal', text="kCal")

        self.calorie_history_view.grid(column=0, row=0)
        sb = ttk.Scrollbar(calorie_history_frame, orient=tk.VERTICAL)
        sb.grid(column=1, row=0, sticky='ns')

        self.calorie_history_view.config(yscrollcommand=sb.set)
        sb.config(command=self.calorie_history_view.yview)

    # Adds adhoc meal e.g. snack or something ate out - or doesn't appear in the list of foods.
    # Takes a name and associated calories.
    def adhoc_meal(self):
        # print("adhoc meal")

        # Add the food item to the end of the meal list.
        self.meal_tree_view.insert(parent='', index=tk.END, values=(0, 'None', self.adhoc_meal_name.get(),
                                                                    0, self.adhoc_meal_kcal.get()))
        self.meal_total_calories = self.meal_total_calories + self.adhoc_meal_kcal.get()
        self.adhoc_meal_box.delete(0, tk.END)
        self.adhoc_meal_kcal_box.delete(0, tk.END)
        self.update_meal_calories()

    # Populate the history Tree View. search_date is used to get the information for that date.
    def populate_history(self):
        self.calorie_history_view.delete(*self.calorie_history_view.get_children())

        today = str(datetime.now())[:10]

        search_date = f"%{today}%"
        # print(search_date)

        # print(f"Search String {search_date}")

        with self.history_db_con:
            # print(self.favorite_radio_sel.get())
            if search_date is None:
                # print("search is None")
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History")
            else:
                # Search for today's calories
                # print(f"Search String {search_date}")
                history_data = self.history_db_con.execute("SELECT id, Date, KCALS, Weight FROM History"
                                                           " WHERE Date LIKE ?", (search_date,))

        self.calorie_history_view.tag_configure('odd', font=config.data_font, background='light grey')
        self.calorie_history_view.tag_configure('even', font=config.data_font)

        index = 0
        self.todays_calories = 0

        for item in history_data:
            if index % 2:
                self.calorie_history_view.insert(parent='', index=item[0], values=(item[0], item[1][10:-3],
                                                                                   item[2], item[3]),
                                                 tags='even')
            else:
                self.calorie_history_view.insert(parent='', index=item[0], values=(item[0], item[1][10:-3],
                                                                                   item[2], item[3]),
                                                 tags='odd')
            index = index + 1

            self.todays_calories = self.todays_calories + int(item[3])

        self.todays_calories_value_label.configure(text=f"{self.todays_calories:.0f} kCal")
        self.after(60 * 60 * 1000,
                   self.populate_history)  # Update once an hour - to ensure the day change gets included

    def update_meal_calories(self):
        self.meal_kcal_display.configure(text=f"{self.meal_total_calories:.0f} kCal")

    # This adds to the history of meals
    def add_to_history(self):

        now_micro = time.time()
        print(now_micro)

        now = datetime.now().replace(microsecond=0)
        now.replace(second=0)

        # Get all the items from the meal.
        meal = self.meal_tree_view.get_children()
        for part in meal:
            # print(part)
            # print(self.meal_tree_view.item(part)['values'])
            fooddata_db_id, foodcode, foodname, weight, calories = self.meal_tree_view.item(part)['values']
            print(fooddata_db_id, foodcode, foodname, weight, calories)

            if fooddata_db_id != 0:
                logger.debug(f"Food data being gathered for {fooddata_db_id}")
                part_data = self.food_data_db_con.execute(
                    "SELECT id, FoodCode, FoodName, PROT, FAT, CHO, CHOL, TOTSUG, AOACFIB FROM FoodData WHERE id = ?",
                    (fooddata_db_id,))

                for data in part_data:

                    data_id, foodcode, foodname, protein, fat, cho, chol, totsug, aoacfib = data
                    # print(id, foodcode, foodname, protein, fat, cho, chol, totsug, aoacfib)

                    weight = float(self.weight.get_weight())
                    if protein != 'N' and protein != 'Tr' and protein != '':
                        tot_protein = protein * weight / 100
                    else:
                        tot_protein = 0

                    if fat != 'N' and fat != 'Tr' and fat != '':
                        tot_fat = fat * weight / 100
                    else:
                        tot_fat = 0

                    if cho != 'N' and cho != 'Tr' and cho != '':
                        tot_cho = cho * weight / 100
                    else:
                        tot_cho = 0

                    if chol != 'N' and chol != 'Tr' and chol != '':
                        tot_chol = chol * weight / 100
                    else:
                        tot_chol = 0

                    if totsug != 'N' and totsug != 'Tr' and totsug != '':
                        tot_sug = totsug * weight / 100
                    else:
                        tot_sug = 0

                    if aoacfib != 'N' and aoacfib != 'Tr' and aoacfib != '':
                        tot_aoacfib = aoacfib * weight / 100
                    else:
                        tot_aoacfib = 0

                    logger.info(f'Meal History Add -->weight {weight}g protein {tot_protein}g, fat {tot_fat}g, '
                                f'carbs {tot_cho}g, chol {tot_chol}g, sugar {tot_sug}g, aoacfib {tot_aoacfib}')

                    ret = self.meal_history_db_con.execute(
                        'INSERT INTO MealHistory (unix_ms, Date, fooddata_db_id, FoodName,'
                        'PROT, FAT, CHO, CHOL, TOTSUG, AOACFIB, KCALS, WEIGHT) '
                        ' values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        [now_micro, now, fooddata_db_id, foodname,
                         tot_protein, tot_fat, tot_cho, tot_chol,
                         tot_sug, tot_aoacfib, calories, weight])
                    logger.info(f'sql return {ret}')
                    self.meal_history_db_con.commit()

        if self.meal_total_calories != 0:
            with self.history_db_con:
                self.history_db_con.execute("INSERT INTO History (Date, KCALS, Weight) values(?, ?, ?)",
                                            [now, 0, int(self.meal_total_calories)])
                self.history_db_con.commit()

        # Update the history tree
        self.populate_history()

        # Clear the meal tree and total calories as it is now part of history.
        self.meal_tree_view.delete(*self.meal_tree_view.get_children())
        self.meal_total_calories = 0
        self.update_meal_calories()


# Class to manaage the history frame of the Application.
class DailyFrame:

    def __init__(self, frame, weight):
        self.daily_frame = frame

        self.weight = weight

        global favorite_radio_sel

        favorite_radio_sel= tk.IntVar()

        small_fave_image = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/fave.png').resize((32, 32)))

        self.inter_frame = tk.Frame(self.daily_frame)

        fave_radio = tk.Radiobutton(self.inter_frame,
                                    image=small_fave_image,
                                    variable=favorite_radio_sel,
                                    command=self.radio_sel,
                                    value=0, font=config.widget_font)

        fave_radio.image = small_fave_image

        all_image = ImageTk.PhotoImage(Image.open
                                       (f'{mod_path}/images/6541614_logo_overflow_stack_stackoverflow_icon.png')
                                       .resize((32, 32)))

        all_radio = tk.Radiobutton(self.inter_frame,
                                   image=all_image,
                                   variable=favorite_radio_sel,
                                   command=self.radio_sel,
                                   value=1)

        all_radio.image = all_image

        add_to_meal_image = ImageTk.PhotoImage(Image.open(
            f'{mod_path}/images/8665198_circle_arrow_right_icon.png').resize((32, 32)))

        add_to_meal_btn = tk.Button(self.inter_frame, image=add_to_meal_image, command=self.add_to_meal,
                                    width=50)

        add_to_meal_btn.image = add_to_meal_image

        remove_from_meal_image = ImageTk.PhotoImage(Image.open(
            f'{mod_path}/images/8665200_circle_arrow_left_icon.png').resize((32, 32)))

        # Button to Remove something from the meal.
        remove_from_meal_btn = tk.Button(self.inter_frame, image=remove_from_meal_image,
                                         command=self.remove_from_meal, width=50)

        remove_from_meal_btn.image = remove_from_meal_image

        # Favorite Toggle Icon and Button
        fave_image = ImageTk.PhotoImage(Image.open(f'{mod_path}/images/fave.png').resize((48, 48)))

        toggle_favourite_btn = tk.Button(self.inter_frame, image=fave_image,  # text='Fav',
                                         command=self.toggle_favourite, font=config.widget_font, width=50)
        toggle_favourite_btn.image = fave_image

        fave_radio.grid(column=0, row=0, sticky='nw')
        all_radio.grid(column=0, row=1, sticky='nw')
        add_to_meal_btn.grid(column=0, row=2, sticky='ne', pady=5)
        remove_from_meal_btn.grid(column=0, row=3, sticky='ne')
        toggle_favourite_btn.grid(column=0, row=4, sticky='se', pady=60)

        # Initialise total calories for today.
        self.todays_calories = 0

        # Connection to database of food.
        self.history_db_con = sq.connect(f'{mod_path}/history.db')
        self.meal_history_db_con = sq.connect(f'{mod_path}/meal_history.db')
        self.food_data_db_con = sq.connect(f'{mod_path}/food_data.db')

        # Create the Meal History DB tables if not already created.
        with self.meal_history_db_con:
            # create cursor object
            cur = self.meal_history_db_con.cursor()

            list_of_tables = cur.execute(
                """SELECT name FROM sqlite_master WHERE type='table'
                AND name='MealHistory'; """).fetchall()

            # print(list_of_tables)

            if not list_of_tables:
                # print("Table not found")
                # print("Creating Meal History")

                # Create the table as it wasn't found.
                self.meal_history_db_con.execute(""" CREATE TABLE MealHistory(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        unix_ms INTEGER,
                        Date TEXT,
                        fooddata_db_id INTEGER,
                        FoodCode TEXT,
                        FoodName TEXT,
                        PROT FLOAT,
                        FAT FLOAT,
                        CHO FLOAT,
                        CHOL FLOAT,
                        TOTSUG FLOAT,
                        AOACFIB FLOAT,
                        KCALS FLOAT,
                        WEIGHT FLOAT
                        );
                    """)

        # Configure the grid for all the widgets.
        self.daily_frame.columnconfigure(0, weight=4)
        self.daily_frame.columnconfigure(1, weight=1)
        self.daily_frame.columnconfigure(2, weight=4)

        # Create the other necessary frame objects.
        food_data_frame = tk.Frame(self.daily_frame)
        meal_frame = tk.Frame(self.daily_frame)

        # Create the right hand frame for dealing with the meals.
        self.food_data_frame = FoodDataFrame(food_data_frame, self.weight)

        self.meal_frame = MealFrame(meal_frame, self.weight)

        # Locate the frames.
        food_data_frame.grid(column=0, row=0, sticky='n')
        self.inter_frame.grid(column=1, row=0, pady=30, sticky='n')
        meal_frame.grid(column=2, row=0, sticky='n')

    # Add an item to the meal calculating total meal calories.
    def add_to_meal(self):
        selected = self.food_data_frame.food_tree_view.selection()
        chosenfood = self.food_data_frame.food_tree_view.item(selected[0])
        # print(chosenfood)
        db_id, food_code, food_name, kcalories_per_100, fave = chosenfood["values"]
        # print(self.weight)
        food_weight = self.weight.get_weight()
        # print(food_name, calories_per_100)
        food_calories = float(kcalories_per_100) * food_weight / 100
        if food_calories < 0:
            food_calories = 0

        # Add the food item to the end of the meal list.
        self.meal_frame.meal_tree_view.insert(parent='', index=tk.END, values=(db_id, food_code, food_name, food_weight,
                                                                               f"{food_calories:.0f}"))

        self.meal_frame.meal_total_calories = self.meal_frame.meal_total_calories + food_calories
        self.meal_frame.update_meal_calories()

        # Zero out the scale, so it is ready for additional food
        self.weight.zero()

    # Remove an item from the meal
    def remove_from_meal(self):
        # print("remove from meal")
        selected = self.meal_frame.meal_tree_view.selection()
        # print("*", selected)

        if len(selected) > 0:
            remove_food = (self.meal_frame.meal_tree_view.item(selected[0]))
            # print(remove_food)
            db_id, food_cde, remove_food_name, weight, calories = remove_food["values"]

            # print(remove_food_name, weight, calories)

            # Remove the food item to the end of the meal list.
            self.meal_frame.meal_tree_view.delete(selected[0])

            # Not sure about this - adds data to another class's object - not great practice?
            self.meal_frame.meal_total_calories = self.meal_frame.meal_total_calories - calories
            self.meal_frame.update_meal_calories()

    # Reacts to a change in the radio button selections (Favorite or All)
    def radio_sel(self):
        # print(str(self.favorite_radio_sel.get()))
        self.food_data_frame.populate_food_data()

    # Marks or un-marks a food as a favourite.
    def toggle_favourite(self):
        selected = self.food_data_frame.food_tree_view.selection()

        # TODO: sort out multiple selections.
        for sel_item in selected:
            # print(sel_item)
            data_id = self.food_data_frame.food_tree_view.item(selected[0])["values"][0]

            if self.food_data_frame.food_tree_view.item(selected[0])["values"][4] == 0:
                favourite = 1
            else:
                favourite = 0

            # Update the selected item with the new favourite setting
            with self.food_data_db_con:
                self.food_data_db_con.execute("UPDATE FoodData SET Favourite = ? where id= ?", [favourite, data_id])

        self.food_data_frame.populate_food_data()
