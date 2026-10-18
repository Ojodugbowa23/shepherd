import numpy as np
from recognition import get_embedding

def unit(v):
    return v / np.linalg.norm(v)

def cosine(a, b):
    return float(1 - np.dot(unit(a), unit(b)))

def rank_of(query, true_name, gallery):
    order = sorted(gallery, key=lambda n: cosine(query, gallery[n]))
    return order.index(true_name) + 1

emb = {f"p{p}": [get_embedding(f"test_photos/lfw_check/person{p}_{k}.jpg") for k in (1, 2, 3)]
       for p in range(1, 5)}
love = [get_embedding("test_photos/Love_1.jpg"), get_embedding("test_photos/Love_2.jpg")]

single, multi = [], []
for held in range(3):
    kept = {n: [unit(e) for i, e in enumerate(embs) if i != held] for n, embs in emb.items()}
    g_single = {n: k[0] for n, k in kept.items()}
    g_multi = {n: unit(sum(k)) for n, k in kept.items()}
    g_single["love"] = g_multi["love"] = unit(love[0])
    queries = [(n, embs[held]) for n, embs in emb.items()] + [("love", love[1])]
    for n, q in queries:
        single.append(rank_of(q, n, g_single))
        multi.append(rank_of(q, n, g_multi))

for label, ranks in (("one photo", single), ("two photos averaged", multi)):
    print(label, "| rank 1:", sum(r == 1 for r in ranks),
          "| top 3:", sum(r <= 3 for r in ranks), "| of", len(ranks))