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
# This remains the one piece of necessary CSS
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
        # Ensure 'Total Points' is numeric for styling
        if 'Total Points' in df.columns:
            df['Total Points'] = pd.to_numeric(df['Total Points'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
        return pd.DataFrame()


# --- Main Page Display ---

st.header("Pocket viikkokisat '25")

leaderboard_df = load_leaderboard_data()

if leaderboard_df is not None and not leaderboard_df.empty:
    
    # --- SPLIT TABLE LOGIC ---

    # Define the columns that will be fixed
    fixed_columns = ['Rank', 'Player']
    
    # Check if required columns exist before proceeding
    if all(col in leaderboard_df.columns for col in fixed_columns):
        
        # Create the two separate dataframes
        df_fixed = leaderboard_df[fixed_columns]
        df_scrollable = leaderboard_df.drop(columns=fixed_columns)

        # Create a layout with two columns
        col1, col2 = st.columns([1, 3]) # Give more space to the scrolling part

        with col1:
            st.write("**Ranking**")
            # Display the fixed columns (Rank and Player)
            st.dataframe(df_fixed, hide_index=True, use_container_width=True)

        with col2:
            st.write("**Points by Tournament**")
            # Display the scrollable columns with a background gradient on 'Total Points'
            st.dataframe(
                df_scrollable.style.background_gradient(cmap='viridis', subset=['Total Points']), 
                hide_index=True, 
                use_container_width=True
            )
    else:
        st.warning("Leaderboard columns 'Rank' and 'Player' not found. Displaying raw table.")
        st.dataframe(leaderboard_df, hide_index=True, use_container_width=True)

else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")