import numpy as np
from recognition import get_embedding
from enrollment import enroll_member, load_embeddings

enroll_member(1, "test_photos/Love_1.jpg")

stored = load_embeddings()
print("Enrolled ids:", list(stored.keys()))
print("Shape and type:", stored[1].shape, stored[1].dtype)

fresh = get_embedding("test_photos/Love_1.jpg")
print("Round trip matches:", np.allclose(stored[1], fresh))