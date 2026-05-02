import cv2

cap = cv2.VideoCapture("rtsp://157.245.111.63:8554/cam1")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break
    print(ret)