# -*- coding: utf-8 -*
import socketserver
import threading
import socket
import re
import time


# 服务端开放的ip和端口号port
HOST = '172.20.10.13'
PORT = 2222
# 本地map文件路径
FILEPATH = './map.txt'
# 缓冲池大小
BUFSIZE = 1024
# 地址
ADDR = (HOST, PORT)
# 创建互斥锁
mutex = threading.Lock()
#
map_changed = True
send_msg = "PICK ROBOT WORKING\r\n"
recv_msg  = ''
#global map_changed, send_msg, recv_msg
class MyServer(socketserver.BaseRequestHandler):
    # 定义handle方法，函数名只能是handle
    def handle(self):
        global map_changed, send_msg, recv_msg
        conn = self.request
        # 打开文件
        with open(FILEPATH, mode='r+', encoding='utf-8') as f:
            content = f.read()
            
        # 发送map.txt内容
        conn.sendall(content.encode('utf-8'))

        # 进入监听全局变量，注意加锁
        while True:
            time.sleep(1)
            
            mutex.acquire()
            print('send:' + send_msg)
            conn.sendall(send_msg.encode('utf-8'))
#                send_msg = ''
            mutex.release()
            send_msg = "DELIVERY ROBOT FREE\r\n"
#            data = str(conn.recv(BUFSIZE), encoding='utf-8') #接受tcp消息
#            if data:
#                pattern = re.compile('(\d+,\d+ )+')
#                if (pattern.match(data)):
#                    # 覆盖写
#                    with open(FILEPATH, mode='r+', encoding='utf-8') as f:
#                        f.write(data) 
#                else:
#                    
#                    recv_msg = data
#                    print("收到消息:" + recv_msg)
#                data = ""


if __name__ == '__main__':
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(ADDR, MyServer)
    server.serve_forever()
