import sqlite3
from pathlib import Path
import numpy as np
from detect_faces import detect_single_face, crop_face
from recognition import get_embedding, embedding_from_image

Path("detected_faces").mkdir(exist_ok=True)


def save_embedding(member_id, embedding, photo_path):
    conn = sqlite3.connect("church_register.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE members SET embedding = ?, photo_path = ? WHERE id = ?",
        (embedding.astype(np.float32).tobytes(), photo_path, member_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"No member with id {member_id}")
    conn.commit()
    conn.close()


def enroll_member(member_id, photo_path):
    save_embedding(member_id, get_embedding(photo_path), photo_path)


def enroll_member_from_face(member_id, photo_path):
    img, boxes = detect_single_face(photo_path)
    if not boxes:
        raise ValueError(f"No face found in {photo_path}")
    if len(boxes) > 1:
        print(f"Warning: {len(boxes)} faces in {photo_path}, using the largest")
    box = max(boxes, key=lambda b: b[2] * b[3])
    face = crop_face(img, box)
    face.save(f"detected_faces/enrolled_{member_id}.jpg")
    save_embedding(member_id, embedding_from_image(face), photo_path)


def load_embeddings():
    conn = sqlite3.connect("church_register.db")
    rows = conn.execute(
        "SELECT id, embedding FROM members WHERE embedding IS NOT NULL AND status = 'active'"
    ).fetchall()
    conn.close()
    return {member_id: np.frombuffer(blob, dtype=np.float32) for member_id, blob in rows}