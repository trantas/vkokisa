# app.py - Combined Leaderboard and Update Tool

import streamlit as st
import pandas as pd
import gspread
import tournament_scraper # Your module
import sys

# --- Page Configuration ---
st.set_page_config(
    page_title="Pocket Viikkokisat '25",
    page_icon="🎱",
    layout="wide"
)

# --- Constant ---
GOOGLE_SHEET_NAME = "pocket viikkokisa leaderboard"

# --- Data Loading Function (for Homepage) ---
@st.cache_data(ttl=600)
def load_leaderboard_data():
    """
    Connects to Google Sheets and fetches the leaderboard data.
    """
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("GCP service account secret is not configured in app settings.")
            return None
        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.sheet1
        df = pd.DataFrame(worksheet.get_all_records())
        # Ensure 'Total Points' is numeric
        if 'Total Points' in df.columns:
            df['Total Points'] = pd.to_numeric(df['Total Points'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
        return pd.DataFrame()


# --- Page 1: Homepage / Leaderboard View ---
def render_home_page():
    """Renders the main leaderboard display."""
    st.header("Pocket viikkokisat '25")
    
    leaderboard_df = load_leaderboard_data()

    if leaderboard_df is not None and not leaderboard_df.empty:
        if 'Rank' in leaderboard_df.columns and 'Player' in leaderboard_df.columns:
            
            leaderboard_df['Ranking'] = leaderboard_df['Rank'].astype(str) + '. ' + leaderboard_df['Player'].astype(str)
            df_to_display = leaderboard_df.drop(columns=['Rank', 'Player'])
            cols = df_to_display.columns.tolist()
            cols = ['Ranking'] + [col for col in cols if col != 'Ranking']
            df_to_display = df_to_display[cols]
            df_to_display = df_to_display.set_index('Ranking')
            
            table_height = (len(df_to_display) + 1) * 35
            
            st.dataframe(
                df_to_display, 
                use_container_width=True,
                height=table_height
            )
        else:
            st.warning("Leaderboard is missing 'Rank' or 'Player' columns. Displaying raw data.")
            st.dataframe(leaderboard_df, use_container_width=True)
    else:
        st.warning("Leaderboard data could not be loaded or is empty.")


# --- Page 2: Update Tool View ---
def render_update_page():
    """Renders the password-protected update tool."""
    st.title("Update Tournament Data")

    # --- MODIFIED: Use session state for password check ---
    
    # Initialize session state
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False

    def password_form():
        """Form to check for password."""
        with st.form("password_form"):
            password = st.text_input("Enter password to access this page", type="password")
            submitted = st.form_submit_button("Enter")
            if submitted:
                if hasattr(st.secrets, "PASSWORD") and password == st.secrets["PASSWORD"]:
                    st.session_state.password_correct = True
                    # Use experimental_rerun for wider compatibility
                    st.experimental_rerun() 
                else:
                    st.error("The password you entered is incorrect.")

    # If password is not correct, show the login form and stop.
    if not st.session_state.password_correct:
        password_form()
        return

    # If password IS correct, show the main update tool.
    st.success("Authenticated.")
    st.write("---")

    with st.form(key='scraper_form'):
        tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1)
        # MODIFIED: Button text
        submit_button = st.form_submit_button(label='Update tournament points')

    if submit_button:
        if not tournament_id:
            st.warning("Please enter a valid Tournament ID.")
        else:
            try:
                with st.spinner(f"Processing tournament {tournament_id}..."):
                    # Step 1: Extract Data
                    tournament_date = tournament_scraper.extract_tournament_date(tournament_id, headers=tournament_scraper.HEADERS)
                    if not tournament_date:
                        raise ValueError(f"Could not find a valid date for tournament ID {tournament_id}.")

                    bracket_url = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
                    results_url = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"
                    
                    final_standings = tournament_scraper.extract_final_standings(results_url, headers=tournament_scraper.HEADERS)
                    match_results = tournament_scraper.extract_match_data(bracket_url, headers=tournament_scraper.HEADERS)
                    
                    if not match_results:
                        st.warning("Could not retrieve any valid match results from the bracket.")
                        return

                    # Step 2: Calculate Points
                    player_wins = tournament_scraper.calculate_win_counts(match_results)
                    points = tournament_scraper.calculate_tournament_points(match_results, player_wins, final_standings)

                    if not points:
                        st.warning("No player points were calculated for this tournament.")
                        return
                    
                    # Step 3: Update Leaderboard
                    creds = dict(st.secrets["gcp_service_account"])
                    tournament_scraper.update_leaderboard_sheet(
                        tournament_date=tournament_date,
                        tournament_points=points,
                        sheet_name=GOOGLE_SHEET_NAME,
                        creds=creds
                    )
                
                st.success(f"Leaderboard '{GOOGLE_SHEET_NAME}' updated successfully!")
                
                # ADDED: Link back to the main page
                st.markdown("[Return to Homepage](/)")

            except Exception as e:
                st.error(f"An error occurred during processing:")
                st.error(e)


# --- Main Router ---
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["home"])[0]

if page == "update":
    render_update_page()
else:
    render_home_page()