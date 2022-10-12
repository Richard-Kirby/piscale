import tkinter as tk
import time
import HX711 as HX

class App(tk.Frame):
    def __init__(self,master=None):

        # Connect to the scale and zero it out.
        # create a SimpleHX711 object using GPIO pin 14 as the data pin,
        # GPIO pin 15 as the clock pin, -370 as the reference unit, and
        # -367471 as the offset
        self.hx = HX.SimpleHX711(14, 15, int(-370 / 1.244), -367471)
        self.hx.zero()

        tk.Frame.__init__(self, master)
        self.master = master
        self.time_label = tk.Label(text="", fg="Blue", font=("Helvetica", 18))
        #self.label.place(x=50,y=80)
        self.time_label.pack()
        self.weight_disp = tk.Label(text="", fg="Red", font=("Helvetica", 50))
        #self.weight_disp.place(x=50, y=100)
        self.weight_disp.pack()
        self.update_weight()
        # create a button
        self.zero_btn = tk.Button(self.master, text="Zero out", command=self.zero)
        self.zero_btn.pack()

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.time_label.configure(text=now)
        self.after(1000, self.update_clock)

    # Zero out the scale
    def zero(self):
        self.hx.zero()


    def update_weight(self):
        # Get the current weight on the scale
        weight = (f"{self.hx.weight(2)}")
        #print(weight)
        self.weight_disp.configure(text = weight)
        self.after(500, self.update_weight)

root = tk.Tk()
app=App(root)
root.wm_title("Fatman Scale")
root.geometry("200x200")
root.after(1000, app.update_clock)
root.mainloop()
