from tkinter import *
from tkinter import ttk

ws = Tk()
ws.title("PythonGuides")

tv = ttk.Treeview(ws, columns=(1, 2, 3), show='headings', height=8)
tv.pack()

tv.heading(1, text="name")
tv.heading(2, text="eid")
tv.heading(3, text="Salary")

def update_item():
    selected = tv.focus()
    temp = tv.item(selected, 'values')
    sal_up = float(temp[2]) + float(temp[2]) * 0.05
    tv.item(selected, values=(temp[0], temp[1], sal_up))

tv.insert(parent='', index=0, iid=0, values=("vineet", "e11", 1000000.00))
tv.insert(parent='', index=1, iid=1, values=("anil", "e12", 120000.00))
tv.insert(parent='', index=2, iid=2, values=("ankit", "e13", 41000.00))
tv.insert(parent='', index=3, iid=3, values=("Shanti", "e14", 22000.00))

Button(ws, text='Increment Salary', command=update_item).pack()

style = ttk.Style()
style.theme_use("default")
style.map("Treeview")

ws.mainloop()