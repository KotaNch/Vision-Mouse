import cv2
import os
import sys
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import subprocess

import datetime
import asyncio
import time

import json
import threading
from pathlib import Path
from flask import Flask, jsonify,request,send_from_directory

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

#----------=====---------
#          Paths
#----------=====--------
CONFIG_PATH = Path("config.json")
STATIC_DIR = Path("web")

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/web")

  
   
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

last_commnad_time = 0.0
last_move = 0


#--------------------------------------
#           WEB FUNCTIONS
#--------------------------------------
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "screen_size": [1920, 1080],
        "mouse_smooth": 0.2,
        "deadzone": 5,
        "scroll_threshold": 20,
        "scroll_delay": 0.5,
        "swipe_threshold": 30,
        "gesture_delay": 1.5,
        "commands": []
    }

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False, indent=2)


config = load_config()

status = {
    "running": True,
    "last_gesture": None,
    "last_action": None,
    "fps": 0
}
 
@app.get("/")
def index():
    return send_from_directory(STATIC_DIR,"index.html")
   

@app.get("/api/config")
def api_get_config():
    return jsonify(config)

@app.post("/api/config")
def api_set_config():
    global config
    data = request.get_json(force=True)
    config.update(data)
    save_config(config)
    return jsonify({"ok":True,"config":config})
         
 
@app.get("/api/status")
def api_status():
    return jsonify(status)


def run_web():
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

  
#--------------------------------------
#   FUNCTIONS WITH MV AND YDOTOOL... AND PYAUTOGUI
#--------------------------------------


def distanse(x1,y1,x2,y2) -> float:
    return ((x2-x1)**2 +(y2-y1)**2)**0.5

async def run_process(command):
    global last_commnad_time
    gesture_delay = config.get("gesture_delay",1.5)
    if time.time() -last_commnad_time < gesture_delay:
        return
    process = await asyncio.create_subprocess_exec(*command)
    await process.wait()
    last_commnad_time = time.time()
    status["last_action"] = " ".join(command)
  
def mouse_move(x,y):
    global last_move
    if time.time() - last_move < 0.01:
        return
    last_move = time.time()
    if IS_WINDOWS:
        pyautogui.moveTo(int(x),int(y))
    else:
        subprocess.run(["ydotool", "mousemove", "--absolute", str(int(x)), str(int(y))])

    
    

        
scroll_active = False
scroll_start = None
scroll_last = 0
scroll_delay = 0.5
scroll_threshold = 20


def key_up():
    if IS_WINDOWS:
        pyautogui.press("up")
    else:
        subprocess.run(["ydotool", "key", "103:1", "103:0"])

def key_down():
    if IS_WINDOWS:
        pyautogui.press("down")
    else:
        subprocess.run(["ydotool", "key", "108:1", "108:0"])

         
def click():   
    global last_move
    if time.time() - last_move < 0.5:
        return
    if IS_WINDOWS:
        pyautogui.click()
    else:    
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
    if IS_WINDOWS:
            
        if dir == 'left':
            pyautogui.hotkey("ctrl","win","left")
        if dir == 'right':
            pyautogui.hotkey("ctrl","win","right")
        if dir == 'up':
            pyautogui.hotkey("win","tab")
        if dir == 'down':
            pyautogui.hotkey("win","d")
    else:
        if dir == 'left':
            subprocess.run(["ydotool", "key", "125:1", "105:1", "105:0", "125:0"])
        
        if dir == 'right':
            subprocess.run(["ydotool", "key", "125:1", "106:1", "106:0", "125:0"])

        if dir == 'up':
            subprocess.run(["ydotool", "key", "125:1", "103:1", "103:0", "125:0"])
        
        if dir == 'down':
            subprocess.run(["ydotool", "key", "125:1", "108:1", "108:0", "125:0"])


prev_x, prev_y = 0,0

def smooth(x, y):
    global prev_x, prev_y
    cof = config.get("mouse_smooth", 0.2)
    prev_x = prev_x * (1 - cof) + x * cof
    prev_y = prev_y * (1 - cof) + y * cof
    return prev_x, prev_y

last_mouse_x, last_mouse_y = 0,0 


#--------------------------------------------------
#               MAIN FINCTION
#               !!!!!!!!!!!!!
#==============================================
def apply_deadzone(x,y,last_x,last_y,threshold=5):
    threshold = config.get("deadzone",5)
    if abs(x-last_x) < threshold and abs(y-last_y) < threshold:
        return last_x, last_y
    return x,y
async def main():
    global scroll_active,scroll_last,scroll_start
    global gesture_active,gesture_fired,gesture_start
    global last_mouse_x, last_mouse_y

    frame_count = 0
    fps_timer = time.time()


    while camera.isOpened():
        success, img = camera.read()
        if not success:continue

        frame_count+=1

        elapsed = time.time() - fps_timer
        if elapsed >= 1.0:
            status["fps"] = round(frame_count/elapsed,1)
            frame_count = 0
            fps_timer = time.time()
    
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        detection_results = detector.detect(mp_img)  
        swipe_threshold = config.get("swipe_threshold",30)
        scroll_threshold = config.get("scroll_threshold",20)
        scroll_delay = config.get("scroll_delay",0.5)

        

        if detection_results.hand_landmarks:
            
            for hand_landmarks in detection_results.hand_landmarks:  
                
                for id, landmark in enumerate(hand_landmarks):
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
                            sx,sy = smooth(pos_x,pos_y)
                            sx,sy = apply_deadzone(sx,sy, last_mouse_x, last_mouse_y)
                            last_mouse_x,last_mouse_y = sx,sy
                            mouse_move(sx,sy)
                        if finger[1] == 1 and finger[2] ==1 and finger[3] == 0 and finger[4] == 0:
                           click() 

            
                for i in range(4,21,4):
                    shortDistance = distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1]) +  (distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1])/2.5)
                    # print('short: ',shortDistance,'full dist: ',distan se(p[0][0],p[0][1],p[i][0],p[i][1]))
                    finger[(i-4)//4] = 1 if distanse(p[0][0],p[0][1],p[i][0],p[i][1]) > shortDistance else 0
                    # print('i: ',(i-4)//4 )
                # print(finger)
                     
                status["last_gesture"] = finger[1:]
                for item in config.get("commands", []):
                    fingers = item.get("fingers", [])
                    command = item.get("command", [])

                    if len(fingers) != 4 or not command:
                        continue
 
                    if (
                        finger[1] == fingers[0] and
                        finger[2] == fingers[1] and
                        finger[3] == fingers[2] and
                        finger[4] == fingers[3]
                        
                    ):      
                        await run_process(command)         
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
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())


