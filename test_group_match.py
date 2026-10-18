import sys
from detect_faces import detect_faces, crop_face
from recognition import embedding_from_image
from matching import shortlist_from_embedding
from setup_db import get_name

img, boxes = detect_faces(sys.argv[1])
for i, box in enumerate(boxes, start=1):
    emb = embedding_from_image(crop_face(img, box))
    top = shortlist_from_embedding(emb, k=3)
    line = ", ".join(f"{get_name(m)} {d:.2f}" for m, d in top)
    print(f"face {i}: {line}")