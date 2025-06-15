# app.py - The Leaderboard Front Page

import streamlit as st
import pandas as pd
import gspread
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
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


# --- Custom CSS for Styling & Hiding UI Elements ---
CUSTOM_CSS = """
<style>
    /* Hide the sidebar navigation completely */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }

    /* ADDED: A container to ensure horizontal scrolling on narrow screens */
    .grid-container {
        width: 100%;
        overflow-x: auto;
    }
    
    /* Remove the default border from AG Grid */
    .ag-root-wrapper {
        border: none !important;
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
    
    bold_cell_style = JsCode("""
    function(params) {
        return {'fontWeight': 'bold'}
    }
    """)
    gb.configure_column("Total Points", cellStyle=bold_cell_style)
    
    # Configure pinned columns
    gb.configure_column("Rank", pinned="left", width=70)
    gb.configure_column("Player", pinned="left", width=180)
    
    gb.configure_grid_options(domLayout='autoHeight')
    
    gridOptions = gb.build()
    
    # --- Display the AG-Grid Table ---

    # ADDED: Wrap the AgGrid call in a div with our custom class
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    
    AgGrid(
        leaderboard_df,
        gridOptions=gridOptions,
        theme='streamlit',
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("Leaderboard data could not be loaded or is empty. An admin can run an update on the /update page.")