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


REGION_NUM = 5

forward = True
threadLock = threading.Lock()
fileLock = threading.Lock()
map = {}
waited_object = []
region = 0
DIST = 10
sensors = [0] * 5

# 服务端开放的ip和端口号port
HOST = '172.20.10.13'
PORT = 2222
# 地址
ADDR = (HOST, PORT)
# 本地map文件路径
FILEPATH = './map.txt'
# 缓冲池大小
BUFSIZE = 1024
# 创建互斥锁
mutex = threading.Lock()

map_changed = False
send_msg = ""
recv_msg = ""
monitor = False

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
        global region, waited_object
        global forward, sensors, map_changed, send_msg, recv_msg, monitor
        car = self.car
        target_object = 0
        target_region = 0
        is_find = False

        count_down = 0 # 用于前进一段步长
        
        send_msg = "PICK ROBOT FREE\r\n"
        while True:
            sensors = car.read_sensors()
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            if (self.stat == 0):  # 待命状态
#                print("状态0")
                car.stop()
                #######Test#######
                # test_object = int(input("输入要取的物品:"))
                # waited_object.append(test_object)
                ##################
                monitor = True
                pat = re.compile("QH:.+")
                if (pat.match(recv_msg)):
                    recv_msg = recv_msg.strip()
                    print("处理消息:" + recv_msg)
                    recv_msg = recv_msg[3:]
                    entrys = recv_msg.split(",")
                    for i in range(0, len(entrys)):
                        if (re.compile("\d+").match(entrys[i])):
                            waited_object.append(int(entrys[i]))
                    monitor = False
                    recv_msg = ""

                if (waited_object):  # 待抓物品不为空
                    forward = True
                    is_find = False
                    target_object = waited_object[0]
                    del waited_object[0]
                    map = rw.readMap()
                    target_region = map[target_object]

                    send_msg = "PICK ROBOT WORKING\r\n"
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
                    send_msg = "PICK 未找到目标货物\r\n"

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
                    send_msg = "PICK 未找到目标货物\r\n"
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
                turn_flag = car.turn_judge(sensors)
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                if (region == 0):
                    self.stat = 0
                    car.stop()
                    send_msg = "PICK ROBOT FREE\r\n"
                    # 更新map
#                    if (is_find):
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

class MyServer(socketserver.BaseRequestHandler):
    # 定义handle方法，函数名只能是handle
    def handle(self):
        global map_changed, send_msg, recv_msg, monitor
        conn = self.request
        # 打开文件
        with open(FILEPATH, mode='r+', encoding='utf-8') as f:
            content = f.read()
            print(content)
        # 发送map.txt内容
        conn.sendall(content.encode('utf-8'))
#        recv_task = server_thread_recv(conn)
#        recv_task.start()
        # 进入监听全局变量，注意加锁
        while True:
            if map_changed:
                # 获取锁
                mutex.acquire()
                with open(FILEPATH, mode='r+', encoding='utf-8') as f:
                    content = f.read()  # 一次性读成一个字符串
                    print(content)
                conn.sendall(content.encode('utf-8'))
                map_changed = False
                # 释放锁
                mutex.release()
                

            # 判断msg非空
            if send_msg:
                mutex.acquire()
                conn.sendall(send_msg.encode('utf-8'))
                send_msg = ''
                mutex.release()
            while monitor:
                data = str(conn.recv(BUFSIZE), encoding='utf-8') #接受tcp消息
                if data:
                    pattern = re.compile('(\d+,\d+ )+')
                    if (pattern.match(data)):
                        # 覆盖写
                        with open(FILEPATH, mode='r+', encoding='utf-8') as f:
                            f.write(data) 
                    else:
                    
                        recv_msg = data
                        print("收到消息:" + recv_msg)
                    data = ""

#class server_thread_recv(threading.Thread):
#    def __init__(self, conn):
#        threading.Thread.__init__(self)
#        self.conn = conn
#    def run(self):
#        global recv_msg
#        while(True):
#            data = str(self.conn.recv(BUFSIZE), encoding='utf-8') #接受tcp消息
#            if data:
#                pattern = re.compile('(\d+,\d+ )+')
#                if (pattern.match(data)):
#                    # 覆盖写
#                    with open(FILEPATH, mode='r+', encoding='utf-8') as f:
#                        f.write(data) 
#                else:
#                    recv_msg = data
#                    print("收到消息:" + recv_msg)
#                data = ""

class server_thread(threading.Thread):
    def __init__(self, ADDR):
        threading.Thread.__init__(self)
        self.ADDR = ADDR
    def run(self):
#        socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        server = socketserver.ThreadingTCPServer(self.ADDR, MyServer)
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