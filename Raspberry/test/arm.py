# -*- coding: utf-8 -*
import time

def catch():
    print("正在抓物体..")
    time.sleep(1)
    print("已抓到物体")

def relase():
    print("正在放物品..")
    time.sleep(1)
    print("已放置物品")

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

