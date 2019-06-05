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

# 红外线的接口
msensor = 24
rsensor1 = 27
lsensor1 = 22
rsensor2 = 25
lsensor2 = 10

# 速度
minspeed = 30
lowspeed = 35
midspeed = 68
highspeed = 70

minspeed = minspeed - 10
lowspeed = lowspeed - 10
midspeed = midspeed - 10
highspeed = highspeed - 10



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

    def forward(self, duty_b=50, duty_a=50):  # right left
        # print("forward")
        GPIO.output(self.I1, True)
        GPIO.output(self.I3, True)
        if duty_a != self.last_pwmA:
            self.my_pwmA.ChangeDutyCycle(duty_a)
            self.last_pwmA = duty_a
        if duty_b != self.last_pwmB:
            self.my_pwmB.ChangeDutyCycle(duty_b)
            self.last_pwmB = duty_b

    def back(self, duty_b=50, duty_a=50):  # right left
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

    # sensors: 中间三个传感器

    def line_patrol_forward(self, sensors=0, flag=0, turn_flag=0):
        if flag == 1:
            if sensors == '010':
                self.slip_cnt = 0
                self.forward(highspeed, highspeed)  # (右侧电机，左侧电机)
            elif sensors == '100':
                self.slip_cnt = 0
                self.forward(highspeed, minspeed)  # 左转

            elif sensors == '110':
                self.slip_cnt += 30
                speed = highspeed - self.slip_cnt/10
                if speed < lowspeed:
                    self.slip_cnt = 0
                    speed = lowspeed
                self.forward(highspeed, speed)

            elif sensors == '001':
                self.slip_cnt = 0
                self.forward(minspeed, highspeed)  # 右转
            elif sensors == '011':
                self.slip_cnt += 30
                speed = highspeed - self.slip_cnt/10
                if speed < lowspeed:
                    self.slip_cnt = 0
                    speed = lowspeed
                self.forward(speed, highspeed)

            elif sensors == '111':
                self.slip_cnt = 0
                self.forward(highspeed, highspeed)
            elif sensors == '000':
                if turn_flag == 1:
                    self.left(highspeed)
                else:
                    self.right(highspeed)
            else:
                self.stop()
        else:
            if sensors == '010':
                self.forward(highspeed, highspeed)
            elif sensors == '100':
                self.forward(highspeed, 0)
            elif sensors == '110':  # turn_left
                self.forward(highspeed, lowspeed)
            elif sensors == '001':
                self.forward(0, highspeed)
            elif sensors == '011':  # turn_right
                self.forward(lowspeed, highspeed)
            elif sensors == '111':
                self.forward(highspeed, highspeed)
            elif sensors == '000':
                if turn_flag == 1:
                    self.left(highspeed)
                else:
                    self.right(highspeed)
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

    def get_unload_pos(self, sensors=[0] * 5, flag_cnt=0):
        if sensors[4] == 1 and sensors[0] == 1:  # outside sensors is black at the same time
            self.now_state = 0
        else:
            self.now_state = 1
        if self.now_state == 0 and self.last_state == 1:
            flag_cnt = (flag_cnt + 1) % 5
            print("进入第" + str(flag_cnt) + "区域")
        self.last_state = self.now_state
        return flag_cnt
