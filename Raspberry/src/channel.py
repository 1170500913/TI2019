# 引脚定义、引脚初始化、引脚释放

import RPi.GPIO as GPIO

# 电动机引脚
IN1 = 11
IN2 = 12
IN3 = 13
IN4 = 15


# 红外线传感器引脚
L1 = 0   # 左边外侧
L0 = 1   # 左边内侧
R0 = 2   # 右边内侧
R1 = 3   # 右边外侧

# 超声波传感器引脚
TRIG = 4
ECHO = 5


# 引脚初始化
def init_channel():
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)

    GPIO.setup(L0, GPIO.IN)
    GPIO.setup(L1, GPIO.IN)
    GPIO.setup(R0, GPIO.IN)
    GPIO.setup(R1, GPIO.IN)

    GPIO.setup(TRIG, GPIO.out)
    GPIO.setup(ECHO, GPIO.IN)
