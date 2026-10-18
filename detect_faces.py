import sys
from pathlib import Path

import cv2
from PIL import Image

YUNET = str(Path(__file__).with_name("face_detection_yunet_2023mar.onnx"))


def remove_overlaps(boxes, limit=0.5):
    kept = []
    for x, y, w, h in sorted(boxes, key=lambda b: b[2] * b[3], reverse=True):
        duplicate = False
        for kx, ky, kw, kh in kept:
            ix = max(0, min(x + w, kx + kw) - max(x, kx))
            iy = max(0, min(y + h, ky + kh) - max(y, ky))
            if ix * iy / (w * h) > limit:
                duplicate = True
        if not duplicate:
            kept.append((x, y, w, h))
    return kept


def read_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    return img


def detect_faces_yunet(image_path, score=0.7):
    img = read_image(image_path)
    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(YUNET, "", (w, h), score, 0.3, 5000)
    _, faces = detector.detect(img)
    boxes = []
    if faces is not None:
        for f in faces:
            x, y, bw, bh = (int(v) for v in f[:4])
            boxes.append((max(0, x), max(0, y), bw, bh))
    return img, remove_overlaps(boxes)


def detect_faces(image_path, score=0.7):
    return detect_faces_yunet(image_path, score)


def detect_single_face_haar(image_path):
    img = read_image(image_path)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    pad = img.shape[0] // 2
    for neighbors, size, border in [(6, 40, 0), (3, 20, 0), (3, 20, pad)]:
        if border:
            work = cv2.copyMakeBorder(
                img, border, border, border, border,
                cv2.BORDER_CONSTANT, value=(128, 128, 128),
            )
        else:
            work = img
        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        boxes = cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=neighbors, minSize=(size, size)
        )
        if len(boxes):
            shifted = [(int(x) - border, int(y) - border, int(w), int(h)) for x, y, w, h in boxes]
            return img, remove_overlaps(shifted)
    return img, []


def detect_single_face(image_path):
    img, boxes = detect_faces_yunet(image_path, 0.5)
    if boxes:
        return img, boxes
    return detect_single_face_haar(image_path)


def crop_face(img, box, margin=0.4):
    x, y, w, h = box
    side = max(w, h)
    cx, cy = x + w / 2, y + h / 2
    half = side * (1 + 2 * margin) / 2
    x1, y1 = max(0, int(cx - half)), max(0, int(cy - half))
    x2, y2 = min(img.shape[1], int(cx + half)), min(img.shape[0], int(cy + half))
    crop = img[y1:y2, x1:x2]
    return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))


if __name__ == "__main__":
    score = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
    img, boxes = detect_faces(sys.argv[1], score)
    out = Path("detected_faces")
    out.mkdir(exist_ok=True)
    marked = img.copy()
    for i, (x, y, w, h) in enumerate(boxes, start=1):
        cv2.rectangle(marked, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(marked, str(i), (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imwrite(str(out / "marked.jpg"), marked)
    print("faces found:", len(boxes))
    for i, box in enumerate(boxes, start=1):
        print(i, box)