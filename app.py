# app.py - The Leaderboard Front Page

import streamlit as st
import pandas as pd
import gspread
import tournament_scraper # Your module

# --- Page Configuration ---
st.set_page_config(
    page_title="Pocket Viikkokisat '25",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Constant ---
GOOGLE_SHEET_NAME = "pocket viikkokisa leaderboard"

# --- Hide Sidebar CSS ---
st.markdown(
    """
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }
</style>
""",
    unsafe_allow_html=True,
)

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

leaderboard_df = load_leaderboard_data()

if leaderboard_df is not None and not leaderboard_df.empty:
    
    # --- FIXED: Use set_index and a calculated height ---
    
    # Check if the required 'Rank' column exists before trying to set it as the index
    if 'Rank' in leaderboard_df.columns:
        
        df_to_display = leaderboard_df.set_index('Rank')
        
        # --- ADDED: Calculate height dynamically ---
        # Calculate height: (number of rows + 1 for header) * 35 pixels per row
        table_height = (len(df_to_display) + 1) * 35
        
        # Display the dataframe with the new calculated height
        st.dataframe(
            df_to_display, 
            use_container_width=True,
            height=table_height
        )
    else:
        # Fallback for if the 'Rank' column is missing
        st.warning("Leaderboard is missing the 'Rank' column. Displaying raw data.")
        table_height = (len(leaderboard_df) + 1) * 35
        st.dataframe(
            leaderboard_df, 
            use_container_width=True,
            height=table_height
        )

else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")