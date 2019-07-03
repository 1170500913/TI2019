# -*- coding: utf-8 -*
from car import Car
import RPi.GPIO as GPIO
import threading
import ultra
import camera
import arm
import re
import rw
import socketserver
import threading
import socket
import serverThread

REGION_NUM = 5

forward = True
threadLock = threading.Lock()
fileLock = threading.Lock()
map = {}
waited_object = []
region = 0
DIST = 10
sensors = [0] *5

# 服务端开放的ip和端口号port
HOST = '172.20.10.13'
PORT = 2222

# 地址
ADDR = (HOST, PORT)

map_changed = False
send_msg = ""
recv_msg = ""

class count_thread(threading.Thread):
    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region, forward, sensors
        car = self.car
        while (True):
#            threadLock.acquire()
            sensors = car.read_sensors()
#            threadLock.release()
            region = car.detect_line(sensors, region, forward)


class main_thread(threading.Thread):

    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region, waited_object, forward, sensors
        car = self.car
        target_object = 0
        target_region = 0
        is_find = False

        count_down = 0 # 用于前进一段步长
        

        while True:
            sensors = car.read_sensors()
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            if (self.stat == 0):  # 待命状态
                car.stop()
                #######Test#######
                # test_object = int(input("输入要取的物品:"))
                # waited_object.append(test_object)
                ##################

                pat = re.compile("qh:.+")
                if (pat.match(recv_msg)):
                    recv_msg = recv_msg[0:len(recv_msg) - 1]
                    entrys = recv_msg.split("[,\n\r]")
                    for entry in entrys:
                        if (re.compile("\d+").match(entry)):
                            waited_object.append(int(entry))

                if (waited_object):  # 待抓物品不为空
                    forward = True
                    is_find = False
                    target_object = waited_object[0]
                    del waited_object[0]
                    map = rw.readMap()
                    target_region = map[target_object]
                    self.stat = 1

            if (self.stat == 1):  # 巡线到目标区域
#                print("状态1")
                
                turn_flag = car.turn_judge(sensors)
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                
                if (region == target_region + 1):  # 到了目标区域的结束区,掉头
                    # 先往前走一点
                    count_down = 2000
                    self.stat = 6

                    

            if (self.stat == 2):  # 寻货状态
#                print("状态2")
                
                
                    
                turn_flag = car.turn_judge(sensors)
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                
                if (region != target_region):
                    self.stat = 5
                    print("未找到目标货物")

                dist = car.distance()

                
                print("dist = " + str(dist))

                detect = False
                if (dist < DIST):
                    detect = True
                    
                if (detect == True):
                    car.stop()
                    object_id = camera.identify()
                    print("object = " + str(object_id))
                    if (object_id == target_object):   # 识别成功
                        is_find = True
                        arm.catch()   # 抓取物品
                        self.stat = 5
                    else:
                        self.stat = 3    # 前进一段步长
                        count_down = 400

                       

            if (self.stat == 3):   # 前进一段步长
#                print("状态3")
                count_down -= 1
                
                turn_flag = car.turn_judge(sensors)
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                
                if (region != target_region):
                    self.stat = 5
                    print("未找到目标货物")
                if (count_down == 0):
                    self.stat = 2

            if (self.stat == 4):  # 掉头
#                print("状态4")
                car.line_patrol_forward(in_sensors, 1, 0)
                if (sensors[2] == 1): # 掉头结束，开始寻货 
                    car.stop()
                    print("掉头结束")
                    self.stat = 2

                    

            if (self.stat == 5):   # 回到出发点
#                print("状态5")
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                if (region == 0):
                    self.stat = 0
                    car.stop()

                    # 更新map
                    if (is_find):
                        fileLock.acquire()
                        map = rw.readMap()
                        arm.release()
                        del map[target_object]
                        rw.writeMap(map)
                        fileLock.release()
                        map_changed = True

            if (self.stat == 6):   # 到达目标区域后, 再前进一段步长
                count_down -= 1
                
                turn_flag = car.turn_judge(sensors)
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                
                if (count_down == 0):
                    # 准备掉头
                    # 先转过一段距离, 以便状态4的判定
                    forward = False
                    region -= 1 # 减去多出的区域
                    count = 10000
                    while (count != 0):
                        car.right()
                        count -= 1
                    self.stat = 4

class server_thread(threading.Thread):
    def __init__(self, ADDR):
        threading.Thread.__init__(self)
        self.ADDR = ADDR
    def run(self):
        server = socketserver.ThreadingTCPServer(self.ADDR, serverThread.MyServer)
        server.serve_forever()

if __name__ == "__main__":
    try:
        car = Car()
        task1 = main_thread(car)
        task2 = count_thread(car)
        task3 = server_thread(ADDR)

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