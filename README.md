# Vision Mouse

A simple app that reads gestures and performs certain actions. 

## What it can do:
- Switch desktops with the Windows key + the arrow key. 3-finger scrolling.
- Scroll up and down by simply pressing the arrow keys (you can scroll through TikTok). Pinky up and down.
- Move the cursor and click. Move the index finger, click, and then lift the index and middle fingers.
- Your own commands that run as if in a terminal, with configuration. In the config section, you enter an array of the form [1,1,1,1], where each number represents a finger from the index finger to the little finger, and 1 is raised, 0 is lowered. Next, you specify the command ["first word", "second word"] in this format. Here's the final example: comands = [([1,0,0,1],["brave"])], you can add more separated by commas. 

## Stack
I used Python with OpenCV, MediaPipe, ydotool (Wayland input control) because it is a good language for working with machine vision and there are many libraries available.

## Installation
### 1. Clone the repository

```bash
git clone https://github.com/KotaNch/Vision-Mouse.git
```
### 2. Installation dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### 3. Installation ydotool (for Arch / EndeavourOS)
```bash
sudo pacman -S ydotool
systemctl --user enable --now ydotoold
```

### 4. Start
``` bash
python main.py
```

P.S.
I want to add new features in future, if there are ideas write it...   