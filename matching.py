import numpy as np
from enrollment import load_embeddings
from recognition import get_embedding

def identify(photo_path, threshold=None):
    gallery = load_embeddings()
    if not gallery:
        return None, None

    query = get_embedding(photo_path)
    distances = {member_id: float(np.linalg.norm(query - emb)) for member_id, emb in gallery.items()}

    best_id = min(distances, key=distances.get)
    best_distance = distances[best_id]

    if threshold is not None and best_distance > threshold:
        return None, best_distance
    return best_id, best_distance
def shortlist_from_embedding(query, k=3):
    gallery = load_embeddings()
    if not gallery:
        return []

    scored = []
    for member_id, emb in gallery.items():
        similarity = np.dot(query, emb) / (np.linalg.norm(query) * np.linalg.norm(emb))
        scored.append((member_id, float(1 - similarity)))

    scored.sort(key=lambda pair: pair[1])
    return scored[:k]


def shortlist(photo_path, k=3):
    return shortlist_from_embedding(get_embedding(photo_path), k)
    query = get_embedding(photo_path)
    scored = []
    for member_id, emb in gallery.items():
        similarity = np.dot(query, emb) / (np.linalg.norm(query) * np.linalg.norm(emb))
        scored.append((member_id, float(1 - similarity)))

    scored.sort(key=lambda pair: pair[1])
    return scored[:k]