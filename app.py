import streamlit as st
# Assuming your main script is now a module named 'tournament_scraper'
import tournament_scraper 
import pandas as pd

st.title("Tournament Data Extractor")
st.write("Enter a tournament ID to fetch data and generate reports.")

# Simple number input for the ID
tournament_id = st.number_input("Enter Tournament ID", min_value=1, step=1, value=848)

if st.button("Run Script"):
    if tournament_id:
        with st.spinner(f"Processing tournament {tournament_id}... Please wait."):
            # 1. Extract all data by calling your existing functions
            tournament_date = tournament_scraper.extract_tournament_date(tournament_id)
            if not tournament_date:
                st.error(f"Could not find a valid date for tournament ID {tournament_id}.")
            else:
                bracket_url = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
                results_url = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"

                final_standings = tournament_scraper.extract_final_standings(results_url)
                match_results = tournament_scraper.extract_match_data(bracket_url)

                if match_results:
                    # 2. Process the data
                    player_wins = tournament_scraper.calculate_win_counts(match_results)
                    points_data = tournament_scraper.calculate_tournament_points(match_results, player_wins, final_standings)

                    # 3. Display results directly in the app
                    st.success(f"Successfully processed tournament from {tournament_date}!")
                    
                    st.subheader("Final Points Summary")
                    df = pd.DataFrame(points_data).sort_values(by='Total Points', ascending=False)
                    st.dataframe(df)

                    # 4. Provide a download link for the CSV
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Tournament Results as CSV",
                        data=csv_data,
                        file_name=f"tournament_{tournament_id}_{tournament_date}.csv",
                        mime='text/csv',
                    )
                else:
                    st.warning("Could not retrieve any valid match results from the bracket.")
    else:
        st.warning("Please enter a valid tournament ID.")