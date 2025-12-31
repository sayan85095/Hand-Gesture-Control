from flask import Flask, render_template, Response
import cv2
from HandTrackingModule import HandDetector
import atexit  # For cleanup

app = Flask(__name__)

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1, detectionCon=0.85)

def generate_frames():
    while True:
        success, img = cap.read()
        if not success:
            break

        img = detector.find_hands(img)
        lmList = detector.find_position(img, draw=False)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Cleanup camera on exit
atexit.register(lambda: cap.release())

if __name__ == "__main__":
    app.run(debug=True)