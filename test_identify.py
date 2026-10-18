from setup_db import add_member
from enrollment import enroll_member
from matching import identify

ids = {}
for p in range(1, 5):
    ids[p] = add_member(f"Test Person {p}", "00000000000")
    enroll_member(ids[p], f"test_photos/lfw_check/person{p}_1.jpg")
print("Enrolled test members:", ids)

for p in range(1, 6):
    for k in (2, 3):
        best_id, dist = identify(f"test_photos/lfw_check/person{p}_{k}.jpg")
        print(f"person{p}_{k} -> member {best_id}, distance {dist:.2f}")