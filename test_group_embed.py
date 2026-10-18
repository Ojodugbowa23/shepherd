import sys
import numpy as np
from detect_faces import detect_faces, crop_face
from setup_db import get_name

img, boxes = detect_faces(sys.argv[1])
for i, box in enumerate(boxes, start=1):
    face = crop_face(img, box)
    face.save(f"detected_faces/padded_{i}.jpg")
    emb = embedding_from_image(face)
    print(i, face.size, emb.shape, round(float(np.linalg.norm(emb)), 1))