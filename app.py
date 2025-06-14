import streamlit as st
import pandas as pd
import tournament_scraper # Import your custom module

# --- App UI Configuration ---
st.set_page_config(page_title="Tournament Scraper", layout="wide")
st.title("Tournament Data Extractor")
st.write("Enter a tournament ID from tspool.fi to fetch data, calculate points, and update the master leaderboard.")

# --- App Logic ---

# Use a form to group the input and button
with st.form(key='scraper_form'):
    tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1, value=848)
    # IMPORTANT: Change this to the exact name of your Google Sheet
    google_sheet_name = st.text_input("Google Sheet Name:", value="pocket viikkokisa leaderboard")
    submit_button = st.form_submit_button(label='Run Scraper and Update Leaderboard')

if submit_button:
    if not tournament_id or not google_sheet_name:
        st.warning("Please enter a valid Tournament ID and Google Sheet Name.")
    else:
        with st.spinner(f"Processing tournament {tournament_id}..."):
            
            # --- 1. Extraction ---
            st.subheader(f"Step 1: Extracting Data for Tournament {tournament_id}")
            
            tournament_date = tournament_scraper.extract_tournament_date(
                tournament_id, 
                headers=tournament_scraper.HEADERS
            )

            if not tournament_date:
                st.error(f"Could not find a valid date for tournament ID {tournament_id}. Aborting.")
            else:
                st.success(f"Found tournament date: {tournament_date}")
                bracket_url = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
                results_url = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"

                final_standings = tournament_scraper.extract_final_standings(
                    results_url, 
                    headers=tournament_scraper.HEADERS
                )
                match_results = tournament_scraper.extract_match_data(
                    bracket_url, 
                    headers=tournament_scraper.HEADERS
                )

                # --- 2. Processing and Updating ---
                st.subheader("Step 2: Calculating Points and Updating Leaderboard")
                if match_results:
                    player_wins = tournament_scraper.calculate_win_counts(match_results)
                    current_tournament_points = tournament_scraper.calculate_tournament_points(
                        match_results, player_wins, final_standings
                    )
                    
                    if current_tournament_points:
                        try:
                            # This is where the magic happens
                            tournament_scraper.update_leaderboard_sheet(
                                tournament_date=tournament_date,
                                tournament_points=current_tournament_points,
                                sheet_name=google_sheet_name,
                                creds_dict=st.secrets["gcp_service_account"]
                            )
                            st.success(f"Master leaderboard '{google_sheet_name}' updated successfully!")

                        except Exception as e:
                            st.error(f"Failed to update Google Sheets leaderboard. Please check configuration.")
                            st.error(f"Error details: {e}")
                    else:
                        st.warning("No player points were calculated for this tournament.")
                else:
                    st.warning("Could not retrieve any valid match results from the bracket.")
