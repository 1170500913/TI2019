# -*- coding: utf-8 -*
from car import Car
import RPi.GPIO as GPIO
import threading
import ultra
import camera
import arm
import re
import rw

REGION_NUM = 5

forward = True
threadLock = threading.Lock()
map = {}
waited_object = []
region = 0
DIST = 10


class count_thread(threading.Thread):
    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region
        car = self.car
        while (True):
            threadLock.acquire()
            sensors = car.read_sensors()
            threadLock.release()
            region = car.detect_line(sensors, num, forward)


class main_thread(threading.Thread):

    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region, waited_object
        car = self.car
        target_object
        target_region

        count_down = 0 # 用于前进一段步长
        

        while True:
            sensors = car.read_sensors()
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            if (self.stat == 0):  # 待命状态

                #######Test#######
                test_object = input("输入要取的物品:")
                waited_object.append(test_object)
                ##################

                if (waited_object):  # 待抓物品不为空
                    target_object = waited_object[0]
                    del waited_object[0]
                    map = rw.readMap()
                    target_region = map[target_object]
                    self.stat = 1

            if (self.stat == 1):  # 巡线到目标区域
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == target_region) + 1:  # 到了目标区域的结束区,掉头

                    # 准备掉头
                    # 先转过一段距离, 以便状态4的判定
                    forward = False
                    count = 5000
                    while (count != 0):
                        car.right()
                        count -= 1
                    self.stat = 4

            if (self.stat == 2):  # 寻货状态
                car.line_patrol_forward(in_sensors, flag = 1, turn_flag = 0)
                if (region != target_region):
                    self.stat = 5
                    print("未找到目标货物")

                dist = car.distance()

                
                print("dist = " + str(dist))

                detect = False
                if (dist < DIST):
                    detect = True
                else:
                    detect = False
                    
                if (detect == True):
                    car.stop()
                    object_id = camera.identify()
                    print("object = " + str(object_id))
                    if (object_id == -1):  # 识别失败
                        self.stat = 3    # 前进一段步长
                        count_down = 400
                    elif (object_id == target_object):   # 识别成功
                        arm.catch()   # 抓取物品
                        self.stat = 5

                       

            if (self.stat == 3):   # 前进一段步长
                count_down -= 1
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region != target_region):
                    self.stat = 4
                    print("未找到目标货物")
                    finished = True
                if (count_down == 0):
                    self.stat = 2

            if (self.stat == 4):  # 掉头
                car.right()
                if (sensor[2] == 1): # 掉头结束，开始寻货 
                    car.stop()
                    self.stat == 2

                    

            if (self.stat == 5):   # 回到出发点
                
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == 0):
                    self.stat = 0
                    arm.release()

                    # 更新map
                    threadLock.acquire()
                    map = rw.readMap()
                    del map[target_object]
                    rw.writeMap(map)
                    threadLock.release()
