# app.py - The Leaderboard Front Page

import streamlit as st
import pandas as pd
import gspread
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import tournament_scraper # Your module

# --- Page Configuration ---
# All page settings are now in this single command at the top of the script.
st.set_page_config(
    page_title="Pocket Viikkokisat '25",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="collapsed" # This helps, but CSS below is needed to fully hide it
)

# --- Constant ---
GOOGLE_SHEET_NAME = "pocket viikkokisa leaderboard"


# --- Custom CSS for Styling & Hiding UI Elements ---
CUSTOM_CSS = """
<style>
    /* This robustly hides the sidebar and its hamburger button */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* This is the container for the data grid */
    .ag-root-wrapper {
        border: none !important; /* Remove the default border from AG Grid */
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

# Inject the custom CSS into the page
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.header("Pocket viikkokisat '25")

leaderboard_df = load_leaderboard_data()

if leaderboard_df is not None and not leaderboard_df.empty:

    # --- AG-Grid Configuration ---
    gb = GridOptionsBuilder.from_dataframe(leaderboard_df)
    
    # Style the 'Total Points' column to be bold
    bold_cell_style = JsCode("""
    function(params) {
        return {'fontWeight': 'bold'}
    }
    """)
    gb.configure_column("Total Points", cellStyle=bold_cell_style)
    
    # Configure 'Rank' and 'Player' to be pinned to the left
    gb.configure_column("Rank", pinned="left", width=70)
    gb.configure_column("Player", pinned="left", width=180)
    
    # Configure the grid to auto-size its height to show all rows
    gb.configure_grid_options(domLayout='autoHeight')
    
    gridOptions = gb.build()
    
    # --- Display the AG-Grid Table ---
    AgGrid(
        leaderboard_df,
        gridOptions=gridOptions,
        theme='streamlit',
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False 
    )

else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")