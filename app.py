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
GOOGLE_SHEET_NAME = "Your Google Sheet Name Here"


# --- Custom CSS for our own HTML Table ---
TABLE_STYLING_CSS = """
<style>
    /* This class will be applied to the container of our table */
    .table-container {
        width: 100%;
        overflow-x: auto; /* Enable horizontal scrolling */
    }
    /* Style the table itself */
    #leaderboard-table {
        border-collapse: collapse; /* Essential for sticky headers */
        width: 100%;
        color: #FAFAFA; /* Text color for dark theme */
    }
    /* Style header and data cells */
    #leaderboard-table th, #leaderboard-table td {
        padding: 8px 12px;
        border: 1px solid #3d3d3d;
        text-align: center;
    }
    /* Style the header row */
    #leaderboard-table thead th {
        background-color: #1a1c24; /* A slightly darker color for the header */
        position: sticky;
        top: 0;
        z-index: 10;
    }
    /* Make the first column (Rank) sticky */
    #leaderboard-table thead th:nth-child(1),
    #leaderboard-table tbody tr td:nth-child(1) {
        position: sticky;
        left: 0;
        background-color: #0e1117; /* Match Streamlit's dark theme background */
        z-index: 5;
    }
    /* Make the second column (Player) sticky */
    #leaderboard-table thead th:nth-child(2),
    #leaderboard-table tbody tr td:nth-child(2) {
        position: sticky;
        left: 60px; /* Adjust this value based on the width of the Rank column */
        background-color: #0e1117;
        z-index: 5;
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

st.header("Pocket viikkokisat '25")

leaderboard_df = load_leaderboard_data()

if not leaderboard_df.empty:
    # Convert the DataFrame to an HTML table with a specific ID
    table_html = leaderboard_df.to_html(
        index=False, 
        escape=False, 
        table_id="leaderboard-table",
        justify="center"
    )

    # Combine the custom CSS and the HTML table into a single string
    full_html = f"{TABLE_STYLING_CSS}<div class='table-container'>{table_html}</div>"

    # Display using st.markdown
    st.markdown(full_html, unsafe_allow_html=True)
else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")