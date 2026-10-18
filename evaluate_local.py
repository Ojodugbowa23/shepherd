import itertools
import numpy as np
from recognition import get_embedding

people = 5
photos_each = 3

embeddings = {}
for p in range(1, people + 1):
    for k in range(1, photos_each + 1):
        embeddings[(p, k)] = get_embedding(f"test_photos/lfw_check/person{p}_{k}.jpg")

same, diff = [], []
for a, b in itertools.combinations(embeddings.keys(), 2):
    d = np.linalg.norm(embeddings[a] - embeddings[b])
    if a[0] == b[0]:
        same.append(d)
    else:
        diff.append(d)

print("Same-person pairs:", len(same), "- mean distance:", round(float(np.mean(same)), 2))
print("Different-person pairs:", len(diff), "- mean distance:", round(float(np.mean(diff)), 2))

wins = sum(s < d for s in same for d in diff)
print("Same-person distance was smaller in", wins, "of", len(same) * len(diff), "comparisons")

enrolled = {p: embeddings[(p, 1)] for p in range(1, people + 1)}

correct = 0
total = 0
for p in range(1, people + 1):
    for k in (2, 3):
        query = embeddings[(p, k)]
        distances = {q: np.linalg.norm(query - e) for q, e in enrolled.items()}
        best = min(distances, key=distances.get)
        correct += (best == p)
        total += 1
        print(f"Person {p} photo {k}: closest enrolled = person {best}, distance {distances[best]:.2f}")

print(f"Top-1 identification: {correct}/{total}")