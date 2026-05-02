import cv2
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import subprocess

import datetime
import asyncio
import time
#------------------------------------
#       CONFIG COMANDS
#-----------------------------------
comands = [([1,0,0,1],["brave"])]

  
screen_size = (1920, 1080)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.3,
    min_hand_presence_confidence=0.3,
    min_tracking_confidence=0.3
)
detector = vision.HandLandmarker.create_from_options(options)

camera = cv2.VideoCapture(0)


gesture_active = False
gesture_start = None
gesture_fired = False
swipe_threshold = 30


p = [[0,0] for i in range(21)]           
finger = [0 for i in range(5)] 

max_diff = 1
delay = datetime.datetime.now().second


last_move = 0

def distanse(x1,y1,x2,y2) -> float:
    return ((x2-x1)**2 +(y2-y1)**2)**0.5

async def run_process(command):
    global last_move
    if time.time() - last_move < 1.5:
        return
    process = await asyncio.create_subprocess_exec(*command)
    last_move = time.time()


  
def mouse_move(x,y):
    global last_move
    if time.time() - last_move < 0.01:
        return
    last_move = time.time()
    subprocess.run(["ydotool", "mousemove", "--absolute", str(int(x)), str(int(y))])


scroll_active = False
scroll_start = None
scroll_last = 0
scroll_delay = 0.5
scroll_threshold = 20


def key_up():
    subprocess.run(["ydotool", "key", "103:1", "103:0"])

def key_down():
    subprocess.run(["ydotool", "key", "108:1", "108:0"])


def click():
    global last_move
    if time.time() - last_move < 0.5:
        return
    subprocess.run(["ydotool", "click", "0xC0"])
    last_move = time.time()

def hand_cneter(p):
    ind = [0,5,9,13,17]
    cx = sum(p[i][0] for i in ind)/5
    cy = sum(p[i][1] for i in ind)/5
    return cx, cy

def swipe_direction(start,current):
    dx = current[0] - start[0] 
    dy = current[1] - start[1]

    if abs(dx) > abs(dy):
        return "left" if dx < 0 else "right"
    else:
        return "up" if dy < 0 else "down"
def swipes(dir):
    if dir == 'left':
        subprocess.run(["ydotool", "key", "125:1", "105:1", "105:0", "125:0"])
      
    if dir == 'right':
        subprocess.run(["ydotool", "key", "125:1", "106:1", "106:0", "125:0"])

    if dir == 'up':
        subprocess.run(["ydotool", "key", "125:1", "103:1", "103:0", "125:0"])
      
    if dir == 'down':
        subprocess.run(["ydotool", "key", "125:1", "108:1", "108:0", "125:0"])


prev_x, prev_y = 0,0
cof = 0.2
def smooth(x, y):
    global prev_x, prev_y
    prev_x = prev_x * (1 - cof) + x * cof
    prev_y = prev_y * (1 - cof) + y * cof
    return prev_x, prev_y

def apply_deadzone(x,y,last_x,last_y,threshold=5):
    if abs(x-last_x) < threshold and abs(y-last_y) < threshold:
        return last_x, last_y
    return x,y

while camera.isOpened():
    success, img = camera.read()
    if not success:continue
  
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    detection_results = detector.detect(mp_img)  

    if detection_results.hand_landmarks:
        
        for hand_landmarks in detection_results.hand_landmarks:  
            id = 0 
            for landmark in hand_landmarks:
                x,y = int(landmark.x * img.shape[1], ), int(landmark.y * img.shape[0])
                cv2.circle(img, (x,y), 5, (0,255,0), -1)
                

                # name = landmark.name
              
                p[id][0],p[id][1] = x,y
                if id == 8:
                   
                    cv2.circle(img, (x, y), 15, (0, 100, 255), cv2.FILLED)
                if id == 12:
                    cv2.circle(img, (x, y), 15, (0, 0, 255), cv2.FILLED)
                
                 
                # print(x,y)
                if id == 8:
                    pos_x =  screen_size[0]/2- x / img.shape[1] * screen_size[0]/2
                    pos_y = y /  img.shape[0] * screen_size[1]/2
                    # print(pos_x,pos_y)``
                    if finger[1] == 1 and finger[2] ==0 and finger[3] == 0 and finger[4] == 0:
                        x,y = smooth(pos_x,pos_y)
                        x,y = apply_deadzone(x,y, prev_x, prev_y)
                        mouse_move(x,y)
                    if finger[1] == 1 and finger[2] ==1 and finger[3] == 0 and finger[4] == 0:
                        click() 

          
 
                id +=1
            for i in range(4,21,4):
                shortDistance = distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1]) +  (distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1])/2.5)
                # print('short: ',shortDistance,'full dist: ',distan se(p[0][0],p[0][1],p[i][0],p[i][1]))
                finger[(i-4)//4] = 1 if distanse(p[0][0],p[0][1],p[i][0],p[i][1]) > shortDistance else 0
                # print('i: ',(i-4)//4 )
            # print(finger)
            
            now = datetime.datetime.now().second
            for fingers, comand in comands:
                # print('fingers: ',fingers,'comand: ',comand, 'finger: ', finger )
                if finger[1] == fingers[0] and finger[2] == fingers[1] and finger[3] == fingers[2] and finger[4] == fingers[3] and abs(now-delay) > max_diff:
                    if len(comand) == 1:
                        asyncio.run(run_process(comand[0]))
                    else:asyncio.run(run_process(comand))
            
            cx, cy = hand_cneter(p)

            if finger[1] == 1 and finger[2] == 1 and finger[3] == 1 and finger[4] == 0:
                if not gesture_active:
                    gesture_active = True
                    gesture_start = (cx, cy)
                    gesture_fired = False
                elif not gesture_fired:
                    if abs(cx - gesture_start[0]) > swipe_threshold or abs(cy - gesture_start[1]) > swipe_threshold:
                        direction = swipe_direction(gesture_start, (cx, cy))
                        swipes(direction)
                        gesture_fired = True
            else:
                gesture_active = False
                gesture_fired = False
                gesture_start = None     

            if finger[1] == 0 and finger[2] == 0 and finger[3] == 0 and finger[4] == 1: 
                if not scroll_active:
                    scroll_active = True
                    scroll_start = cy
                else:
                    dy = cy - scroll_start

                    if abs(dy) > scroll_threshold and time.time() - scroll_last > scroll_delay:
                        if dy > 0:
                            key_down()
                        else:key_up()

                        scroll_start = cy
                        scroll_last = time.time()
            else:
                scroll_active = False
                scroll_start = None
                          
                          

            # if finger[1] == 1 and finger[2] ==0 and finger[3] == 0 and finger[4] == 1 and abs(now-delay) > max_diff:
            #         asyncio.run(run_process("steam"))
            #         delay = datetime.datetime.now().second
 
            # if finger[1] == 0 and finger[2] == 1 and finger[3] == 0 and finger[4] == 0 and abs(now-delay) > max_diff:
            #     asyncio.run(run_process("brave"))
            #     delay = datetime.datetime.now().second
            # if finger[1] == 0 and finger[2] == 0 and finger[3] == 0 and finger[4] == 0 and abs(now-delay) > max_diff:
            #     asyncio.run(run_process("reboot"))
            #     delay = datetime.datetime.now().second
            
        
            
        

 
    cv2.imshow('Hands', img)
    if cv2.waitKey(5) & 0xFF == 27:
        break
camera.release()
cv2.destroyAllWindows() 


