# Connect to the HX711 directly, not via the library
import time
import pigpio

pi= pigpio.pi()

# data pin - data is pushed out bit by bit.
data_pin = 14
clock_pin = 15
while True:
    pi.write(clock_pin, 0) # Write the clock pin low - this indicates pi is waiting for input to be ready.

    while pi.read(data_pin) == 1: # Wait until the chip indiates it is ready by outputting a 1.
        pass

    code =[]

    delay = 1/10000000
    #print(delay)

    for pulse in range(24):
        #time.sleep(delay)
        pi.write(clock_pin, 1)  # Write the clock pin high - this requests the next bit.
        #time.sleep(delay)
        #data_in = pi.read(data_pin)
        #print(f"{data_in}")
        code.append (pi.read(data_pin)) # Read and append the bit to the array.
        #time.sleep(delay)
        pi.write(clock_pin, 0)  # Write the clock pin low - this allows the next bit to be written.
        #time.sleep(delay*600)

    print(code)
    time.sleep(2)

