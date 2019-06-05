# -*- coding: UTF-8 -*-
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
from car import Car
import threading

# 全局变量
count = 0   # 黑横线的数量

threadLock = threading.Lock()

# 巡线
class Thread1(threading.Thread):

    def __init__(self, car):
        threading.Thread.__init__(self)
        self.car = car

    def run(self):
        global count
        car = self.car
        while (True):
            sensors = car.read_sensors()
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
        global count
        car = self.car
        while (True):
            sensors = car.read_sensors()
            count = car.get_unload_pos(sensors, count)
            time.sleep(0.001)


if __name__ == "__main__":
    try:
        stop = int(input("最大黑横线："))
        car = Car()
        task1 = Thread1(car)
        task2 = Thread2(car)
        task1.start()
        task2.start()
        task1.join()
        task2.join()
    except KeyboardInterrupt:
        print("ERROR")
    finally:
        GPIO.cleanup()

