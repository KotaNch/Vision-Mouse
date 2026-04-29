import cv2
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import subprocess
from shutil import which


screen_size = (1920, 1080)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

camera = cv2.VideoCapture(0)

p = [[0,0] for i in range(21)]           
finger = [0 for i in range(5)]   


def distanse(x1,y1,x2,y2) -> float:
    return ((x2-x1)**2 +(y2-y1)**2)**0.5

def move_mouse(x,y):

    subprocess.run(["ydotool","mousemove", "--absolute", str(int(x)), str(int(y))])
def click_left():
    subprocess.run(["ydotool", "click", "0xC0"])

if which("ydotool") is None:
    print("ydotool is not installed")
    exit(1)
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
                

                name = landmark.name
             
                p[id][0],p[id][1] = x,y
                if id == 8:
                  
                    cv2.circle(img, (x, y), 15, (0, 100, 255), cv2.FILLED)
                if id == 12:
                    cv2.circle(img, (x, y), 15, (0, 0, 255), cv2.FILLED)
                
              
                print(x,y)

                id +=1
            for i in range(4,21,4):
                shortDistance = distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1]) +  (distanse(p[0][0],p[0][1], p[i-3][0],p[i-3][1])/2.5)
                print('short: ',shortDistance,'full dist: ',distanse(p[0][0],p[0][1],p[i][0],p[i][1]))
                finger[(i-4)//4] = 1 if distanse(p[0][0],p[0][1],p[i][0],p[i][1]) > shortDistance else 0
                print('i: ',(i-4)//4 )
            # print(finger)
            
        


    cv2.imshow('Hands', img)
    if cv2.waitKey(5) & 0xFF == 27:
        break
camera.release()
cv2.destroyAllWindows() 


