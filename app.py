import streamlit as st
import pandas as pd
import os
import tournament_scraper

# --- App UI Configuration ---
st.set_page_config(page_title="Tournament Scraper", layout="wide")
st.title("Tournament Data Extractor")
st.write("Enter a tournament ID from tspool.fi to fetch data, calculate points, and update the master leaderboard.")

# --- App Logic ---

with st.form(key='scraper_form'):
    tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1, value=848)
    google_sheet_name = st.text_input("Google Sheet Name:", value="Your Google Sheet Name Here")
    submit_button = st.form_submit_button(label='Run Scraper and Update Leaderboard')

if submit_button:
    # --- ADDED: Pre-emptive check for secrets ---
    if "gcp_service_account" not in st.secrets:
        st.error("Error: The `gcp_service_account` secret is not configured in your Streamlit Cloud settings. Please add it.")
    elif not st.secrets["gcp_service_account"]:
        st.error("Error: The `gcp_service_account` secret is empty. Please paste your full JSON key file content into the secret.")
    elif not tournament_id or not google_sheet_name:
        st.warning("Please enter a valid Tournament ID and Google Sheet Name.")
    else:
        with st.spinner(f"Processing tournament {tournament_id}... Please wait."):
            # ... (The rest of the logic is the same as before) ...
            # The try/except block below will now catch more specific errors from the module
            try:
                # This call now benefits from the improved error handling in the module
                tournament_scraper.update_leaderboard_sheet(
                    tournament_date=tournament_date,
                    tournament_points=current_tournament_points, # This should be leaderboard_data
                    sheet_name=google_sheet_name,
                    creds=st.secrets["gcp_service_account"]
                )
                st.success(f"Master leaderboard '{google_sheet_name}' updated successfully!")

            except Exception as e:
                st.error(f"An error occurred while updating the leaderboard.")
                # The error message from the module will now be more specific
                st.error(f"Details: {e}")
