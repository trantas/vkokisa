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


# --- Data Loading Function with Caching ---
@st.cache_data(ttl=600) # Cache the data for 10 minutes
def load_leaderboard_data():
    """
    Connects to Google Sheets and fetches the leaderboard data.
    Returns a pandas DataFrame.
    """
    try:
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

st.title("Pocket viikkokisat '25 pisteet")

leaderboard_df = load_leaderboard_data()

if not leaderboard_df.empty:
    # Prepare the dataframe for styling
    df_to_display = leaderboard_df.copy()
    
    # Ensure 'Rank' is set as the index for display but not part of styling
    if 'Rank' in df_to_display.columns:
        df_to_display = df_to_display.set_index('Rank')

    # Identify numeric columns for styling (all except 'Player')
    numeric_cols = [col for col in df_to_display.columns if col != 'Player']
    
    # Apply styles
    st.dataframe(
        df_to_display.style
            .background_gradient(cmap='viridis', subset=['Total Points'])
            .format("{:.0f}", subset=numeric_cols), # Format all numeric columns as integers
        use_container_width=True
    )
else:
    st.warning("Leaderboard data could not be loaded. Please run an update on the 'Update Data' page.")