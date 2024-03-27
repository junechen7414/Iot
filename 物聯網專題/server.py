### 前置作業 ###
### 關閉防火牆以確保連線 ###
### pip install pyautogui Pillow ###
import socket
import pyautogui
import time

HOST = '0.0.0.0'
PORT = 1234

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            keyboard_command = data.decode()
            print('Received:', keyboard_command)
            pyautogui.press(keyboard_command)
