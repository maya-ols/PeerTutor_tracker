import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_NAME = "Peer Tutor tracker"

# ---- Connect to Google Sheets ----
scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scopes
)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

st.set_page_config(page_title="Peer Tutoring Tracker", layout="centered")
st.title("📚 Peer Tutoring Tracker")

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
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")

        today = pd.Timestamp(datetime.now().date())

        # ---- TODAY'S SUMMARY ----
        st.markdown("## Today's Summary")
        today_df = df[df["Date"] == today]

        if today_df.empty:
            st.info("No sessions logged today yet.")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Sessions Today", len(today_df))
            col2.metric("Hours Today", f"{today_df['Minutes'].sum() / 60:.1f}")

            today_tutor_summary = (
                today_df.groupby("Tutor")["Minutes"].sum() / 60
            ).round(1).sort_values(ascending=False).reset_index()
            today_tutor_summary.columns = ["Tutor", "Hours Today"]

            st.dataframe(today_tutor_summary, use_container_width=True, hide_index=True)

        st.divider()

        # ---- ALL-TIME SUMMARY ----
        st.markdown("## All-Time Summary")

        col1, col2 = st.columns(2)
        col1.metric("Total Sessions", len(df))
        col2.metric("Total Hours", f"{df['Minutes'].sum() / 60:.1f}")

        all_time_tutor_summary = (
            df.groupby("Tutor")["Minutes"].sum() / 60
        ).round(1).sort_values(ascending=False).reset_index()
        all_time_tutor_summary.columns = ["Tutor", "Total Hours"]
        all_time_tutor_summary.insert(0, "Rank", range(1, len(all_time_tutor_summary) + 1))

        st.markdown(f"**{len(all_time_tutor_summary)} tutors total**")
        st.dataframe(
            all_time_tutor_summary,
            use_container_width=True,
            hide_index=True,
            height=min(35 * (len(all_time_tutor_summary) + 1), 600)
        )
