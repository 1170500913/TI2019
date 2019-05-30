# -*- coding: UTF-8 -*-
import os
from PIL import Image
#import pytesseract
import time  # RPi time Lib
import RPi.GPIO as GPIO  # RPi GPIO Lib
#from ir_lib import *
#from SunFounder_PCA9685 import Servo
import threading
#import urllib, urllib2, base64, sys
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

    def get_unload_pos(self, sensors=[0] * 5, flag_cnt=0):
        if sensors[4] == 1 and sensors[2] == 1:  # m and r2 is black at the same time
            self.now_state = 0
        else:
            self.now_state = 1
        if self.now_state == 0 and self.last_state == 1:
            flag_cnt += 1
        self.last_state = self.now_state
        return flag_cnt

    def line_patrol_forward(self, sensors=0, flag=0, turn_flag=0):
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

    def line_patrol_back(self, sensors=0, flag=0, turn_flag=0):
        if flag == 1:
            if sensors == '010':
                self.slip_cnt = 0
                self.back(Rhigspeed, Lhigspeed) #(右侧电机，左侧电机)
            elif sensors == '100':
                self.slip_cnt = 0
                self.back(speedx,minspeed) #左转
                
            elif sensors == '110':
                #self.back(Rhigspeed,HMidspeed) #左转
                self.slip_cnt += 20
                speed = speed = Rhigspeed - self.slip_cnt/10
                if speed < HMidspeed:
                    self.slip_cnt = 0
                    speed = HMidspeed
                self.back(Rhigspeed,speed)
                
            elif sensors == '001':
                self.slip_cnt = 0
                self.back(minspeed,speedx) #右转
            elif sensors == '011':
                #self.back(HMidspeed,Lhigspeed) #右转
                self.slip_cnt += 20
                speed = speed = Rhigspeed - self.slip_cnt/10
                if speed < HMidspeed:
                    self.slip_cnt = 0
                    speed = HMidspeed
                self.back(speed,Rhigspeed)  
                
            elif sensors == '111':
                self.slip_cnt = 0
                self.back(Rhigspeed,Lhigspeed) 
            elif sensors == '000':
                if turn_flag == 1:
                    self.left(Lhigspeed)
                else:
                    self.right(Rhigspeed)
            else:
                self.stop()
        else:
            if sensors == '010':
                self.back(Rlowspeed, Llowspeed)
            elif sensors == '100':
                self.back(speedx,0)
            elif sensors == '110': #turn_left
                self.back(Rlowspeed,LMidspeed)            
            elif sensors == '001':
                self.back(0,speedx)
            elif sensors == '011': #turn_right
                self.back(LMidspeed,Llowspeed)           
            elif sensors == '111':
                self.back(Rlowspeed,Llowspeed)
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


if __name__ == '__main__':
    try:
        car = Car()
        while (True):
            sensors = car.read_sensors()
            mid_three_sensors =  str(sensors[1]) + str(sensors[2]) + str(sensors[3])
            car.line_patrol(mid_three_sensors) 
    except KeyboardInterrupt:
        print('ERROR')

    finally:
        GPIO.cleanup()
