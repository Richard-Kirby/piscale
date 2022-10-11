from datetime import datetime
import HX711 as HX


# print(hx.__version__)

print("start")
# create a SimpleHX711 object using GPIO pin 2 as the data pin,
# GPIO pin 3 as the clock pin, -370 as the reference unit, and
# -367471 as the offset
with HX.SimpleHX711(14, 15, int(-370 / 1.244), -367471) as hx:
  print("with")
  # set the scale to output weights in ounces
  # hx.setUnit(Mass.Unit.)

  # zero the scale
  hx.zero()

  weight_list=[]

  # constantly output weights using the median of 35 samples
  while True:
    weight_list.append(hx.weight(2)) #eg. 1.08 oz
    if len(weight_list) == 10:
      print(datetime.now(), weight_list)
      weight_list=[]


