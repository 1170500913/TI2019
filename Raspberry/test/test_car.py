  # -*- coding: utf-8 -*
  
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
from car import Car

if __name__ == '__main__':
    try:
        ch = input("::")
        car = Car()
        while (True):
            if (ch == 'w'):
                car.forward(60, 60)
            elif (ch == 's'):
                car.back()
            elif (ch == 'a'):
                car.left()
            elif (ch == 'd'):
                car.right()
    except KeyboardInterrupt:
        print('ERROR')

    finally:
        GPIO.cleanup()
