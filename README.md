# Shepherd

Church attendance register with face-assisted check-in and absence follow-up.

## What it does

An admin fetches photos from the church Facebook page. The app detects each face, suggests the three closest enrolled members, and a person confirms or skips every face. Attendance is stored per service. Members with no record for a service are listed as absent, and a check-in message is previewed for each (dry run, nothing is sent).

## Run it

    python -m pip install -r requirements.txt
    python seed_demo.py
    python -m streamlit run app.py --server.fileWatcherType none

`seed_demo.py` creates a demo database with fake members. YuNet face detection needs `face_detection_yunet_2023mar.onnx` from the OpenCV Zoo in the project folder.

## Results so far

The face model is a small CNN trained on LFW identities with two or more photos. On held-out LFW faces it ranked the right person first in 6 of 9 queries and in the top three in 8 of 9. On a real church group photo, both labelled members missed the top three. Distance cannot separate members from strangers, so nothing is auto-marked. A person always confirms.

## Known limits

Weak on profile photos and covered heads with the Haar detector, which is why YuNet is used. Accuracy falls as the gallery grows. The model was trained briefly. Real member data (database, photos) is never committed.