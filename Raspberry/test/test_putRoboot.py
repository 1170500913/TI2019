# -*- coding: utf-8 -*
from car import Car
import RPi.GPIO as GPIO
import threading
import ultra
import camera
import arm

threadLock = threading.Lock()
map = {}
region = 0
DIST = 10

class main_thread(threading.Thread):

    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region
        car = self.car
        finished = False
        count_down = 0 # 用于前进一段步长
        object_id = 0
        while (True):
            sensors = car.read_sensors()
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            if (self.stat == 0):  # 等待状态
                car.stop()
                ch = input("输入s开始")
                if (ch == 's'):
                    self.stat = 1

            if (self.stat == 1):  # 寻货状态
                car.line_patrol_forward(in_sensors, 1, 0)

                if (region != 0):
                    self.stat = 5
                    print("没有可搬的货物")
                    finished = True
                    
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
                        self.stat = 2
                        count_down = 400
                    else:   # 识别成功
                        arm.catch()
                        finished = False
                        self.stat = 3

            if (self.stat == 2):   # 前进一段步长状态
                count_down -= 1
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region != 0):
                    self.stat = 5
                    print("没有可搬的货物")
                    finished = True
                    
                if (count_down == 0):
                    self.stat = 1    # 前进步长结束，又回到寻货状态
            
            if (self.stat == 3):   # 离开停货区状态
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == 1):
                    self.stat = 4


            if (self.stat == 4):  # 寻找位置状态
                car.line_patrol_forward(in_sensors, 1, 0)
                dist = car.distance()
                detect = True
                if (dist < DIST):
                    detect = True
                else:
                    detect = False
                
                if (detect == False):
                    car.stop()
                    arm.relase()
                    map[object_id] = region  # 更新map
                    self.stat = 5

                if (region == 0):
                	print("货架已经满了")
                	self.stat = 0

            if (self.stat == 5):   # 回停货区的途中
                car.line_patrol_forward(in_sensors, 1, 0)
                if (region == 0):
                    if (finished):
                        self.stat = 0
                    else :
                        self.stat = 1


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
            num = region
            region = car.get_unload_pos(sensors, num)

if __name__ == "__main__":
    try:
        car = Car()
        task1 = main_thread(car)
        task2 = count_thread(car)
        task1.start()
        task2.start()
        task1.join()
        task2.join()
    except KeyboardInterrupt:
        print("ERROR")
    finally:
        GPIO.cleanup()

