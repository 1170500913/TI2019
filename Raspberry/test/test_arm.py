# -*- coding: utf-8 -*
from car import Car
from arm import Arm
import time


if __name__ == "__main__":
#    car = Car()
#    car.capture()
#    time.sleep(1)
#    car.unload()
    arm = Arm()
#	for i in range(2500, 0, -10):
    arm.servo_angle(arm.s1,2500)
    time.sleep(0.01)

    