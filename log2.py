import logging

mylog = logging.getLogger('scaleLogger')

def dum():
    mylog.error("Error from Log2")

if __name__ == '__main__':
    dum()