import streamlit as st
import pandas as pd
import os
import tournament_scraper # Import your custom module

# --- App UI Configuration ---
st.set_page_config(page_title="Tournament Scraper", layout="wide")
st.title("Tournament Data Extractor")
st.write("Enter a tournament ID from tspool.fi to fetch data, calculate points, and update the master leaderboard.")

# --- Main App Logic ---

# Use a form to group the input and button
with st.form(key='scraper_form'):
    tournament_id = st.number_input("Enter Tournament ID:", min_value=1, step=1, value=848)
    submit_button = st.form_submit_button(label='Run Scraper')

if submit_button:
    if not tournament_id:
        st.warning("Please enter a valid tournament ID.")
    else:
        with st.spinner(f"Processing tournament {tournament_id}... Please wait."):
            
            # --- 1. Extract Data ---
            st.write("---")
            st.subheader("Step 1: Extracting Data")

            # Pass the imported HEADERS dictionary to the function
            tournament_date = tournament_scraper.extract_tournament_date(
                tournament_id, 
                headers=tournament_scraper.HEADERS
            )

            if not tournament_date:
                st.error(f"Could not find a valid date for tournament ID {tournament_id}. Aborting.")
            else:
                st.success(f"Found tournament date: {tournament_date}")

                # Construct URLs and call other functions, always passing the headers
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

                # --- 2. Process Data and Save Files ---
                st.subheader("Step 2: Processing and Saving Files")

                if match_results:
                    player_wins = tournament_scraper.calculate_win_counts(match_results)
                    current_tournament_points = tournament_scraper.calculate_tournament_points(match_results, player_wins, final_standings)
                    
                    if current_tournament_points:
                        # Save the single-tournament CSV to the server
                        tournament_scraper.save_tournament_csv(current_tournament_points, final_standings, tournament_csv_filename)
                        st.success(f"Generated report for this tournament: `{tournament_csv_filename}`")

                        # Update the master leaderboard
                        tournament_scraper.update_total_points_csv(tournament_date, current_tournament_points)
                        st.success("Updated master leaderboard file: `total_points.csv`")
                        
                        # --- 3. Display Results and Provide Downloads ---
                        st.write("---")
                        st.subheader("Step 3: View Results")

                        # Display the master leaderboard
                        st.write("Updated Master Leaderboard (`total_points.csv`):")
                        if os.path.exists("total_points.csv"):
                            total_df = pd.read_csv("total_points.csv", skiprows=1)
                            st.dataframe(total_df)

                            # Provide download buttons
                            with open("total_points.csv", "r", encoding="utf-8") as f:
                                st.download_button(
                                   "Download Master Leaderboard (total_points.csv)",
                                   f.read(),
                                   file_name="total_points.csv",
                                   mime="text/csv"
                                )
                            with open(tournament_csv_filename, "r", encoding="utf-8") as f:
                                st.download_button(
                                   f"Download This Tournament's Report ({tournament_csv_filename})",
                                   f.read(),
                                   file_name=tournament_csv_filename,
                                   mime="text/csv"
                                )
                        else:
                            st.warning("`total_points.csv` not found, could not display final leaderboard.")

                    else:
                        st.warning("No player points were calculated for this tournament.")
                else:
                    st.warning("Could not retrieve any valid match results from the bracket.")
