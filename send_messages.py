from absences import find_absences
from setup_db import get_phone

TEMPLATE = (
    "Hello {name}, we missed you at church on {sunday}. "
    "We hope all is well. We just wanted to check on you and see how you're doing. "
    "God bless you"
)


def build_messages():
    messages = []
    for member_id, name, sunday in find_absences():
        messages.append((member_id, get_phone(member_id), TEMPLATE.format(name=name, sunday=sunday)))
    return messages


def send(phone, text, dry_run=True):
    if dry_run:
        print(f"[DRY RUN] To {phone}: {text}")
    else:
        raise NotImplementedError("Connect an SMS or WhatsApp provider here.")


if __name__ == "__main__":
    for member_id, phone, text in build_messages():
        send(phone, text)