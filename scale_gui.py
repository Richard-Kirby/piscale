import tkinter as tk
from tkinter import ttk
import time
import sqlite3 as sq


import HX711 as HX

class App(tk.Frame):
    def __init__(self, master=None):

        # Connect to the scale and zero it out.
        # create a SimpleHX711 object using GPIO pin 14 as the data pin,
        # GPIO pin 15 as the clock pin, -370 as the reference unit, and
        # -367471 as the offset
        self.hx = HX.SimpleHX711(14, 15, int(-370 / 1.244), -367471)
        self.hx.zero()

        tk.Frame.__init__(self, master)

        # configure the grid
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)

        #root.columnconfigure(3, weight=1)

        self.master = master
        self.time_label = tk.Label(text="", fg="Blue", font=("Helvetica", 18))
        #self.label.place(x=50,y=80)
        self.weight_disp = tk.Label(text="", fg="Red", font=("Helvetica", 30))

        #self.weight_disp.place(x=50, y=100)
        # self.weight_disp.pack()
        self.update_weight()
        # create a button

        self.zero_btn = tk.Button(self.master, text="Zero", command=self.zero)
        self.exit_btn = tk.Button(self.master, text="Exit", command=self.exit)
        self.add_to_meal_btn = tk.Button(self.master, text="Add To Meal", command=self.add_to_meal)

        # Connection to database of food.
        self.db_con = sq.connect('food_data.db')

        # Setting Style
        style = ttk.Style()
        style.theme_use("default")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")

        # List of food and their characteristics.
        self.food_tree_view = ttk.Treeview(self.master, columns=('db_id', 'FoodName', 'kCal', 'Fave'),
                                           show='headings', height=12)

        self.food_tree_view["displaycolumns"]=('FoodName', 'kCal', 'Fave')
        self.food_tree_view.column('FoodName', anchor=tk.W, width=320)
        self.food_tree_view.column('kCal', anchor=tk.E, width=90)
        self.food_tree_view.column('Fave', anchor=tk.CENTER, width=20)
        self.food_tree_view.heading('FoodName', text="Food Name")
        self.food_tree_view.heading('kCal', text="kCal/100g")
        self.food_tree_view.heading('Fave', text="Fave")
        self.food_tree_view.grid(column=0, row=2)

        sb = ttk.Scrollbar(self.master, orient=tk.VERTICAL) # was frame.
        sb.grid(column=1, row=2)

        self.food_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.food_tree_view.yview)

        # Populate all the data from the Database of information
        self.populate_food_data()

        # Create the meal TreeView, which tracks the meal
        self.meal_tree_view = ttk.Treeview(self.master, columns=('FoodName', 'Weight', 'kCal'), show='headings', height=12)
        self.meal_tree_view.column('FoodName', anchor=tk.CENTER, width=100)
        self.meal_tree_view.column('Weight', anchor=tk.CENTER, width=80)
        self.meal_tree_view.column('kCal', anchor=tk.CENTER, width=80)

        self.meal_tree_view.heading('FoodName', text="Food Name")
        self.meal_tree_view.heading('kCal', text="kCal")
        self.meal_tree_view.heading('Weight', text="grams")

        # Intialise the mawl to 0 caories.
        self.meal_total_calories = 0
        self.meal_kcal_display = tk.Label(text="0", fg="Red", font=("Helvetica", 15))

        self.favorite_radio_sel = tk.IntVar()

        fave_radio = tk.Radiobutton(self.master,
                       text="Favorites",
                       variable=self.favorite_radio_sel,
                       command=self.radio_sel,
                       value=1)

        all_radio = tk.Radiobutton(self.master,
                       text="All",
                       variable=self.favorite_radio_sel,
                       command=self.radio_sel,
                       value=2)

        # Button to Remove something from the meal.
        self.remove_from_meal_btn = tk.Button(self.master, text="Remove From Meal", command=self.remove_from_meal)

        # Buttons to toggle whether a food is a favourite or not, to enable filtering.
        self.toggle_favourite_btn = tk.Button(self.master, text="Favourite Toggle", command=self.toggle_favourite)

        self.time_label.grid(column=0, row=0)
        self.weight_disp.grid(column=0, row=1)
        self.zero_btn.grid(column=1, row=0)
        self.exit_btn.grid(column=1, row=1)
        self.add_to_meal_btn.grid(column=2, row=1)
        self.remove_from_meal_btn.grid(column=3, row=1)
        self.meal_tree_view.grid(column=2, row=2, columnspan=2)
        self.meal_kcal_display.grid(column=3, row=3)
        fave_radio.grid(column=0, row=3)
        all_radio.grid(column=0, row=4)
        self.toggle_favourite_btn.grid(column=1, row=3)

    # Grab the data from the Database and add it to the TreeView table.
    def populate_food_data(self):
        self.food_tree_view.delete(*self.food_tree_view.get_children())

        with self.db_con:
            food_data = self.db_con.execute("SELECT id, FoodCode, FoodName, KCALS, Favourite FROM FoodData")

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


    def update_clock(self):
        now = time.strftime("%a %b %Y %H:%M:%S")
        self.time_label.configure(text=now)
        self.after(1000, self.update_clock)

    # Zero out the scale
    def zero(self):
        self.hx.zero()

    # Exit function
    def exit(self):
        quit()

    def update_weight(self):
        # Get the current weight on the scale
        weight_str = str(self.hx.weight(2))
        # print(weight_str)
        self.weight = float(weight_str[:-2])

        # Ignore any negative weight greater than 2g - avoids flicker of -ve sign.
        if self.weight < 0 and self.weight > -2:
            self.weight = 0
        weight_display = (f"{float(self.weight):03.0f}g")

        #print(weight)
        self.weight_disp.configure(text = weight_display)
        self.after(500, self.update_weight)

    def update_meal_calories(self):
        self.meal_kcal_display.configure(text = (f"{self.meal_total_calories:.0f} kCal"))

    # Add an item to the meal calculating total meal calories.
    def add_to_meal(self):
        selected = self.food_tree_view.selection()
        chosenfood = self.food_tree_view.item(selected[0])
        print(chosenfood)
        food_name, calories_per_100 = chosenfood["values"]
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
        print(str(self.favorite_radio_sel.get()))

    def toggle_favourite(self):
        selected = self.food_tree_view.selection()

        for sel_item in selected:
            print(sel_item)
            id = self.food_tree_view.index(sel_item)

            if self.food_tree_view.item(selected[0])["values"][3] == 0:
                Favourite = 1
            else:
                Favourite = 0


            print(id, self.food_tree_view.item(sel_item), Favourite)

            # This doesn't seem to be working. 
            with self.db_con:
                print(self.db_con.execute("UPDATE FoodData SET Favourite = ? where id= ?", [Favourite , id]))

        time.sleep(1)
        self.populate_food_data()


root = tk.Tk()
app=App(root)
root.wm_title("Fatman Scale")

root.attributes('-fullscreen', True)
root.after(1000, app.update_clock)
root.mainloop()
