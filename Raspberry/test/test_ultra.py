from car import Car
import RPi.GPIO as GPIO
import time

car = Car()
while True:
    time.sleep(1)
    print(str(car.distance()))
        