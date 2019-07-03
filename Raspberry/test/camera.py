#import requests
import os
from aip import AipOcr
import time
# import cv2

#获取access_token
#def getAccessToken():
#    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=23LFphQdhMGskxj7pwUuNCGt&client_secret=NLIUSf0loXcDDwdStvB4mN52GBC8OiMM'
#
#    headers = {
#        'Content-Type': 'application/json;charset=UTF-8'
#    }
#    res = requests.get(host, headers).json()
#    accessToken = res['access_token']
#    # print(res['access_token'])
#    return accessToken


#读取图片
def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

##########################################################
##########下面为调用sdk识别数字#############################
#输入：图片路径
#输出：识别出的数字，若识别失败，返回-1
def getNumber(filepath):
    APP_ID = '16285069'
    API_KEY = '23LFphQdhMGskxj7pwUuNCGt'
    SECRET_KEY = 'NLIUSf0loXcDDwdStvB4mN52GBC8OiMM'

    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    # image = get_file_content('img/2.jpg')

    image = get_file_content(filepath)
    # 调用数字识别
    message = client.numbers(image)
   # print(message)
    if (message.get('words_result_num') == 0):
        return -1
    for text in message.get('words_result'):
        # print(text.get('words') + '\n')
        return int(text.get('words'))

def identify():
    # cap=cv2.VideoCapture(0)
    # i=0
    # # 当前帧
    # frame_index = 0

    # while(1):
    #     frame_index = frame_index + 1
    #     ret ,frame = cap.read()
    #    # k=cv2.waitKey(1)
    #     if frame_index == 60:
    #         break
    #     elif frame_index == 30:
    #         cv2.imwrite('test.jpg',frame)
    #         i+=1
    #     cv2.imshow("capture", frame)
    # cap.release()
    # cv2.destroyAllWindows()
    os.system("fswebcam --no-banner -r 640x480 test.jpg")
#    time.sleep(1)
    return getNumber('test.jpg')

if __name__ == "__main__":
    print(identify())

