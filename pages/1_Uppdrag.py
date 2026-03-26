import json
import uuid
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Uppdrag", page_icon="📁", layout="wide")

CONSULTANTS = ["Manuel Kandala", "Mia Aspberg", "Magnus Sörin"]
STATUSES = ["Öppen", "Intervju", "Vunnen", "Förlorad", "Avböjd"]
DATA_FILE = Path(__file__).parent.parent / "assignments.json"

LIST_COLUMNS = [
    "name",
    "date",
    "consultant",
    "status",
    "customer",
    "broker",
    "url",
    "contact_person",
    "contact_phone",
    "contact_email",
    "price",
]

COLUMN_LABELS = {
    "name": "Uppdragsnamn",
    "date": "Datum",
    "consultant": "Konsult",
    "status": "Status",
    "customer": "Kund",
    "broker": "Förmedlare",
    "url": "URL",
    "contact_person": "Kontaktperson",
    "contact_phone": "Telefon",
    "contact_email": "E-post",
    "price": "Pris (kr/h)",
}


def load_assignments() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_assignments(assignments: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(assignments, f, ensure_ascii=False, indent=2)


def empty_assignment() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": "",
        "date": str(date.today()),
        "consultant": CONSULTANTS[0],
        "status": "Öppen",
        "customer": "",
        "broker": "",
        "url": "",
        "contact_person": "",
        "contact_phone": "",
        "contact_email": "",
        "price": None,
    }


def assignment_form(assignment: dict, is_new: bool) -> None:
    with st.form("assignment_form"):
        st.subheader("Nytt uppdrag" if is_new else "Redigera uppdrag")

        name = st.text_input("Uppdragsnamn *", value=assignment.get("name", ""))
        date_val = st.text_input("Datum (YYYY-MM-DD)", value=assignment.get("date", str(date.today())))

        consultant_idx = CONSULTANTS.index(assignment["consultant"]) if assignment.get("consultant") in CONSULTANTS else 0
        consultant = st.selectbox("Konsult *", CONSULTANTS, index=consultant_idx)

        status_idx = STATUSES.index(assignment["status"]) if assignment.get("status") in STATUSES else 0
        status = st.selectbox("Status", STATUSES, index=status_idx)

        customer = st.text_input("Kund", value=assignment.get("customer", ""))
        broker = st.text_input("Förmedlare", value=assignment.get("broker", ""))
        url = st.text_input("Uppdragets URL", value=assignment.get("url", ""))
        contact_person = st.text_input("Kontaktperson", value=assignment.get("contact_person", ""))
        contact_phone = st.text_input("Telefon", value=assignment.get("contact_phone", ""))
        contact_email = st.text_input("E-post", value=assignment.get("contact_email", ""))

        price_val = assignment.get("price")
        price = st.number_input(
            "Pris (kr/h)",
            min_value=0,
            step=25,
            value=int(price_val) if price_val is not None else 0,
        )

        col_save, col_cancel = st.columns([1, 5])
        submitted = col_save.form_submit_button("Spara", type="primary")
        cancelled = col_cancel.form_submit_button("Avbryt")

    if cancelled:
        st.session_state.pop("editing_id", None)
        st.session_state.pop("creating", None)
        st.rerun()

    if submitted:
        if not name.strip():
            st.error("Uppdragsnamn är obligatoriskt.")
            return
        if not consultant:
            st.error("Konsult är obligatoriskt.")
            return

        updated = {
            **assignment,
            "name": name.strip(),
            "date": date_val.strip(),
            "consultant": consultant,
            "status": status,
            "customer": customer.strip(),
            "broker": broker.strip(),
            "url": url.strip(),
            "contact_person": contact_person.strip(),
            "contact_phone": contact_phone.strip(),
            "contact_email": contact_email.strip(),
            "price": int(price) if price else None,
        }

        assignments = load_assignments()
        if is_new:
            assignments.append(updated)
        else:
            assignments = [updated if a["id"] == updated["id"] else a for a in assignments]

        save_assignments(assignments)
        st.session_state.pop("editing_id", None)
        st.session_state.pop("creating", None)
        st.success("Sparat!")
        st.rerun()


# --- Main ---

st.title("Uppdrag")

if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "creating" not in st.session_state:
    st.session_state["creating"] = False

# Show form when creating or editing
if st.session_state["creating"]:
    assignment_form(empty_assignment(), is_new=True)
    st.stop()

if st.session_state["editing_id"]:
    assignments = load_assignments()
    match = next((a for a in assignments if a["id"] == st.session_state["editing_id"]), None)
    if match:
        assignment_form(match, is_new=False)
        st.stop()
    else:
        st.session_state["editing_id"] = None

# List view
col_title, col_btn = st.columns([6, 1])
col_btn.button(
    "Nytt uppdrag",
    type="primary",
    on_click=lambda: st.session_state.update({"creating": True}),
)

assignments = load_assignments()

if not assignments:
    st.info("Inga uppdrag registrerade ännu. Klicka på 'Nytt uppdrag' för att börja.")
    st.stop()

# Sort by date descending by default
assignments_sorted = sorted(assignments, key=lambda a: a.get("date", ""), reverse=True)

# Build display table with a clickable name column
st.write("Klicka på ett uppdragsnamn för att redigera.")

header_cols = st.columns([2, 1, 1.5, 1, 1.5, 1.5, 2, 1.5, 1.2, 1.8, 1])
for col, key in zip(header_cols, LIST_COLUMNS):
    col.markdown(f"**{COLUMN_LABELS[key]}**")

st.divider()

for assignment in assignments_sorted:
    row_cols = st.columns([2, 1, 1.5, 1, 1.5, 1.5, 2, 1.5, 1.2, 1.8, 1])

    # Name as a button to trigger edit
    if row_cols[0].button(assignment.get("name", "(inget namn)"), key=f"edit_{assignment['id']}"):
        st.session_state["editing_id"] = assignment["id"]
        st.rerun()

    row_cols[1].write(assignment.get("date", ""))
    row_cols[2].write(assignment.get("consultant", ""))
    row_cols[3].write(assignment.get("status", ""))
    row_cols[4].write(assignment.get("customer", ""))
    row_cols[5].write(assignment.get("broker", ""))

    url = assignment.get("url", "")
    if url:
        row_cols[6].markdown(f"[länk]({url})")
    else:
        row_cols[6].write("")

    row_cols[7].write(assignment.get("contact_person", ""))
    row_cols[8].write(assignment.get("contact_phone", ""))
    row_cols[9].write(assignment.get("contact_email", ""))

    price = assignment.get("price")
    row_cols[10].write(str(price) if price is not None else "")
