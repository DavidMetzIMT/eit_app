import cv2

frameWeight = 640
frameHeight = 480
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, frameWeight)
cap.set(4, frameHeight)
cap.set(10, 150)

while cap.isOpened():
    success, img = cap.read()
    if success:
        cv2.imshow("Result", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
