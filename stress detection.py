from keras.preprocessing.image import img_to_array
import imutils
import cv2
from keras.models import load_model
import numpy as np
import time
import argparse
import pygame

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file',
    help='Path to video file (if not using camera)')
parser.add_argument('-c', '--color', type=str, default='gray',
    help='Color space: "gray" (default), "rgb", or "lab"')
parser.add_argument('-b', '--bins', type=int, default=16,
    help='Number of bins per channel (default 16)')
parser.add_argument('-w', '--width', type=int, default=0,
    help='Resize video to specified width in pixels (maintains aspect)')
args = vars(parser.parse_args())

# parameters for loading data and images
detection_model_path = 'haarcascade_files/haarcascade_frontalface_default.xml'
emotion_model_path = 'models/_mini_XCEPTION.102-0.66.hdf5'

# hyper-parameters for bounding boxes shape
# loading models
face_detection = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
emotion_classifier = load_model(emotion_model_path, compile=False)
EMOTIONS = ["stress", "disgust", "scared", "happy", "sad", "surprised", "neutral"]

# Initialize pygame mixer
pygame.mixer.init()

# starting video streaming
cv2.namedWindow('my_face')
camera = cv2.VideoCapture(0)
time.sleep(2)

while True:
    frame = camera.read()[1]
    frame = imutils.resize(frame, width=300)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detection.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30), flags=cv2.CASCADE_SCALE_IMAGE)
    
    canvas = np.zeros((600, 700, 3), dtype="uint8")
    frameClone = frame.copy()
    
    if len(faces) > 0:
        faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
        (fX, fY, fW, fH) = faces
        # Extract the ROI of the face from the grayscale image, resize it to 64x64 pixels
        roi = gray[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (64, 64))
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        
        preds = emotion_classifier.predict(roi)[0]
        emotion_probability = np.max(preds)
        label = EMOTIONS[preds.argmax()]

        for (i, (emotion, prob)) in enumerate(zip(EMOTIONS, preds)):
            text = "{}: {:.2f}%".format(emotion, prob * 100)
            w = int(prob * 300)
            cv2.rectangle(canvas, (7, (i * 35) + 5), (w, (i * 35) + 35), (0, 255, 0), -1)
            cv2.putText(canvas, text, (10, (i * 35) + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
        
        cv2.putText(frameClone, label, (fX, fY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
        cv2.rectangle(frameClone, (fX, fY), (fX + fW, fY + fH), (0, 255, 0), 2)

        if label == "stress":
            print("You are in stress")
            cv2.putText(frameClone, "Please listen to music", (fX, fY - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
            pygame.mixer.music.load('./nicee.mp3')
            pygame.mixer.music.play()

    cv2.imshow('Stress Detection Output', frameClone)
    cv2.imshow("Probabilities", canvas)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
