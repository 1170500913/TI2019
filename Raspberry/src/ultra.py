# 超声波测距
from RPi.GPIO as GPIO
from channel import *
import time

# 测距
def distance():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
         
    while GPIO.input(ECHO) == GPIO_LOW:
        pass
    start = time.time()
     
    while GPIO.input(ECHO) == GPIO_HIGH:
        pass
    stop = time.time()
     
    elapsed = stop - start
    distance = elapsed * 34000  # ms
    distance = distance / 2
    GPIO.cleanup()
    return distance

# 是否低于某距离
def isLowerThan(min = 30):
    dist = distance()
    if (dist < min):
        return True
    else:
        return False
