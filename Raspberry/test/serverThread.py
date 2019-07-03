# -*- coding: utf-8 -*
import socketserver
import threading
import socket
import re

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

map_changed = True
send_msg = "fdsafdsf"
recv_msg  = ''
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
            data = str(conn.recv(BUFSIZE), encoding='utf-8') #接受tcp消息
            if data:
                pattern = re.compile('(\d+,\d+ )+')
                if (pattern.match(data)):
                    # 覆盖写
                    with open(FILEPATH, mode='r+', encoding='utf-8') as f:
                        f.write(data) 
                else:
                    recv_msg = data
                data = ""


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(ADDR, MyServer)
    server.serve_forever()
