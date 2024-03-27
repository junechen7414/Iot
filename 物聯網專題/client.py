### 前置作業 ###
### pip install mediapipe ###
### 開啟server端 ###
import cv2
import mediapipe as mp
import socket
import shutil
import os

# 參數設定
HOST = '192.168.137.1'
PORT = 1234
folder_path = '/home/pi/iot/Posture'

# 手勢定義
def findPosition(image, results, handNo=0):
    lmList = []
    if results.multi_hand_landmarks:
        myHand = results.multi_hand_landmarks[handNo]
        for id, lm in enumerate(myHand.landmark):
            h, w, c = image.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            lmList.append([id, cx, cy])
            with open(f'{folder_path}/position.log', 'a') as file:
               file.write(f"Point : {id}\n{lm}")
    return lmList

def run():
    try:
        shutil.rmtree(folder_path)
        os.makedirs(folder_path)
    except FileNotFoundError:
        os.makedirs(folder_path)

    # 參數設定
    num = 0
    state = "none"
    posture = ""
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5) as hands:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect to server
            s.connect((HOST, PORT))
            while cap.isOpened():
                num +=1
                success, image_orig = cap.read()

                # 拍攝影像預處理
                image_flip_RGB = cv2.cvtColor(cv2.flip(image_orig, 1), cv2.COLOR_BGR2RGB)
                image_flip_RGB.flags.writeable = False
                results = hands.process(image_flip_RGB)
                cv2.imwrite(f'{folder_path}/{num}.jpg', image_orig)
                image_flip_RGB.flags.writeable = True
                image_flip_BGR = cv2.cvtColor(image_flip_RGB, cv2.COLOR_RGB2BGR)
                with open(f'{folder_path}/position.log', 'a') as file:
                    file.write(f"Figure num : {num}\n")
                lmList = findPosition(image_flip_BGR, results=results)

                # 判斷照片中是否有手
                if lmList == []:
                    state = "none"
                    for point in range(0, 21):
                        lmList.append([point, 0, 0])
                else:
                    tipIds = [4, 8, 12, 16, 20]
                    fingers = []
                    for id in range(1, 5):
                        if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                            fingers.append(1)
                        if (lmList[tipIds[id]][2] > lmList[tipIds[id] - 2][2]):
                            fingers.append(0)
                    totalFingers = fingers.count(1)
                    with open(f'{folder_path}/position.log', 'a') as file:
                        file.write(f"Fingers : {totalFingers}\n")
                    if state == "none":
                        if totalFingers == 0:
                            state = "pause"
                        if totalFingers == 3:
                            state = "play"

                    # 手勢對應操作
                    if totalFingers == 4: # stop
                        print('stop')
                        with open('/home/pi/iot/Posture/position.log', 'a') as file:
                            file.write(f"Posture : stop\n\n")
                        break
                    if totalFingers == 0 and state == "play": # play
                        state = "pause"
                        posture = "space"
                        print('pause')
                    if totalFingers == 3 and state == "pause": # pause
                        state = "play"
                        posture = "space"
                        print('play')
                    if totalFingers == 1:
                        if lmList[8][1] < 280: # left
                            posture = "left"
                            print(posture)
                        if lmList[8][1] > 360: # right
                            posture = "right"
                            print(posture)
                    if totalFingers == 2:
                        if lmList[9][2] > 260: # down
                            posture = "down"
                            print(posture)
                        if lmList[9][2] < 220: # up
                            posture = "up"
                            print(posture)
                    s.sendall(posture.encode())
                    with open('/home/pi/iot/Posture/position.log', 'a') as file:
                        file.write(f"Posture : {posture}\n\n")
                # 歸零
                posture = ""
                cv2.destroyAllWindows()
    cap.release()

if __name__ == '__main__':
    run()