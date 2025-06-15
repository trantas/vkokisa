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
GOOGLE_SHEET_NAME = "pocket viikkokisa leaderboard"


# --- Custom CSS for Advanced Table Styling & Hiding Sidebar ---
TABLE_STYLING_CSS = """
<style>
    /* Hide the sidebar navigation */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* This is the container for the data rows. Remove height limit */
    div[data-testid="stDataFrame"] > div:nth-child(2) > div {
        max-height: none !important;
    }

    /* Define the scrollable container for the table */
    .table-container {
        width: 100%;
        overflow-x: auto;
    }
    
    #leaderboard-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    #leaderboard-table th, #leaderboard-table td {
        padding: 8px 12px;
        border: 1px solid #3d3d3d;
        text-align: center;
        white-space: nowrap;
    }

    /* --- STICKY RULES --- */

    /* General sticky header */
    #leaderboard-table thead th {
        position: -webkit-sticky; /* for Safari */
        position: sticky;
        top: 0;
        background: #1a1c24; /* A slightly darker color for the header */
        z-index: 3;
    }

    /* First sticky column (Rank) */
    #leaderboard-table thead th:nth-child(1),
    #leaderboard-table tbody td:nth-child(1) {
        position: -webkit-sticky; /* for Safari */
        position: sticky;
        left: 0;
        background: #0e1117; /* Match Streamlit's dark theme background */
        z-index: 2;
    }

    /* Second sticky column (Player) */
    #leaderboard-table thead th:nth-child(2),
    #leaderboard-table tbody td:nth-child(2) {
        position: -webkit-sticky; /* for Safari */
        position: sticky;
        left: 60px; /* Adjust this to be width of first column */
        background: #0e1117;
        z-index: 2;
    }

    /* The top-left corner cell (Rank header) must be on top of everything */
    #leaderboard-table thead th:nth-child(1) {
        z-index: 4; /* Higher z-index than other headers and cells */
        background: #1a1c24; /* Match header background */
    }
    
    /* The Player header cell also needs a higher z-index */
    #leaderboard-table thead th:nth-child(2) {
        z-index: 4;
        background: #1a1c24; /* Match header background */
    }

</style>
"""

# --- Data Loading Function with Caching ---
@st.cache_data(ttl=600)
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
        return pd.DataFrame()


# --- Main Page Display ---

st.header("Pocket viikkokisat '25")

# Inject the custom CSS into the page
st.markdown(TABLE_STYLING_CSS, unsafe_allow_html=True)

leaderboard_df = load_leaderboard_data()

if leaderboard_df is not None and not leaderboard_df.empty:
    # Apply bold styling to the 'Total Points' column and hide the pandas index
    styled_df = leaderboard_df.style \
        .set_properties(**{'font-weight': 'bold'}, subset=['Total Points']) \
        .hide(axis="index")

    # Convert the STYLED DataFrame to an HTML table with a specific ID
    table_html = styled_df.to_html(
        escape=False, 
        table_id="leaderboard-table",
        justify="center"
    )

    # Wrap the HTML table in our scrollable container
    full_html = f"<div class='table-container'>{table_html}</div>"

    # Display using st.markdown
    st.markdown(full_html, unsafe_allow_html=True)
else:
    # This message shows if the sheet is empty or fails to load
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")