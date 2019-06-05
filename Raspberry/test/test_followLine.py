# -*- coding: UTF-8 -*-
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
from car import Car
import threading

# 全局变量
count = 0   # 黑横线的数量
sensors = [0] * 5

# 巡线
class Thread1(threading.Thread):

    def __init__(self, car,stop=10):
        threading.Thread.__init__(self)
        self.car = car
        self.stop = stop

    def run(self):
        global count, sensors
        car = self.car
        while (True):
            mid_three_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])  
            turn_flag = car.turn_judge(sensors)
            car.line_patrol_forward(mid_three_sensors, 1, turn_flag)
            if (count >= self.stop):
                car.stop()
                break

# 检测黑横线
class Thread2(threading.Thread):
    def __init__(self, car):
        threading.Thread.__init__(self)
        self.car = car

    def run(self):
        global count, sensors
        car = self.car
        while (True):
            count = car.get_unload_pos(sensors, count)

# 更新传感器
class Thread3(threading.Thread):
    def __init__(self, car):
        threading.Thread.__init__(self)
        self.car = car
    def run(self):
        global sensors
        while (True):
            sensors = car.read_sensors()


if __name__ == "__main__":
    try:

        stop = input("最大黑横线：")
        car = Car()
        task1 = Thread1(car, stop)
        task2 = Thread2(car)
        task3 = Thread3(car)
        task1.start()
        task2.start()
        task3.start()
        task1.join()
        task2.join()
        task3.join()
    except KeyboardInterrupt:
        print("ERROR")
    finally:
        GPIO.cleanup()

