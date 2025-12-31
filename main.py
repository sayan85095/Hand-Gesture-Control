import cv2
import math
import numpy as np
import pyautogui
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from HandTrackingModule import HandDetector

# ================= CAMERA =================
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Camera not opened")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("Hand Gesture Control", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Hand Gesture Control", 1280, 720)

detector = HandDetector(maxHands=1)

# ================= AUDIO =================
try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    minVol, maxVol = volume.GetVolumeRange()[:2]
    audio_ok = True
except Exception as e:
    print(f"⚠ Audio control not available: {e}")
    audio_ok = False

# ================= SETTINGS =================
tipIds = [4, 8, 12, 16, 20]
pyautogui.FAILSAFE = False
last_action_time = 0
action_delay = 0.3

# ================= CURSOR SMOOTHING =================
prevX, prevY = 0, 0
smoothening = 7  # higher value = smoother but slower

# ================= LOOP =================
while True:
    success, img = cap.read()
    if not success:
        print("❌ Failed to capture image")
        break

    img = detector.find_hands(img)
    lmList = detector.find_position(img, draw=False)

    if len(lmList) >= 21:
        fingers = []

        # Thumb
        fingers.append(1 if lmList[4][1] > lmList[3][1] else 0)

        # Other fingers
        for i in range(1, 5):
            fingers.append(1 if lmList[tipIds[i]][2] < lmList[tipIds[i] - 2][2] else 0)

        current_time = time.time()
        screenW, screenH = pyautogui.size()

        # 👉 Cursor move (Index finger)
        if fingers == [0, 1, 0, 0, 0]:
            x, y = lmList[8][1], lmList[8][2]
            # Convert coordinates
            X = np.interp(x, [0, 640], [0, screenW])
            Y = np.interp(y, [0, 480], [0, screenH])
            # Smooth cursor
            X = prevX + (X - prevX) / smoothening
            Y = prevY + (Y - prevY) / smoothening
            pyautogui.moveTo(X, Y)
            prevX, prevY = X, Y

        # 👉 Left click
        elif fingers == [1, 1, 0, 0, 0]:
            if current_time - last_action_time > action_delay:
                pyautogui.click()
                last_action_time = current_time

        # 👉 Scroll
        elif fingers == [0, 1, 1, 0, 0]:
            pyautogui.scroll(300)

        # 👉 Volume control
        elif audio_ok and fingers == [1, 0, 0, 0, 1]:
            length = math.hypot(lmList[4][1] - lmList[20][1],
                                lmList[4][2] - lmList[20][2])
            vol = np.interp(length, [50, 200], [minVol, maxVol])
            volume.SetMasterVolumeLevel(vol, None)

    cv2.imshow("Hand Gesture Control", img)

    # ESC to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# ================= CLEANUP =================
cap.release()
cv2.destroyAllWindows()
