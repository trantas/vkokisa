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
    
    # Check if the required columns exist before proceeding
    if 'Rank' in leaderboard_df.columns and 'Player' in leaderboard_df.columns:
        
        # --- ADDED: Combine 'Rank' and 'Player' into a new 'Ranking' column ---
        leaderboard_df['Ranking'] = leaderboard_df['Rank'].astype(str) + '. ' + leaderboard_df['Player'].astype(str)
        
        # Drop the old, separate columns
        df_to_display = leaderboard_df.drop(columns=['Rank', 'Player'])
        
        # Set the new combined column as the DataFrame's index
        df_to_display = df_to_display.set_index('Ranking')

        # --- Calculate height dynamically ---
        table_height = (len(df_to_display) + 1) * 35
        
        # Display the dataframe with the new calculated height
        st.dataframe(
            df_to_display, 
            use_container_width=True,
            height=table_height
        )
    else:
        # Fallback for if the 'Rank' or 'Player' columns are missing
        st.warning("Leaderboard is missing 'Rank' or 'Player' columns. Displaying raw data.")
        table_height = (len(leaderboard_df) + 1) * 35
        st.dataframe(
            leaderboard_df, 
            use_container_width=True,
            height=table_height
        )

else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")