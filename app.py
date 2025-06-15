# app.py - Combined Leaderboard and Update Tool

import streamlit as st
import pandas as pd
import gspread
import tournament_scraper # Your module

# --- Page Configuration ---
# This is the only call to set_page_config and it's at the top.
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
        if 'Rank' in leaderboard_df.columns:
            df_to_display = leaderboard_df.set_index('Rank')
            table_height = (len(df_to_display) + 1) * 35
            st.dataframe(df_to_display, use_container_width=True, height=table_height)
        else:
            st.warning("Leaderboard missing 'Rank' column. Displaying raw data.")
            st.dataframe(leaderboard_df, use_container_width=True)
    else:
        st.warning("Leaderboard data could not be loaded or is empty.")


# --- Page 2: Update Tool View ---
def render_update_page():
    """Renders the password-protected update tool."""
    st.title("Update Tournament Data")

    # Password Protection
    if not hasattr(st.secrets, "PASSWORD"):
        st.error("Password is not configured for this app. Please add it to your Streamlit Secrets.")
        return
        
    password = st.text_input("Enter password to access this page", type="password")
    
    if password != st.secrets["PASSWORD"]:
        if password: # Show error only if a password was entered
            st.error("The password you entered is incorrect.")
        else: # Prompt to enter password
            st.info("Please enter the password to continue.")
        return # Stop rendering the rest of the page

    # If password is correct, show the rest of the page
    st.success("Password correct. You can now update a tournament.")
    st.write("---")

    with st.form(key='scraper_form'):
        tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1)
        submit_button = st.form_submit_button(label='Run Scraper and Update Leaderboard')

    if submit_button:
        if not tournament_id:
            st.warning("Please enter a valid Tournament ID.")
        else:
            with st.status(f"Processing tournament {tournament_id}...", expanded=True) as status:
                st.write("Step 1: Extracting Data...")
                tournament_date = tournament_scraper.extract_tournament_date(tournament_id, headers=tournament_scraper.HEADERS)
                if not tournament_date:
                    status.update(label="Error!", state="error", expanded=True)
                    st.error(f"Could not find a valid date for tournament ID {tournament_id}.")
                    return

                st.write(f"Found tournament date: {tournament_date}")
                bracket_url = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
                results_url = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"

                final_standings = tournament_scraper.extract_final_standings(results_url, headers=tournament_scraper.HEADERS)
                match_results = tournament_scraper.extract_match_data(bracket_url, headers=tournament_scraper.HEADERS)

                st.write("Step 2: Calculating Points...")
                if match_results:
                    player_wins = tournament_scraper.calculate_win_counts(match_results)
                    points = tournament_scraper.calculate_tournament_points(match_results, player_wins, final_standings)
                    
                    if points:
                        st.write("Step 3: Updating Master Leaderboard on Google Sheets...")
                        try:
                            creds = dict(st.secrets["gcp_service_account"])
                            tournament_scraper.update_leaderboard_sheet(
                                tournament_date=tournament_date,
                                tournament_points=points,
                                sheet_name=GOOGLE_SHEET_NAME,
                                creds=creds
                            )
                            status.update(label="Process Complete!", state="complete", expanded=False)
                            st.success(f"Leaderboard '{GOOGLE_SHEET_NAME}' updated successfully!")
                            st.info("You can now view the updated standings on the main page.")
                        except Exception as e:
                            status.update(label="Error!", state="error", expanded=True)
                            st.error(f"Failed to update Google Sheets: {e}")
                    else:
                        status.update(label="Warning", state="warning", expanded=True)
                        st.warning("No player points were calculated.")
                else:
                    status.update(label="Warning", state="warning", expanded=True)
                    st.warning("Could not retrieve any valid match results.")


# --- Main Router ---
# Use query params to decide which page to show.
if st.query_params.get("page") == "update":
    render_update_page()
else:
    render_home_page()