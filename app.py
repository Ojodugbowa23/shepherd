import csv
import io
import os
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import quote

import cv2
import streamlit as st
from PIL import Image, ImageDraw

from absences import find_absences, last_sunday, sundays_between
from detect_faces import detect_faces, crop_face
from enrollment import enroll_member_from_face
from facebook_source import fetch_page_photos
from matching import shortlist_from_embedding
from recognition import embedding_from_image
from seed_demo import seed_if_empty
from send_messages import TEMPLATE
from setup_db import add_attendance, add_member, get_phone

APP_NAME = "Shepherd"
DB = "church_register.db"
IMAGE_TYPES = {".jpg", ".jpeg", ".png"}
METHOD_LABEL = {"face_recognition": "photo match", "manual": "by hand"}

ICONS = {
    "facebook": "<path d='M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z'/>",
    "users": "<path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/>"
             "<path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
    "pencil": "<path d='M12 20h9'/><path d='M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z'/>",
    "calendar": "<rect x='3' y='4' width='18' height='18' rx='2'/><path d='M16 2v4M8 2v4M3 10h18'/>",
    "message": "<path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/>",
    "face": "<circle cx='12' cy='12' r='10'/><path d='M8 14s1.5 2 4 2 4-2 4-2'/><path d='M9 9h.01'/><path d='M15 9h.01'/>",
    "check": "<path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><path d='m9 11 3 3L22 4'/>",
    "clock": "<circle cx='12' cy='12' r='10'/><path d='M12 6v6l4 2'/>",
    "image": "<rect x='3' y='3' width='18' height='18' rx='2'/><circle cx='8.5' cy='8.5' r='1.5'/><path d='m21 15-5-5L5 21'/>",
}
COLUMN = ('[data-testid="column"]', '[data-testid="stColumn"]')


def icon_rule(selectors, name):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
           "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>" + ICONS[name] + "</svg>")
    uri = "data:image/svg+xml," + quote(svg)
    return (", ".join(selectors) + ' { content: ""; display: inline-block; width: 1em; height: 1em; '
            'margin-right: .5em; vertical-align: -.125em; color: var(--accent); background-color: currentColor; '
            f'-webkit-mask: url("{uri}") center / contain no-repeat; mask: url("{uri}") center / contain no-repeat; }}\n')


BASE_CSS = """
:root {
  --ink: #1F2A2E; --muted: #5B6B6F; --line: #DDE2E0; --accent: #0D5C63; --accent-dark: #094A50;
  --card: #FFFFFF; --sidebar: #ECEFEE;
  --r-sm: 6px; --r-md: 12px; --ease: cubic-bezier(.2, .7, .2, 1);
  --t-sm: .875rem; --t-base: 1rem; --t-lg: 1.25rem; --t-xl: 1.75rem; --t-2xl: 2.25rem;
}
html, body, .stApp { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.5; color: var(--ink); }
h1, h2, h3 { font-weight: 600; line-height: 1.25; letter-spacing: 0; color: var(--ink); }
h1 { font-size: var(--t-xl); }
h2, h3 { font-size: var(--t-lg); }
p, label, li { font-size: var(--t-base); font-weight: 400; }
[data-testid="stCaptionContainer"] { font-size: var(--t-sm); color: var(--muted); }
.stMarkdown p { margin: 0 0 .75rem; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 3.5rem; max-width: 1200px; }
[data-testid="stVerticalBlock"] { gap: .75rem; }
[data-testid="stSidebar"] { background: var(--sidebar); border-right: 1px solid var(--line); }
.brand { margin: 0 0 1.5rem; }
.brand-word { display: inline-block; font-size: var(--t-xl); font-weight: 600; line-height: 1.25;
  color: var(--accent); padding-bottom: .25rem; border-bottom: 3px solid var(--accent); }
.note { background: var(--card); border: 1px solid var(--line); border-radius: var(--r-sm); padding: .75rem 1rem;
  font-size: var(--t-sm); color: var(--muted); margin-top: .5rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: var(--r-md); }
[data-baseweb="input"] > div, [data-baseweb="select"] > div { background: var(--card); border-radius: var(--r-sm); }
.stButton > button, .stDownloadButton > button { border-radius: var(--r-sm); font-weight: 600;
  transition: transform 160ms var(--ease), border-color 160ms var(--ease); }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px); }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { min-height: 2.75rem; padding: 0 1.5rem; }
.stButton > button[kind="secondary"], [data-testid="stBaseButton-secondary"] { border-color: var(--accent); color: var(--accent); background: transparent; }
.st-key-fetch_photos, .st-key-fetch_photos button { width: 100%; }
button[data-baseweb="tab"] { font-weight: 600; }
[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--line); border-radius: var(--r-md);
  padding: 1rem 1.25rem; animation: rise 360ms var(--ease) both;
  transition: transform 160ms var(--ease), border-color 160ms var(--ease); }
[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: var(--accent); }
[data-testid="stMetricLabel"] p { font-size: var(--t-sm); font-weight: 400; color: var(--muted); }
[data-testid="stMetricValue"] { font-size: var(--t-2xl); font-weight: 600; line-height: 1.2; color: var(--ink); }
[data-testid="column"]:nth-child(2) [data-testid="stMetric"], [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] { animation-delay: 70ms; }
[data-testid="column"]:nth-child(3) [data-testid="stMetric"], [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] { animation-delay: 140ms; }
[data-testid="column"]:nth-child(4) [data-testid="stMetric"], [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] { animation-delay: 210ms; }
.empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: .25rem;
  padding: 2rem 1rem; background: var(--card); border: 1px dashed var(--line); border-radius: var(--r-md); color: var(--muted); }
.empty strong { color: var(--ink); font-size: var(--t-base); font-weight: 600; }
.empty span { font-size: var(--t-sm); }
.skeleton-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: .5rem 0 1rem; }
.skeleton { height: 190px; border-radius: var(--r-md); border: 1px solid var(--line);
  background: linear-gradient(90deg, #EEF0EE 25%, #E1E6E4 37%, #EEF0EE 63%);
  background-size: 400% 100%; animation: shimmer 1.4s var(--ease) infinite; }
@keyframes shimmer { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
"""
ICON_CSS = ""
for n, name in enumerate(["facebook", "users", "pencil", "calendar", "message"], start=1):
    ICON_CSS += icon_rule([f'button[data-baseweb="tab"]:nth-of-type({n}) p::before'], name)
for n, name in enumerate(["users", "face", "check", "clock"], start=1):
    ICON_CSS += icon_rule([f'{c}:nth-child({n}) [data-testid="stMetricLabel"] p::before' for c in COLUMN], name)
ICON_CSS += icon_rule([".empty::before"], "image")
EMPTY_ICON_SIZE = ".empty::before { display: block; width: 1.75rem; height: 1.75rem; margin: 0 0 .5rem; }\n"
STYLE = "<style>" + BASE_CSS + ICON_CSS + EMPTY_ICON_SIZE + "</style>"


def make_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, 63, 63), radius=14, fill=(13, 92, 99, 255))
    draw.rectangle((28, 12, 35, 52), fill=(255, 255, 255, 255))
    draw.rectangle((18, 22, 45, 29), fill=(255, 255, 255, 255))
    return img


def query(sql, args=()):
    conn = sqlite3.connect(DB)
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return rows


def all_members():
    return query("SELECT id, full_name FROM members WHERE status = 'active' ORDER BY full_name")


def already_marked(member_id, day):
    return bool(query(
        "SELECT 1 FROM attendance_records WHERE member_id = ? AND service_date = ?",
        (member_id, day),
    ))


def service_dates():
    joined = [r[0] for r in query(
        "SELECT date_joined FROM members WHERE status = 'active' AND date_joined IS NOT NULL")]
    dates = {r[0] for r in query("SELECT DISTINCT service_date FROM attendance_records")}
    if joined:
        start = date.fromisoformat(min(joined))
        dates |= {d.isoformat() for d in sundays_between(start, last_sunday())}
    return sorted(dates, reverse=True)


def service_record(day):
    present = query(
        "SELECT m.id, m.full_name, a.method FROM attendance_records a "
        "JOIN members m ON m.id = a.member_id WHERE a.service_date = ? ORDER BY m.full_name",
        (day,),
    )
    present_ids = {r[0] for r in present}
    absent = [r for r in query(
        "SELECT id, full_name, phone_number FROM members WHERE status = 'active' "
        "AND date_joined IS NOT NULL AND date_joined <= ? ORDER BY full_name", (day,))
        if r[0] not in present_ids]
    return present, absent


def section(title, caption):
    st.subheader(title)
    st.caption(caption)


def empty_state(title, hint):
    st.markdown(f'<div class="empty"><strong>{title}</strong><span>{hint}</span></div>',
                unsafe_allow_html=True)


def skeleton(count):
    return '<div class="skeleton-row">' + '<div class="skeleton"></div>' * min(count, 8) + "</div>"


def demo_enabled():
    if os.environ.get("SHEPHERD_DEMO") == "1":
        return True
    try:
        return bool(st.secrets.get("demo", False))
    except Exception:
        return False


def review_photo(path, key, day):
    with st.spinner("Detecting faces"):
        img, boxes = detect_faces(path)
    if not boxes:
        empty_state("No faces found", "Try a clearer photo with faces turned toward the camera.")
        return
    members = dict(all_members())

    marked = img.copy()
    for i, (x, y, w, h) in enumerate(boxes, start=1):
        cv2.rectangle(marked, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(marked, str(i), (x, max(20, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    st.image(cv2.cvtColor(marked, cv2.COLOR_BGR2RGB), caption=f"{len(boxes)} faces found")

    placeholder = st.empty()
    placeholder.markdown(skeleton(len(boxes)), unsafe_allow_html=True)
    progress = st.progress(0, text="Matching faces")
    candidates = []
    for i, box in enumerate(boxes):
        face = crop_face(img, box)
        top = shortlist_from_embedding(embedding_from_image(face), k=3)
        candidates.append((face, top))
        progress.progress((i + 1) / len(boxes), text=f"Matching face {i + 1} of {len(boxes)}")
    progress.empty()
    placeholder.empty()

    st.caption("Every face starts on Skip. Nothing is saved until you press Save attendance.")
    stamp = f"{key}_{Path(path).name}_{Path(path).stat().st_size}"
    choices = []
    columns = st.columns(4)
    for i, (face, top) in enumerate(candidates):
        top_ids = [m for m, _ in top]
        options = {"Skip": (None, None)}
        for member_id, distance in top:
            options[f"{members[member_id]} ({distance:.2f})"] = (member_id, "face_recognition")
        for member_id, member_name in members.items():
            if member_id not in top_ids:
                options[f"{member_name} (by hand)"] = (member_id, "manual")
        with columns[i % 4]:
            with st.container(border=True):
                st.image(face, caption=f"Face {i + 1}", width=130)
                label = st.selectbox("Who is this?", list(options), key=f"{stamp}_{i}")
        choices.append(options[label])

    if st.button("Save attendance", type="primary", key=f"save_{stamp}"):
        with st.spinner("Saving attendance"):
            saved, skipped = [], []
            for member_id, method in choices:
                if member_id is None:
                    continue
                if already_marked(member_id, day):
                    skipped.append(members[member_id])
                else:
                    add_attendance(member_id, day, method)
                    saved.append(members[member_id])
        st.success(f"Saved for {day}: {', '.join(saved) or 'nobody'}")
        if skipped:
            st.info(f"Already marked, left as is: {', '.join(skipped)}")


st.set_page_config(page_title=f"{APP_NAME} | Church attendance", page_icon=make_icon(), layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(f'<div class="brand"><span class="brand-word">{APP_NAME}</span></div>',
            unsafe_allow_html=True)

if demo_enabled():
    seed_if_empty()

top = st.container()

with st.sidebar:
    st.subheader("Service")
    service_date = st.date_input("Service date", value=last_sunday())
    st.markdown('<div class="note">Recognition suggests and a person confirms. '
                'Messages are a dry run.</div>', unsafe_allow_html=True)
day = service_date.isoformat()

tab_fb, tab_members, tab_hand, tab_services, tab_follow = st.tabs(
    ["Facebook page", "Members", "Mark by hand", "Services", "Follow-up"]
)

with tab_fb:
    section("Facebook page", "Fetch recent page photos, then check in the faces. The token is never saved to disk.")
    c1, c2, c3 = st.columns([2, 3, 1])
    page_id = c1.text_input("Page ID", value=os.environ.get("FACEBOOK_PAGE_ID", ""))
    token = c2.text_input("Page access token", type="password",
                          value=os.environ.get("FACEBOOK_PAGE_TOKEN", ""))
    count = c3.number_input("Photos", min_value=1, max_value=25, value=8)
    if st.button("Fetch photos", type="primary", key="fetch_photos"):
        with st.spinner("Fetching photos from Facebook"):
            try:
                fetch_page_photos(page_id, token, int(count))
            except Exception as error:
                st.error(f"Could not fetch photos: {error}")
    folder = Path("page_photos")
    photos = sorted(p for p in folder.glob("*") if p.suffix.lower() in IMAGE_TYPES) if folder.exists() else []
    if not photos:
        empty_state("No page photos yet", "Fetch them from the page, or place downloaded photos in the page_photos folder.")
    else:
        st.image([str(p) for p in photos], width=110)
        chosen = st.selectbox("Photo to check in", photos, format_func=lambda p: p.name)
        review_photo(str(chosen), "fb", day)

with tab_members:
    section("Members", "Add a member and see who has a face enrolled.")
    left, right = st.columns([1, 2])
    with left:
        name = st.text_input("Full name")
        phone = st.text_input("Phone number")
        photo = st.file_uploader("Front-facing photo (optional)",
                                 type=["jpg", "jpeg", "png"], key="enroll_photo")
        if st.button("Add member", type="primary"):
            if not name.strip() or not phone.strip():
                st.error("Name and phone number are required.")
            else:
                member_id = add_member(name.strip(), phone.strip())
                if photo is not None:
                    Path("member_photos").mkdir(exist_ok=True)
                    path = f"member_photos/member_{member_id}.jpg"
                    Path(path).write_bytes(photo.getvalue())
                    with st.spinner("Enrolling face"):
                        try:
                            enroll_member_from_face(member_id, path)
                            st.success(f"Added {name} (id {member_id}) with a face enrolled.")
                        except ValueError as error:
                            st.warning(f"Added {name} (id {member_id}), no face enrolled: {error}")
                else:
                    st.success(f"Added {name} (id {member_id}) without a photo.")
    with right:
        rows = query("SELECT id, full_name, phone_number, date_joined, embedding IS NOT NULL "
                     "FROM members WHERE status = 'active' ORDER BY id")
        st.dataframe(
            [{"id": r[0], "name": r[1], "phone": r[2], "joined": r[3],
              "face enrolled": "yes" if r[4] else "no"} for r in rows],
            hide_index=True,
        )

with tab_hand:
    section("Mark by hand", "Record attendance without a photo for the service date in the sidebar.")
    names = dict(all_members())
    present = st.multiselect("Members present", list(names), format_func=lambda i: names[i])
    if st.button("Save manual attendance", type="primary"):
        with st.spinner("Saving attendance"):
            for member_id in present:
                if already_marked(member_id, day):
                    st.info(f"{names[member_id]} was already marked for {day}.")
                else:
                    add_attendance(member_id, day, "manual")
                    st.success(f"Marked {names[member_id]} for {day}.")

with tab_services:
    section("Services", "Present and absent members for each service. Absent is worked out from the register, so it always matches the attendance records.")
    dates = service_dates()
    if not dates:
        empty_state("No services yet", "Services appear once members join or attendance is saved.")
    else:
        summary = []
        for d in dates:
            p, a = service_record(d)
            summary.append({"service": d, "present": len(p), "absent": len(a)})
        st.dataframe(summary, hide_index=True)
        chosen_day = st.selectbox("Service", dates, index=dates.index(day) if day in dates else 0)
        present_rows, absent_rows = service_record(chosen_day)
        left, right = st.columns(2)
        with left:
            st.markdown(f"**Present ({len(present_rows)})**")
            st.dataframe([{"name": r[1], "recorded by": METHOD_LABEL.get(r[2], r[2])}
                          for r in present_rows], hide_index=True)
        with right:
            st.markdown(f"**Absent ({len(absent_rows)})**")
            st.dataframe([{"name": r[1], "phone": r[2]} for r in absent_rows], hide_index=True)
        csv_rows = [["service", "name", "status", "recorded by"]]
        csv_rows += [[chosen_day, r[1], "present", METHOD_LABEL.get(r[2], r[2])] for r in present_rows]
        csv_rows += [[chosen_day, r[1], "absent", ""] for r in absent_rows]
        buffer = io.StringIO()
        csv.writer(buffer).writerows(csv_rows)
        st.download_button("Download this service as CSV", buffer.getvalue(),
                           file_name=f"service_{chosen_day}.csv", mime="text/csv")

with tab_follow:
    section("Follow-up", "List members absent from a service and preview the check-in message.")
    latest_only = st.checkbox("Only the latest service", value=True)
    if st.button("Find absences", type="primary"):
        with st.spinner("Finding absences"):
            rows = find_absences()
            if latest_only:
                latest = last_sunday().isoformat()
                rows = [r for r in rows if r[2] == latest]
        if not rows:
            st.success("No absences found.")
        else:
            st.write(f"{len(rows)} absence(s). These messages are a dry run. Nothing is sent.")
            for member_id, member_name, sunday in rows:
                with st.container(border=True):
                    st.markdown(f"**To {get_phone(member_id)}**")
                    st.write(TEMPLATE.format(name=member_name, sunday=sunday))

with top:
    total = query("SELECT COUNT(*) FROM members WHERE status = 'active'")[0][0]
    enrolled = query("SELECT COUNT(*) FROM members WHERE status = 'active' "
                     "AND embedding IS NOT NULL")[0][0]
    present_now = query("SELECT COUNT(DISTINCT member_id) FROM attendance_records "
                        "WHERE service_date = ?", (day,))[0][0]
    a, b, c, d = st.columns(4)
    a.metric("Members", total)
    b.metric("Faces enrolled", enrolled)
    c.metric("Present", present_now)
    d.metric("Not marked", max(total - present_now, 0))