import sys
from pathlib import Path
import cv2
from detect_faces import detect_faces_yunet

score = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
img, boxes = detect_faces_yunet(sys.argv[1], score)
marked = img.copy()
for i, (x, y, w, h) in enumerate(boxes, start=1):
    cv2.rectangle(marked, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(marked, str(i), (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
Path("detected_faces").mkdir(exist_ok=True)
cv2.imwrite("detected_faces/marked_yunet.jpg", marked)
print("faces found:", len(boxes))
for i, box in enumerate(boxes, start=1):
    print(i, box)