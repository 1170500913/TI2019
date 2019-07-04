# -*- coding: utf-8 -*
from car import Car
import RPi.GPIO as GPIO
import threading
import ultra
import camera
import arm
import rw
import socketserver
import threading
import socket

REGION_NUM = 10
threadLock = threading.Lock()
fileLock = threading.Lock()
map = {}
region = 0
turn_judge = 0
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

class main_thread(threading.Thread):

    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0

    def run(self):
        global region, sensors, monitor, map_changed, send_msg, recv_msg
        car = self.car
        finished = False
        count_down = 0 # 用于前进一段步长
        object_id = 0
        
        # 从文件读取map
        map = rw.readMap()

        send_msg = "DELIVERY ROBOT FREE\r\n"
        while (True):
#            threadLock.acquire()
            
#            threadLock.release()
            
            in_sensors = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            turn_flag = car.turn_judge(sensors)
            if (self.stat == 0):  # 等待状态
                car.stop()
                monitor = True
                if (recv_msg == 'CH'):
                    self.stat = 1
                    send_msg = "DELIVERY ROBOT WORKING\r\n"
                    recv_msg = ""
                    monitor = False

            if (self.stat == 1):  # 寻货状态
                car.line_patrol_forward(in_sensors, 1, turn_flag)

                if (region != 0):
                    self.stat = 5
                    send_msg = "DELIVERY 货物已全部入库\r\n"
                    finished = True
                    
                dist = car.distance()
                # print("dist = " + str(dist))
                detect = False
                if (dist < DIST):
                    detect = True
                else:
                    detect = False
                    
                if (detect == True):
                    car.stop()
                    object_id = camera.identify()
                    # print("object = " + str(object_id))
                    if (object_id == -1):  # 识别失败
                        self.stat = 2
                        count_down = 400
                    else:   # 识别成功
                        arm.catch()
                        finished = False
                        self.stat = 3

            if (self.stat == 2):   # 前进一段步长状态
                count_down -= 1
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                if (region != 0):
                    self.stat = 5
                    send_msg = "DELIVERY 货物已全部入库\r\n"
                    finished = True
                    
                if (count_down == 0):
                    self.stat = 1    # 前进步长结束，又回到寻货状态
            
            if (self.stat == 3):   # 离开停货区状态
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                if (region == 1):
                    self.stat = 4


            if (self.stat == 4):  # 寻找位置状态
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                dist = car.distance()
                detect = True
                if (dist < DIST):
                    detect = True
                else:
                    detect = False
                
                if (detect == False):
                    car.stop()
                    arm.release()    # 放下货物

                    fileLock.acquire()
                    map = rw.readMap()  # 读取原本
                    map[object_id] = region  # 更新map
                    rw.writeMap(map)
                    fileLock.release()
                    map_changed = True

                    self.stat = 5

                if (region == 0):
                	send_msg = "DELIVERY 仓库已满!请及时运出货物\r\n"
                	self.stat = 0

            if (self.stat == 5):   # 回停货区的途中
                car.line_patrol_forward(in_sensors, 1, turn_flag)
                if (region == 0):
                    if (finished):
                        send_msg = "DELIVERY ROBOT FREE\r\n"
                        self.stat = 0
                    else :
                        self.stat = 1


class count_thread(threading.Thread):
    def __init__(self, car: Car):
        threading.Thread.__init__(self)
        self.car = car
        self.stat = 0
    def run(self):
        global region, sensors
        car = self.car
        while (True):
            sensors = car.read_sensors()
            region = car.detect_line(sensors, region) % (REGION_NUM + 1)

class MyServer(socketserver.BaseRequestHandler):
    # 定义handle方法，函数名只能是handle
    def handle(self):
        global map_changed, send_msg, recv_msg, monitor
        conn = self.request
        # 打开文件
        with open(FILEPATH, mode='r+', encoding='utf-8') as f:
            content = f.read()
            
        # 发送map.txt内容
        conn.sendall(content.encode('utf-8'))

        # 进入监听全局变量，注意加锁
        while True:
            if map_changed:
                # 获取锁
                mutex.acquire()
                with open(FILEPATH, mode='r+', encoding='utf-8') as f:
                    content = f.read()  # 一次性读成一个字符串
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


class server_thread(threading.Thread):
    def __init__(self, ADDR):
        threading.Thread.__init__(self)
        self.ADDR = ADDR
    def run(self):
        socketserver.ThreadingTCPServer.allow_reuse_address = True
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

