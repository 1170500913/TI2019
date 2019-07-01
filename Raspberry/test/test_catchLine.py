# -*- coding: UTF-8 -*-
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
from car import Car


if __name__ == "__main__":
    try:
        car = Car()
        count = 0
        while (True):
            car.stop()
#            threadLock.acquire()
            sensors = car.read_sensors()
#            threadLock.release()
            count = car.get_unload_pos(sensors, count)
            
#            time.sleep(0.001)
    except KeyboardInterrupt:
        print("ERROR")
    finally:
        GPIO.cleanup()

