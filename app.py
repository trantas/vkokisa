# app.py - The Leaderboard Front Page

import streamlit as st
import pandas as pd
import gspread
import tournament_scraper # Your module

# --- Page Configuration ---
st.set_page_config(
    page_title="Pocket Viikkokisat '25",
    page_icon="🎱",
    layout="wide"
)

# --- Constant ---
# IMPORTANT: Set this to the exact name of your Google Sheet
GOOGLE_SHEET_NAME = "pocket viikkokisa leaderboard"

# --- Custom CSS for Styling the Table ---
# This CSS makes the first two columns sticky and removes the vertical scrollbar
TABLE_STYLING_CSS = """
<style>
/* Target the Streamlit dataframe component */
[data-testid="stDataFrame"] {
    /* Remove the max-height to display the full table */
    max-height: none !important;
}

/* Make the header row sticky */
[data-testid="stDataFrame"] > div:nth-child(2) > div > div > div > div:nth-child(1) {
    position: sticky !important;
    top: 0;
    z-index: 2;
}

/* Make the first column (Rank) sticky */
[data-testid="stDataFrame"] > div:nth-child(2) > div > div > div > div:nth-child(2) > div > div:nth-child(1) {
    position: sticky !important;
    left: 0;
    z-index: 1;
    background-color: #0e1117; /* Match Streamlit's dark theme background */
}
/* Make the second column (Player) sticky */
[data-testid="stDataFrame"] > div:nth-child(2) > div > div > div > div:nth-child(2) > div > div:nth-child(2) {
    position: sticky !important;
    left: 60px; /* Adjust this value based on the width of your first column */
    z-index: 1;
    background-color: #0e1117; /* Match Streamlit's dark theme background */
}
</style>
"""

# --- Data Loading Function with Caching ---
@st.cache_data(ttl=600) # Cache the data for 10 minutes
def load_leaderboard_data():
    """
    Connects to Google Sheets and fetches the leaderboard data.
    Returns a pandas DataFrame.
    """
    try:
        # Check if secrets are configured before trying to use them
        if "gcp_service_account" not in st.secrets:
            st.error("GCP service account secret is not configured. Please add it in your app settings.")
            return None
        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.sheet1
        df = pd.DataFrame(worksheet.get_all_records())
        return df
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
        return pd.DataFrame() # Return empty dataframe on error


# --- Main Page Display ---

# Use the smaller header for the title
st.header("Pocket viikkokisat '25")

# Inject the custom CSS into the page
st.markdown(TABLE_STYLING_CSS, unsafe_allow_html=True)

leaderboard_df = load_leaderboard_data()

if not leaderboard_df.empty:
    st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)
else:
    st.warning("Leaderboard data could not be loaded. An admin can run an update at the /update page.")