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

        self.time_label.grid(column=0, row=0)
        self.weight_disp.grid(column=0, row=1)
        self.zero_btn.grid(column=1, row=0)
        self.exit_btn.grid(column=1, row=1)
        self.add_to_meal_btn.grid(column=2, row=1)

        # Connection to database of food.
        self.db_con = sq.connect('food_data.db')

        # Setting Style
        style = ttk.Style()
        style.theme_use("default")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")

        # List of food and their characteristics.
        self.food_tree_view = ttk.Treeview(self.master, columns=('FoodName', 'kCal'), show='headings', height=12)
        self.food_tree_view.column('FoodName', anchor=tk.CENTER, width=320)
        self.food_tree_view.column('kCal', anchor=tk.CENTER, width=80)
        self.food_tree_view.heading('FoodName', text="Food Name")
        self.food_tree_view.heading('kCal', text="kCal/100g")
        self.food_tree_view.grid(column=0, row=2)

        sb = ttk.Scrollbar(self.master, orient=tk.VERTICAL) # was frame.
        sb.grid(column=1, row=2)

        self.food_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.food_tree_view.yview)

        with self.db_con:
            food_data = self.db_con.execute("SELECT FoodCode, FoodName, KCALS FROM FoodData")

        self.food_tree_view.tag_configure('odd', font=("default",12), background='light grey')
        self.food_tree_view.tag_configure('even', font=("default",12))

        index =0
        for food in food_data:
            # print(food)
            if index %2:
                self.food_tree_view.insert(parent='', index = index, values=(food[1], food[2]), tags=('odd'))
            else:
                self.food_tree_view.insert(parent='', index = index, values=(food[1], food[2]), tags=('even'))
            index = index + 1

        # Create the menu TreeView, which tracks the menu
        self.menu_tree_view = ttk.Treeview(self.master, columns=('FoodName', 'Weight', 'kCal'), show='headings', height=12)
        self.menu_tree_view.column('FoodName', anchor=tk.CENTER, width=100)
        self.menu_tree_view.column('Weight', anchor=tk.CENTER, width=80)
        self.menu_tree_view.column('kCal', anchor=tk.CENTER, width=80)

        self.menu_tree_view.heading('FoodName', text="Food Name")
        self.menu_tree_view.heading('kCal', text="kCal")
        self.menu_tree_view.heading('Weight', text="grams")

        self.menu_tree_view.grid(column=2, row=2, columnspan=2)

        # Intialise the mawl to 0 caories.
        self.meal_total_calories = 0
        self.meal_kcal_display = tk.Label(text="0", fg="Red", font=("Helvetica", 15))
        self.meal_kcal_display.grid(column=3, row=3)


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
        chosenfood = (self.food_tree_view.item(selected[0]))
        print(chosenfood)
        food_name, calories_per_100 = chosenfood["values"]
        print(self.weight)
        food_weight = self.weight
        print(food_name, calories_per_100)
        food_calories = float(calories_per_100) * self.weight/100
        if food_calories < 0:
            food_calories = 0

        # Add the food item to the end of the meal list.
        self.menu_tree_view.insert(parent='',index = tk.END,values=(food_name, food_weight, (f"{food_calories:.0f}")))
        self.meal_total_calories = self.meal_total_calories + food_calories
        self.update_meal_calories()

        # Zero out the scale, so it is ready for additional food
        self.hx.zero()


root = tk.Tk()
app=App(root)
root.wm_title("Fatman Scale")

root.attributes('-fullscreen', True)
root.after(1000, app.update_clock)
root.mainloop()
