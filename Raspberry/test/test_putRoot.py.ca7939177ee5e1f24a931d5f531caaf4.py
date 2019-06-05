# -*- coding: utf-8 -*
from car import Car
import RPi.GPIO as GPIO
import threading
import ultra
import camera
import arm

map = {}
region = 0

class main_thread(threading.Thread):

    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region
        car = self.car
        finished = False
        count_down  # 用于前进一段步长
        object_id = 0
        while (True):
            sensors = car.read_sensors()
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            if (self.stat == 0):  # 等待状态
                ch = input("输入s开始")
                if (ch == 's'):
                    self.stat = 1

            if (self.stat == 1):  # 寻货状态
                car.line_patrol_forward(in_sensors, 1, 0)

                if (region != 0):
                    self.stat = 5
                    print("货物搬完了")
                    finished = True

                detect = ultra.detect_object()
                if (detect == True):
                    car.stop()
                    object_id = camera.identify()
                    if (object_id == -1):  # 识别失败
                        self.stat = 2
                        count_down = 100
                    else:   # 识别成功
                        arm.catch()
                        self.stat = 3

            if (self.stat == 2):   # 前进一段步长状态
                count_down -= 1
                car.line_patrol_forward(in_sensors, 1, 0)
                if (count_down == 0):
                    self.stat = 1    # 前进步长结束，又回到寻货状态
            
            if (self.stat == 3):   # 离开停货区状态
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == 1):
                    self.stat = 4


            if (self.stat == 4):  # 寻找位置状态
                car.line_patrol_forward(in_sensors, 1, 0)
                detect = ultra.detect_object()
                if (detect == False):
                    arm.relase()
                    map[object_id] = region  # 更新map
                    self.stat = 5

            if (self.stat == 5)   # 回停货区的途中
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == 0)
                    if (finished):
                        self.stat = 0
                    else 
                        self.stat = 1


class count_thread(threading.Thread):
    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0
     def run(self):
        global count
        car = self.car
        while (True):
            threadLock.acquire()
            sensors = car.read_sensors()
            threadLock.release()
            count = car.get_unload_pos(sensors, count)
