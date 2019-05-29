# -*- coding: UTF-8 -*-
import os
from PIL import Image
import pytesseract
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
from ir_lib import *
from SunFounder_PCA9685 import Servo
import threading
import urllib, urllib2, base64, sys
import ssl, json

lock = threading.Lock()
myservo = []

lf_r1, lf_m, lf_l1, lf_r2, lf_l2 = 0, 0, 0, 0, 0
msensor = 24
rsensor1 = 27
lsensor1 = 22
rsensor2 = 25
lsensor2 = 10

# 设置速度
Llowspeed = 68
Rlowspeed = 70
Lhigspeed = 68
Rhigspeed = 70
HMidspeed = 35
LMidspeed = 35
minspeed = 30
speedx = 70

remote_control = 0

for i in range(0, 4):
    myservo.append(Servo.Servo(i))  # channel 1
    Servo.Servo(i).setup()
    print('myservo%s' % i)


class Arm(object):
    def __init__(self, s1=0, s2=1, s3=2):
        self.s1 = s1  # 底盘
        self.s2 = s2  # 中间
        self.s3 = s3  # 夹持器

    def servo_angle(self, snum, value):
        global angle
        angle = (value - 500) / (100 / 9)
        myservo[snum].write(angle)

    # 初始化位置
    def setup(self):
        self.servo_angle(self.s1, 1500)  # 底盘
        self.servo_angle(self.s2, 1500)
        self.servo_angle(self.s3, 1500)  # 夹持器

    # 夹取
    def step2(self):
        for i in range(1500, 1871, 10):
            self.servo_angle(self.s2, i)  # Mservo_up
            time.sleep(0.01)

    def step3(self):
        for i in range(1500, 2401, 10):
            self.servo_angle(self.s3, i)  # Hservo_open
            time.sleep(0.01)

    def step4(self):
        for i in range(1430, 2501, 10):
            self.servo_angle(self.s1, i)  # Lservo_turn
            time.sleep(0.01)

    def step5(self):
        for i in range(1870, 1551, -10):
            self.servo_angle(self.s2, i)  # Mservo_down
            time.sleep(0.01)

    def step6(self):
        for i in range(2401, 1201, -10):
            self.servo_angle(self.s3, i)  # Hservo_close
            time.sleep(0.01)

    def step7(self):
        for i in range(1550, 1871, 10):
            self.servo_angle(self.s2, i)  # Mservo_up
            time.sleep(0.01)

    def step8(self):
        for i in range(2500, 1431, -10):
            self.servo_angle(self.s1, i)  # Lservo_turn
            time.sleep(0.01)

    # 卸载
    def step10(self):
        for i in range(1430, 2501, 10):
            self.servo_angle(self.s1, i)  # Lservo_turn
            time.sleep(0.01)

    def step11(self):
        for i in range(1870, 1501, -10):
            self.servo_angle(self.s2, i)  # Mservo_down
            time.sleep(0.01)

    def step12(self):
        for i in range(1500, 2401, 10):
            self.servo_angle(self.s3, i)  # Hservo_open
            time.sleep(0.01)

    # def step13(self):
        # for i in range(1500,1871,10):
        # self.servo_angle(self.s2,i) #Mservo_up
        # time.sleep(0.01)

    def step14(self):
        for i in range(2500, 1431, -10):
            self.servo_angle(self.s1, i)  # Lservo_turn
            time.sleep(0.01)

    def step15(self):
        for i in range(2400, 1501, -10):
            self.servo_angle(self.s3, i)  # Hservo_close
            time.sleep(0.01)


class Car(object):
    def __init__(self, rsensor1=27, rsensor2=25, msensor=24, lsensor1=22, lsensor2=10,
                 I1=7, EA=13, I3=8, EB=9, freq=50):
        # self.loadflag = 0  # 负载标志
        self.rsensor1 = rsensor1
        self.rsensor2 = rsensor2
        self.msensor = msensor
        self.lsensor1 = lsensor1
        self.lsensor2 = lsensor2

        self.times = 0
        self.I1 = I1
        self.EA = EA
        self.I3 = I3
        self.EB = EB
        self.freq = freq

        self.fsm = 0
        self.curr_state = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.rsensor1, GPIO.IN)
        GPIO.setup(self.rsensor2, GPIO.IN)
        GPIO.setup(self.msensor, GPIO.IN)
        GPIO.setup(self.lsensor1, GPIO.IN)
        GPIO.setup(self.lsensor2, GPIO.IN)


        GPIO.setup(self.I1, GPIO.OUT)
        GPIO.setup(self.EA, GPIO.OUT)
        GPIO.setup(self.I3, GPIO.OUT)
        GPIO.setup(self.EB, GPIO.OUT)

        self.my_pwmA = GPIO.PWM(self.EA, self.freq)
        self.my_pwmB = GPIO.PWM(self.EB, self.freq)

        self.last_pwmA = 0
        self.last_pwmB = 0

        self.my_pwmA.start(self.last_pwmA)
        self.my_pwmB.start(self.last_pwmB)

        self.slip_cnt = 0

        self.unload_flag = 0
        self.last_state = 0
        self.now_state = 0
        self.speed_flag = 0

        self.last_sensor = [0] * 5

    def forward(self, duty_b=50, duty_a=50):  # left  right
        # print("forward")
        GPIO.output(self.I1, True)
        GPIO.output(self.I3, True)
        if duty_a != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_a)
            self.last_pwmA = duty_a
        if duty_b != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_b)
            self.last_pwmB = duty_b
            
    def back(self, duty_b=50, duty_a=50):  # left  right
        # print("forward")
        GPIO.output(self.I1, False)
        GPIO.output(self.I3, False)
        if duty_a != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_a)
            self.last_pwmA = duty_a
        if duty_b != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_b)
            self.last_pwmB = duty_b
            
    def right(self, duty_cycle=50):
        # print("left")
        GPIO.output(self.I1, True)
        GPIO.output(self.I3, False)
        if duty_cycle != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_cycle)
            self.last_pwmA = duty_cycle
        if duty_cycle != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_cycle)
            self.last_pwmB = duty_cycle

    def left(self, duty_cycle=50):
        # print("right")
        GPIO.output(self.I1, False)
        GPIO.output(self.I3, True)
        if duty_cycle != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_cycle)
            self.last_pwmA = duty_cycle
        if duty_cycle != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_cycle)
            self.last_pwmB = duty_cycle

    def stop(self, duty_cycle=0):
        # print("stop")
        GPIO.output(self.I1, True)
        GPIO.output(self.I3, False)
        if duty_cycle != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_cycle)
            self.last_pwmA = duty_cycle
        if duty_cycle != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_cycle)
            self.last_pwmB = duty_cycle

    def read_sensors(self):
        sensors = [0] * 5
        sensors[0] = GPIO.input(self.lsensor2)
        sensors[1] = GPIO.input(self.lsensor1)
        sensors[2] = GPIO.input(self.msensor)
        sensors[3] = GPIO.input(self.rsensor1)
        sensors[4] = GPIO.input(self.rsensor2)
        return sensors

    # 图像识别
    def characterRecognition(self, path):
        access_token = '24.977dffd3097a7d82bb3ec001cd0f855d.2592000.1558054903.282335-16037182'
        url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=' + access_token
        f = open(path, 'rb')

        img = base64.b64encode(f.read())
        params = {"image": img}
        params = urllib.urlencode(params)
        request = urllib2.Request(url, params)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        response = urllib2.urlopen(request)
        content = response.read()
        content = json.loads(content)
        # print(content)
        # result = content['words_result'][0]['words']
        result = content['words_result']
        num = content['words_result_num']
        # print ('num:',num)
        if (num != 0):  # Prevent multiple characters
            print('result:' + result[0]['words'])
            if '0' in result[0]['words']:
                print('return:Y')
                return 'Y'
        return 'N'
        # return 'Y'

    # 图像处理
    def pre(self, path, path2):
        img = Image.open(path)
        cropped = img.crop((0, 0, 640, 460))  # (left, upper, right, lower)
        cropped.save(path2)

    def capture(self):
        print("capture")
        self.stop()
        b = Arm()
        b.step2()
        b.step3()
        b.step4()
        b.step5()
        b.step6()
        b.step7()
        b.step8()
        # os.system("sudo python capture.py")
        # pass

    def unload(self):
        print("unload")
        self.stop()
        # os.system("sudo python unload.py")
        # pass
        b = Arm()
        b.step10()
        b.step11()
        b.step12()
        b.step14()
        b.step15()

    def attach_fsm(self, state, fsm):
        self.fsm = fsm
        self.curr_state = state
        self.fsm.enter_state(self)

    def change_fsm(self, new_state, new_fsm):
        self.fsm.exit_state(self)
        self.curr_state = new_state
        self.fsm = new_fsm
        self.fsm.enter_state(self)
        self.fsm.exec_state(self)

    def keep_fsm(self):
        self.fsm.exec_state(self)

    def get_unload_pos(self, sensors=[0] * 5, flag_cnt=0):
        if sensors[4] == 1 and sensors[2] == 1:  # m and r2 is black at the same time
            self.now_state = 0
        else:
            self.now_state = 1
        if self.now_state == 0 and self.last_state == 1:
            flag_cnt += 1
        self.last_state = self.now_state
        return flag_cnt

    def line_patrol(self, sensors=0, flag=0, turn_flag=0):
        if flag == 1:
            if sensors == '010':
                self.slip_cnt = 0
                self.forward(Rhigspeed, Lhigspeed) #(右侧电机，左侧电机)
            elif sensors == '100':
                self.slip_cnt = 0
                self.forward(speedx,minspeed) #左转
                
            elif sensors == '110':
                #self.forward(Rhigspeed,HMidspeed) #左转
                self.slip_cnt += 20
                speed = speed = Rhigspeed - self.slip_cnt/10
                if speed < HMidspeed:
                    self.slip_cnt = 0
                    speed = HMidspeed
                self.forward(Rhigspeed,speed)
                
            elif sensors == '001':
                self.slip_cnt = 0
                self.forward(minspeed,speedx) #右转
            elif sensors == '011':
                #self.forward(HMidspeed,Lhigspeed) #右转
                self.slip_cnt += 20
                speed = speed = Rhigspeed - self.slip_cnt/10
                if speed < HMidspeed:
                    self.slip_cnt = 0
                    speed = HMidspeed
                self.forward(speed,Rhigspeed)  
                
            elif sensors == '111':
                self.slip_cnt = 0
                self.forward(Rhigspeed,Lhigspeed) 
            elif sensors == '000':
                if turn_flag == 1:
                    self.left(Lhigspeed)
                else:
                    self.right(Rhigspeed)
            else:
                self.stop()
        else:
            if sensors == '010':
                self.forward(Rlowspeed, Llowspeed)
            elif sensors == '100':
                self.forward(speedx,0)
            elif sensors == '110': #turn_left
                self.forward(Rlowspeed,LMidspeed)            
            elif sensors == '001':
                self.forward(0,speedx)
            elif sensors == '011': #turn_right
                self.forward(LMidspeed,Llowspeed)           
            elif sensors == '111':
                self.forward(Rlowspeed,Llowspeed)
            elif sensors == '000':
                if turn_flag == 1:
                    self.left(Rlowspeed)
                else:
                    self.right(Llowspeed)
            else:
                self.stop()

    def turn_judge(self, sensors):
        line_flag = str(sensors[1]) + str(sensors[2]) + str(sensors[3])
        if line_flag == '000':
            if self.last_sensor[0] == 1:
                return 1
            elif self.last_sensor[4] == 1:
                return 2
            else:
                return 3
        else:
            self.last_sensor = sensors
            return 0


# 遥控器触发后，初始化设置
class idle_fsm(object):
    def enter_state(self, obj):
        obj.loadflag = 0
        print('0 state start')

    def exec_state(self, obj):
        # order = input('start:1/0?') #接收启动任务指令
        obj.task_time = 1  # 任务需要次数
        obj.unload_position = 1  # 任务需要次数
        # obj.targ_text = ['1', '2', '3']  # 任务目标
        global remote_control
        lock.acquire()
        if remote_control == 1:
            obj.state = 1
        elif remote_control == 2:
            obj.speed_flag = 1
            obj.state = 6
        elif remote_control == 3:
            obj.speed_flag = 0
            obj.state = 6
        elif remote_control == 5:
            obj.speed_flag = 0
            obj.state = 7
        elif remote_control == 6:
            obj.speed_flag = 1
            obj.state = 7
        elif remote_control == 7:
            obj.speed_flag = 0
            obj.state = 8
        elif remote_control == 8:
            obj.speed_flag = 1
            obj.state = 8
        elif remote_control == 0:
            obj.state = 0
            obj.stop()
        else:
            obj.state = 0
        lock.release()

    def exit_state(self, obj):
        print('0 state end')


class go_fsm(object):
    def enter_state(self, obj):
        print('1 state start')

    def exec_state(self, obj):
        sensor_flag = obj.read_sensors()
        line_flag = str(sensor_flag[1]) + str(sensor_flag[2]) + str(sensor_flag[3])
        if sensor_flag[0] == 1:
            if sensor_flag[4] == 1:  # l2 and r2 is black at the same time
                print('no target')
                obj.state = 5
            elif sensor_flag[2] == 1:  # l2 and m is black at the same time
                print('1 state stop flag')
                obj.state = 2
            else:
                obj.line_patrol(line_flag, 1)
                obj.state = 1
        else:
            obj.line_patrol(line_flag, 1)
            obj.state = 1

        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('1 state end')


class photo_fsm(object):
    def enter_state(self, obj):
        print('2 state start')

    def exec_state(self, obj):
        obj.stop()
        time.sleep(0.5)
        os.system('./web_cam.sh')
        path = r'/home/pi/image.jpg'
        path2 = r'/home/pi/image1.jpg'
        obj.pre(path, path2)
        get_result = obj.characterRecognition(path2)
        if get_result == 'Y':
            # print('True')
            obj.state = 3  # 进入状态 3
        if get_result == 'N':
            # print('False')
            while True:
            obj.forward(Rhigspeed, Lhigspeed)
            obj.state = 1  # 返回直行状态

        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('2 state end')


class capture_fsm(object):  # 抓取并直行不停
    def enter_state(self, obj):
        print('3 state start')

    def exec_state(self, obj):
        if obj.loadflag == 0:
            obj.capture()  # 抓取程序
            obj.loadflag = 1
        else:
            sensor_flag = obj.read_sensors()
            line_flag = str(sensor_flag[1]) + str(sensor_flag[2]) + str(sensor_flag[3])
            if sensor_flag[4] == 1 and sensor_flag[2] == 1:  # m and r2 is black at the same time
                print('fine unload flag')
                obj.unload_flag = 1
                obj.state = 4
            else:
                obj.line_patrol(line_flag, 1)
                obj.state = 3

        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('3 state end')


class unload_fsm(object):
    def enter_state(self, obj):
        print('4 state start')

    def exec_state(self, obj):
        sensor_flag = obj.read_sensors()
        line_flag = str(sensor_flag[1]) + str(sensor_flag[2]) + str(sensor_flag[3])
        obj.unload_flag = obj.get_unload_pos(sensor_flag, obj.unload_flag)
        if obj.unload_flag == obj.unload_position:
            if obj.loadflag == 1:
                obj.stop()
                obj.unload()  # 卸载物体
                obj.loadflag = 0
                obj.task_time -= 1
        if sensor_flag[2] == 1 and sensor_flag[4] == 1:
            obj.state = 5
        else:
            obj.line_patrol(line_flag, 1)
            obj.state = 4

        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('4 state end')


class throw_over(object):
    def enter_state(self, obj):
        print('5 state start')

    def exec_state(self, obj):
        obj.unload_flag = 0
        sensor_flag = obj.read_sensors()
        line_flag = str(sensor_flag[1]) + str(sensor_flag[2]) + str(sensor_flag[3])
        # if sensor_flag[0] == 0 and sensor_flag[4] == 0:
        if sensor_flag[0] == 0:
            if obj.task_time == 0:
                obj.stop()
                obj.state = 0
            else:
                obj.state = 1
        else:
            obj.line_patrol(line_flag, 1)

        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('5 state end')


class follow(object):
    def enter_state(self, obj):
        print('6 state start')

    def exec_state(self, obj):
        sensor_flag = obj.read_sensors()
        line_flag = str(sensor_flag[1]) + str(sensor_flag[2]) + str(sensor_flag[3])
        turn_flag = obj.turn_judge(sensor_flag)
        print(line_flag)
        obj.line_patrol(line_flag, obj.speed_flag, turn_flag)
        global remote_control
        lock.acquire()
        if remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('6 state end')


class turn_run(object):
    def enter_state(self, obj):
        print('7 state start')

    def exec_state(self, obj):
        lock.acquire()
        global remote_control
        if remote_control == 5:
            obj.left(70)
        elif remote_control == 6:
            obj.right(100)
        elif remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('7 state end')

class forward_run(object):
    def enter_state(self, obj):
        print('8 state start')

    def exec_state(self, obj):
        lock.acquire()
        global remote_control
        if remote_control == 7:
            obj.forward(Rlowspeed,Llowspeed)
        elif remote_control == 8:
            obj.back(Rhigspeed,Lhigspeed)
        elif remote_control == 0:
            obj.state = 0
            obj.stop()
        lock.release()

    def exit_state(self, obj):
        print('8 state end')

def follow_task():
    fsms = {}
    fsms[0] = idle_fsm()
    fsms[1] = go_fsm()
    fsms[2] = photo_fsm()
    fsms[3] = capture_fsm()
    fsms[4] = unload_fsm()
    fsms[5] = throw_over()
    fsms[6] = follow()
    fsms[7] = turn_run()
    fsms[8] = forward_run()

    a = Arm()
    a.setup()
    c = Car()
    c.attach_fsm(0, fsms[0])
    c.state = 0
    while True:
        time.sleep(0.01)
        if c.state == c.curr_state:
            c.keep_fsm()
        else:
            c.change_fsm(c.state, fsms[c.state])


def control_task():
    while True:
        time.sleep(0.5)
        ir = ir_check()
        button = ir.next_key()
        global remote_control
        if button == 'KEY_NUMERIC_0':
            lock.acquire()
            remote_control = 0
            lock.release()
        elif button == 'KEY_NUMERIC_1':
            lock.acquire()
            remote_control = 1
            lock.release()
        elif button == 'KEY_NUMERIC_2':
            lock.acquire()
            remote_control = 2
            lock.release()
        elif button == 'KEY_NUMERIC_3':
            lock.acquire()
            remote_control = 3
            lock.release()
        elif button == 'KEY_NUMERIC_4':
            lock.acquire()
            remote_control = 4
            lock.release()
        elif button == 'KEY_NUMERIC_5':
            lock.acquire()
            remote_control = 5
            lock.release()
        elif button == 'KEY_NUMERIC_6':
            remote_control = 6
        elif button == 'KEY_NUMERIC_7':
            lock.acquire()
            remote_control = 7
            lock.release()
        elif button == 'KEY_NUMERIC_8':
            lock.acquire()
            remote_control = 8
            lock.release()        
        elif button == 'KEY_NUMERIC_9':
            remote_control = 9
        else:
            remote_control = remote_control
            pass


if __name__ == '__main__':
    try:
        task_one = threading.Thread(target=follow_task, args=())
        task_two = threading.Thread(target=control_task, args=())
        task_one.start()
        task_two.start()
        task_one.join()
        task_two.join()

    except KeyboardInterrupt:
        print('ERROR')

    finally:
        GPIO.cleanup()
