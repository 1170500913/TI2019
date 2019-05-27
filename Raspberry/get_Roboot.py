# 取货机器人
import RPi.GPIO as GPIO
import vehicle
import time
import tracking
import ultra
import camera
import arm
from channel import *


WAIT = -1
STOP = 0
UP = 1
DOWN = 2



if __name__ == '__main__':

    # 初始化引脚
    init_channel()

    # 初始状态
    move_stat = WAIT   # 运动状态
    # hold = False  # 是否拿着物体
    ultra_sense = False  # 是否启动超声波寻找物体
    camera_ident = False # 是否启动摄像头识别物体


    step_time = 0  # 摄像头检测失败时，前进的步长
    count = 0      # 遇到的黑横线数目
    edge_flag = False  # 黑横线计数的辅助标志

    region = -1    # 区域, 永远比count少1

    target_region = -1 # 收到的目标区域
    cargo = -1   # 待取的物品，（int 编号）
    

    while (True): # DFA

        # 公共部分：
            
        
        if (move_stat == WAIT):  # 等待
            
            vehicle.stop()
            # 输入区域、物品编号
            region = input('region: ')
            cargo = input('cargo: ')
            
            move_stat = UP

        if (move_stat == STOP):
            vehicle.stop()
            
            
        if (move_stat == UP):    # 沿黑线前进

            # 获取红外信号
            L1_sign = GPIO.input(L1)
            L0_sign = GPIO.input(L0)
            R0_sign = GPIO.input(R0)
            R1_sign = GPIO.input(r1)

            # 根据内侧红外调整姿态
            tracking.track_up(L0_sign, R0_sign)    


            # 更新黑横线计数器，更新区域
            # 机制： “没黑横线” --> “有黑横线” 的过渡区时，count++
            if (L1_sign == GPIO.HIGH and R1_sign == GPIO.HIGH and edge_flag):  
                count += 1
                region += 1
                print(count)
                edge_flag = False  
            elif (L1_sign == GPIO.LOW and R1_sign == GPIO.LOW):
                edge_flag = True


            # 位于目标区域内
            if (region == target_region):             
                time.sleep(step_time)  # 经过一段步长，再进行检测
                                        # 只有当检测失败的时候， step_time != 0
                ultra_sense = True
            

            # 越过了目标区域 --> 没找到物体
            if (region > target_region):
                print('error: can\'t find the target cargo in the specific region!\n')
                move_stat = DOWN   # 回去
                ultra_sense = False  # 停止超声波检测



            # 到头了，返回
            if (count == 5):   
                move_stat = DOWN


        
        if (move_stat == DOWN):  # 返回
            L1_sign = GPIO.input(L1)
            L0_sign = GPIO.input(L0)
            R0_sign = GPIO.input(R0)
            R1_sign = GPIO.input(r1)

            # 根据内侧红外调整姿态
            tracking.track_down(L0_sign, R0_sign)

            # 更新黑横线计数器，更新区域
            if (L1_sign == GPIO.HIGH and R1_sign == GPIO.HIGH and edge_flag):  
                count -= 1
                region -= 1
                print(count)
                edge_flag = False  
            elif (L1_sign == GPIO.LOW and R1_sign == GPIO.LOW):
                edge_flag = True

            if (count == 0):
                move_stat = WAIT()


        if (ultra_sense): # 超声波检测

            if (ultra.isLowerThan()): # 探测到物体
                move_stat = STOP  # 停下
                camera_ident = True # 开启摄像头识别

            else:
                step_time = 0


        if (camera_ident):  # 摄像头识别
            res = camera.identify()
            if (res != -1 and res == cargo):  # 识别成功，且是目标物体
                arm.catch()  # 抓取物品
                ultra_sense = False 
                camera_ident = False 
                move_stat = DOWN  # 返回

            else:  # 识别失败，或者不是目标物体
                camera_ident = False

                # 前进一段步长，再检测
                step_time = 1   # 步长
                move_stat = UP




        
        

