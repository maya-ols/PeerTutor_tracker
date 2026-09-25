import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_NAME = "Peer Tutor tracker"  # I'll update this once you confirm the exact name

# ---- Connect to Google Sheets ----
scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scopes
)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

st.set_page_config(page_title="Tutoring Program Tracker", layout="centered")
st.title("📚 Tutoring Program Tracker")

tab1, tab2 = st.tabs(["Log a Session", "Summary"])

# ---- TAB 1: Log a session ----
with tab1:
    st.subheader("Log a New Session")

    with st.form("log_form", clear_on_submit=True):
        st.markdown("**Tutor**")
        tcol1, tcol2 = st.columns(2)
        tutor_first = tcol1.text_input("First name", key="tutor_first")
        tutor_last = tcol2.text_input("Last name", key="tutor_last")

        st.markdown("**Student**")
        scol1, scol2 = st.columns(2)
        student_first = scol1.text_input("First name", key="student_first")
        student_last = scol2.text_input("Last name", key="student_last")

        subject = st.text_input("Subject")
        minutes = st.number_input("Duration (minutes)", min_value=1, step=5)
        date = st.date_input("Date", value=datetime.now())

        submitted = st.form_submit_button("Log Session")

        if submitted:
            if tutor_first and tutor_last and student_first and student_last and subject:
                tutor_name = f"{tutor_first.strip().title()} {tutor_last.strip().title()}"
                student_name = f"{student_first.strip().title()} {student_last.strip().title()}"

                sheet.append_row([
                    date.strftime("%m/%d/%Y"),
                    tutor_name,
                    student_name,
                    subject.strip().title(),
                    minutes
                ])

                st.success(f"Logged: {tutor_name} tutored {student_name} in {subject.strip().title()} for {minutes} min")
            else:
                st.error("Please fill in first and last name for both tutor and student, and subject.")

# ---- TAB 2: Summary ----
with tab2:
    st.subheader("Program Summary")

    records = sheet.get_all_records()
    if not records:
        st.info("No sessions logged yet.")
    else:
        df = pd.DataFrame(records)
        df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

        total_sessions = len(df)
        total_hours = df["Minutes"].sum() / 60

        col1, col2 = st.columns(2)
        col1.metric("Total Sessions", total_sessions)
        col2.metric("Total Hours", f"{total_hours:.1f}")

        st.markdown("**Hours per Tutor**")
        tutor_summary = (df.groupby("Tutor")["Minutes"].sum() / 60).round(1).sort_values(ascending=False)
        st.bar_chart(tutor_summary)

        st.markdown("**Hours per Student**")
        student_summary = (df.groupby("Student")["Minutes"].sum() / 60).round(1).sort_values(ascending=False)
        st.bar_chart(student_summary)

        st.markdown("**All Sessions**")
        st.dataframe(df, use_container_width=True)
