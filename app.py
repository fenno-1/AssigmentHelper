import streamlit as st
from dotenv import load_dotenv
from matcher import fetch_url_text, extract_pdf_text, match_cv_to_assignment

load_dotenv(override=True)

st.set_page_config(page_title="AssigmentHelper", page_icon="📋", layout="wide")

st.title("📋 AssigmentHelper")
st.caption("Match consultant CVs to assignments using AI")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Assignment")
    input_mode = st.radio("Input type", ["Free text", "URL"], horizontal=True)

    assignment_text = ""
    if input_mode == "URL":
        url = st.text_input("Assignment URL", placeholder="https://...")
        if url and st.button("Fetch assignment", key="fetch"):
            with st.spinner("Fetching..."):
                try:
                    assignment_text = fetch_url_text(url)
                    st.session_state["assignment_text"] = assignment_text
                    st.success("Fetched successfully")
                except Exception as e:
                    st.error(f"Could not fetch URL: {e}")
        assignment_text = st.session_state.get("assignment_text", "")
        if assignment_text:
            with st.expander("Preview fetched text"):
                st.text(assignment_text[:2000] + ("..." if len(assignment_text) > 2000 else ""))
    else:
        assignment_text = st.text_area(
            "Paste assignment description",
            height=300,
            placeholder="Paste the full assignment description here...",
        )

with col2:
    st.subheader("Consultant CV")
    consultant_name = st.text_input("Consultant name", placeholder="First Last")
    cv_file = st.file_uploader("Upload CV (PDF or TXT)", type=["pdf", "txt"])

    cv_text = ""
    if cv_file:
        if cv_file.type == "application/pdf":
            cv_text = extract_pdf_text(cv_file.read())
        else:
            cv_text = cv_file.read().decode("utf-8", errors="ignore")

        with st.expander("Preview CV text"):
            st.text(cv_text[:2000] + ("..." if len(cv_text) > 2000 else ""))

st.divider()

run = st.button(
    "Match CV to Assignment ✨",
    type="primary",
    disabled=not (assignment_text and cv_text and consultant_name),
)

if not (assignment_text and cv_text and consultant_name):
    missing = []
    if not assignment_text:
        missing.append("assignment description")
    if not cv_text:
        missing.append("CV")
    if not consultant_name:
        missing.append("consultant name")
    if missing:
        st.info(f"Please provide: {', '.join(missing)}")

if run:
    st.subheader("Analysis")
    output_container = st.empty()
    full_output = ""

    with st.spinner("Analysing with Claude..."):
        for chunk in match_cv_to_assignment(assignment_text, cv_text, consultant_name):
            full_output += chunk
            output_container.markdown(full_output)

    st.session_state["last_output"] = full_output

    st.download_button(
        label="Download result as Markdown",
        data=full_output,
        file_name=f"{consultant_name.replace(' ', '_')}_match.md",
        mime="text/markdown",
    )
