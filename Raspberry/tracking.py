# 沿黑线走


import vehicle
from channel import *


# 调整姿态

# 向前
def track_up(L0_sign, R0_sign):
    # 获取红外信号
    # L1_sign = GPIO.input(L1)
    # L0_sign = GPIO.input(L0)
    # R0_sign = GPIO.input(R0)
    # R1_sign = GPIO.input(r1)

    # 正好在轨迹上
    if (L0_sign == True and R0_sign == True):
        vehicle.up()

    # 左侧在轨迹上，右侧不在：
    elif (L0_sign == True and R0_sign == False):
        vehicle.turn_left()
        time.sleep(1)
        vehicle.up()
        time.sleep(1)

    # 右侧在轨迹上，左侧不在：
    elif (L0_sign == False and R0_sign == True):
        vehicle.turn_right()
        time.sleep(1)
        vehicle.up()
        time.sleep(1)

    else:
        vehicle.stop()

# 向后
def track_down(L0_sign, R0_sign):
    # 获取红外信号
    # L1_sign = GPIO.input(L1)
    # L0_sign = GPIO.input(L0)
    # R0_sign = GPIO.input(R0)
    # R1_sign = GPIO.input(r1)

    # 正好在轨迹上
    if (L0_sign == True and R0_sign == True):
        vehicle.down()

    # 左侧在轨迹上，右侧不在：
    elif (L0_sign == True and R0_sign == False):
        vehicle.turn_left()
        time.sleep(1)
        vehicle.down()
        time.sleep(1)

    # 右侧在轨迹上，左侧不在：
    elif (L0_sign == False and R0_sign == True):
        vehicle.turn_right()
        time.sleep(1)
        vehicle.down()
        time.sleep(1)

    else:
        vehicle.stop()

