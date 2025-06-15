# pages/1_Update_Data.py - The Scraper Tool Page

import streamlit as st
import tournament_scraper # Your module

st.set_page_config(page_title="Update Data", layout="centered")
st.title("Update Tournament Data")

# --- Password Protection ---
def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Check if the password secret is configured
    if not hasattr(st.secrets, "PASSWORD"):
        st.error("Password is not configured for this app. Please add it to your Streamlit Secrets.")
        return False
        
    password = st.text_input("Enter password to access this page", type="password")
    
    if not password: # Don't show the form if password hasn't been entered
        st.warning("Please enter the password to continue.")
        return False
    elif password == st.secrets["PASSWORD"]:
        return True
    else:
        st.error("The password you entered is incorrect.")
        return False

# --- Main App Logic ---
# The rest of the page is only shown if the password is correct
if check_password():

    st.write("---")
    st.write("Use this page to process a new tournament and update the master leaderboard.")

    # --- Constant ---
    GOOGLE_SHEET_NAME = "Your Google Sheet Name Here"

    with st.form(key='scraper_form'):
        tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1)
        submit_button = st.form_submit_button(label='Run Scraper and Update Leaderboard')

    if submit_button:
        # Check for GCP secrets before running
        if not hasattr(st.secrets, "gcp_service_account"):
            st.error("Error: The `[gcp_service_account]` table is not configured in your Streamlit Secrets.")
        elif not tournament_id:
            st.warning("Please enter a valid Tournament ID.")
        else:
            # This container will show the log of operations
            with st.status(f"Processing tournament {tournament_id}...", expanded=True) as status:
                
                st.write("Step 1: Extracting Data...")
                tournament_date = tournament_scraper.extract_tournament_date(
                    tournament_id, 
                    headers=tournament_scraper.HEADERS
                )

                if not tournament_date:
                    status.update(label="Error!", state="error", expanded=True)
                    st.error(f"Could not find a valid date for tournament ID {tournament_id}.")
                else:
                    st.write(f"Found tournament date: {tournament_date}")
                    bracket_url = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
                    results_url = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"
                    tournament_csv_filename = f"tournament_{tournament_id}_{tournament_date.replace('.', '-')}.csv"

                    final_standings = tournament_scraper.extract_final_standings(
                        results_url, 
                        headers=tournament_scraper.HEADERS
                    )
                    match_results = tournament_scraper.extract_match_data(
                        bracket_url, 
                        headers=tournament_scraper.HEADERS
                    )

                    st.write("Step 2: Calculating Points...")
                    if match_results:
                        player_wins = tournament_scraper.calculate_win_counts(match_results)
                        current_tournament_points = tournament_scraper.calculate_tournament_points(
                            match_results, player_wins, final_standings
                        )
                        
                        if current_tournament_points:
                            st.write("Step 3: Updating Master Leaderboard on Google Sheets...")
                            try:
                                creds_dict = dict(st.secrets["gcp_service_account"])
                                tournament_scraper.update_total_points_csv(
                                    tournament_date=tournament_date,
                                    tournament_points=current_tournament_points,
                                    sheet_name=GOOGLE_SHEET_NAME,
                                    creds=creds_dict
                                )
                                status.update(label="Process Complete!", state="complete", expanded=False)
                                st.success(f"Leaderboard '{GOOGLE_SHEET_NAME}' updated successfully!")
                                st.info("You can now view the updated standings on the main page.")

                            except Exception as e:
                                status.update(label="Error!", state="error", expanded=True)
                                st.error(f"Failed to update Google Sheets leaderboard.")
                                st.error(f"Details: {e}")
                        else:
                            status.update(label="Warning", state="warning", expanded=True)
                            st.warning("No player points were calculated for this tournament.")
                    else:
                        status.update(label="Warning", state="warning", expanded=True)
                        st.warning("Could not retrieve any valid match results from the bracket.")