import tkinter as tk
from tkinter import ttk
import time
import sqlite3 as sq


import HX711 as HX

class FoodData():
    def __init__(self, win, database):
        self.db_con = sq.connect(database)

        frame = tk.Frame(win)
        frame.grid(column=0, row=2, columnspan=3)

        self.food_tree_view = ttk.Treeview(frame, columns=('FoodName', 'kCal'), show='headings', height=12)

        style = ttk.Style()
        style.theme_use("default")
        style.configure('Treeview', rowheight=20)
        style.map("Treeview")

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)


        #self.food_tree_view.column('FoodCode', anchor=tk.CENTER, width=1)
        self.food_tree_view.column('FoodName', anchor=tk.CENTER, width=100)
        self.food_tree_view.column('kCal', anchor=tk.CENTER, width=00)

        #self.food_tree_view.heading('FoodCode', text="Food Code")
        self.food_tree_view.heading('FoodName', text="Food Name")
        self.food_tree_view.heading('kCal', text="kCal/100g")

        self.food_tree_view.grid(column=0, row=0, columnspan=2)

        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        #sb.pack(side=tk.RIGHT, fill=tk.Y)
        sb.grid(column=2, row=0)


        self.food_tree_view.config(yscrollcommand=sb.set)
        sb.config(command=self.food_tree_view.yview)

        #def update_item():
        #    selected = food_tree_view.focus()
        #    temp = food_tree_view.item(selected, 'values')
        #    sal_up = float(temp[2]) + float(temp[2]) * 0.05
        #    food_tree_view.item(selected, values=(temp[0], temp[1], sal_up))

        import sqlite3

        self.db_con = sqlite3.connect(database)

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
        self.menu_tree_view = ttk.Treeview(frame, columns=('FoodName', 'Weight', 'kCal'), show='headings', height=12)
        self.menu_tree_view.column('FoodName', anchor=tk.CENTER, width=100)
        self.menu_tree_view.column('Weight', anchor=tk.CENTER, width=80)
        self.menu_tree_view.column('kCal', anchor=tk.CENTER, width=80)

        #self.menu_tree_view.heading('FoodCode', text="Food Code")
        self.menu_tree_view.heading('FoodName', text="Food Name")
        self.menu_tree_view.heading('kCal', text="kCal")
        self.menu_tree_view.heading('Weight', text="grams")

        #sb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        #sb.pack(side=tk.RIGHT, fill=tk.Y)

        #self.menu_tree_view.config(yscrollcommand=sb.set)
        #sb.config(command=self.menu_tree_view.yview)
        self.menu_tree_view.grid(column=3, row=0, columnspan=2)



class food_selection():
    def __init__(self, win, food_dict):
        self.selection = tk.StringVar()
        self.combo_box = ttk.Combobox(win, textvariable=self.selection)
        self.combo_box['values'] = food_dict
        self.combo_box.pack()



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
        root.columnconfigure(3, weight=1)

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
        self.add_to_meal_btn = tk.Button(self.master, text="Add To Meal", command=self.exit)

        self.time_label.grid(column=0, row=0)
        self.weight_disp.grid(column=0, row=1)
        self.zero_btn.grid(column=1, row=0)
        self.exit_btn.grid(column=1, row=1)
        self.add_to_meal_btn.grid(column=2, row=1)

        #combo_boxes = {}
        #for combo in range(4):
        #    combo_boxes[combo] = food_selection(master, ("rice", "pasta", "white bread", "brown bread", "potatoes"))

        food_data = FoodData(master, 'food_data.db')

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
        weight = float(weight_str[:-2])

        # Ignore any negative weight greater than 2g - avoids flicker of -ve sign.
        if weight < 0 and weight > -2:
            weight = 0
        weight_display = (f"{float(weight):03.0f}g")

        #print(weight)
        self.weight_disp.configure(text = weight_display)
        self.after(500, self.update_weight)

root = tk.Tk()
app=App(root)
root.wm_title("Fatman Scale")

root.attributes('-fullscreen', True)
root.after(1000, app.update_clock)
root.mainloop()
