import numpy as np
from recognition import get_embedding

def euclidean(a, b):
    return float(np.linalg.norm(a - b))

def cosine(a, b):
    return float(1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def rank_report(query_vec, true_name, gallery, metric):
    distances = [(name, metric(query_vec, vec)) for name, vec in gallery.items()]
    distances.sort(key=lambda pair: pair[1])
    names = [name for name, _ in distances]
    rank = names.index(true_name) + 1
    line = ", ".join(f"{n} {d:.2f}" for n, d in distances)
    print(f"{true_name} rank {rank}: {line}")
    return rank

gallery = {f"p{p}": get_embedding(f"test_photos/lfw_check/person{p}_1.jpg") for p in range(1, 5)}
gallery["love"] = get_embedding("test_photos/Love_1.jpg")
print("Embedding norms:", {k: round(float(np.linalg.norm(v)), 1) for k, v in gallery.items()})

queries = [(f"p{p}", get_embedding(f"test_photos/lfw_check/person{p}_{k}.jpg"))
           for p in range(1, 5) for k in (2, 3)]
strangers = [get_embedding(f"test_photos/lfw_check/person5_{k}.jpg") for k in (2, 3)]
queries.append(("love", get_embedding("test_photos/Love_2.jpg")))

for metric in (euclidean, cosine):
    print("\n" + metric.__name__)
    ranks = [rank_report(vec, name, gallery, metric) for name, vec in queries]
    print("rank 1:", sum(r == 1 for r in ranks), "of", len(ranks))
    print("rank 3 or better:", sum(r <= 3 for r in ranks), "of", len(ranks))
    for vec in strangers:
        closest = min((metric(vec, v), n) for n, v in gallery.items())
        print(f"stranger closest: {closest[1]} {closest[0]:.2f}")