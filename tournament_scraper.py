import requests
from bs4 import BeautifulSoup
import csv
import logging
import re
import argparse
from datetime import datetime
import os
import sys
import gspread
import json

# Define a User-Agent header to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

#region --- Data Extraction Functions ---
def extract_tournament_date(tournament_id: int, headers: dict) -> str | None:
    url = f"https://tspool.fi/kisa/{tournament_id}"
    logging.info(f"Fetching tournament date from {url}...")
    finnish_months = {
        "tammikuuta": "01", "helmikuuta": "02", "maaliskuuta": "03",
        "huhtikuuta": "04", "toukokuuta": "05", "kesäkuuta": "06",
        "heinäkuuta": "07", "elokuuta": "08", "syyskuuta": "09",
        "lokakuuta": "10", "marraskuuta": "11", "joulukuuta": "12"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        span_tag = soup.find("span", class_="fw-bold", string="Päivä")
        if span_tag and span_tag.next_sibling:
            date_text = str(span_tag.next_sibling)
            cleaned_text = date_text.strip().lstrip(':').strip()
            parts = cleaned_text.split()
            if len(parts) == 3:
                day = parts[0].replace('.', '')
                month_name = parts[1]
                year = parts[2]
                month_number = finnish_months.get(month_name)
                if month_number:
                    final_date_str = f"{day}.{month_number}.{year}"
                    logging.info(f"Found and formatted tournament date: {final_date_str}")
                    datetime.strptime(final_date_str, '%d.%m.%Y')
                    return final_date_str
        logging.error("Could not find the tournament date using the specific <span> logic.")
        return None
    except (requests.exceptions.RequestException, ValueError, Exception) as e:
        logging.error(f"Failed to extract or validate tournament date: {e}")
        return None

def extract_match_data(url: str, headers: dict) -> list:
    logging.info(f"Fetching match data from {url}...")
    try:
        response = requests.get(url, headers=headers)
        logging.info(f"HTTP Response for {response.url}: Status {response.status_code}, Content-Length: {len(response.content)}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        match_containers = soup.find_all('td', class_='text-md-end')
        if not match_containers:
            logging.warning("Could not find any match container cells ('<td class=\"text-md-end\">').")
            return []
        logging.info(f"Found {len(match_containers)} potential match containers. Processing for completed matches...")
        extracted_data = []
        for container in match_containers:
            home_name_div = container.find('div', class_='home-name')
            away_name_div = container.find('div', class_='away-name')
            home_score_div = container.find('div', class_=re.compile(r'^home-score'))
            away_score_div = container.find('div', class_=re.compile(r'^away-score'))
            if home_name_div and away_name_div and home_score_div and away_score_div:
                player1_full_name = home_name_div.get_text(strip=True)
                player2_full_name = away_name_div.get_text(strip=True)
                player1 = player1_full_name.split('(')[0].strip()
                player2 = player2_full_name.split('(')[0].strip()
                score1 = home_score_div.get_text(strip=True)
                score2 = away_score_div.get_text(strip=True)
                if player1 and player2 and score1 and score2:
                    extracted_data.append({'player1': player1, 'player2': player2, 'score': f"{score1} - {score2}"})
        logging.info(f"Successfully extracted {len(extracted_data)} completed matches.")
        return extracted_data
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during the HTTP request: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred in extract_match_data: {e}")
        return []

def extract_final_standings(url: str, headers: dict, top_n: int = 4) -> list:
    logging.info(f"Fetching final standings from {url}...")
    standings = []
    try:
        response = requests.get(url, headers=headers)
        logging.info(f"HTTP Response for {response.url}: Status {response.status_code}, Content-Length: {len(response.content)}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        rank_texts = soup.find_all(string=re.compile(r"^\d+\.$"))
        if not rank_texts:
            logging.warning("Could not find any text matching the rank pattern (e.g., '1.').")
            return []
        logging.info(f"Found {len(rank_texts)} potential rank strings. Extracting top {top_n} players.")
        for rank_text in rank_texts:
            if len(standings) >= top_n: break
            rank_element = rank_text.parent
            player_div = rank_element.find_next_sibling('div')
            if player_div:
                rank = rank_text.strip()
                player_name = player_div.get_text(strip=True)
                if player_name.strip().startswith('FF '):
                    logging.info(f"Omitting forfeited player from standings: {player_name}")
                    continue
                if player_name:
                    standings.append({'rank': rank, 'player': player_name})
            else:
                logging.warning(f"Found rank text '{rank_text.strip()}' but could not find a player div immediately after it.")
        return standings
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during the HTTP request: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred in extract_final_standings: {e}")
        return []
#endregion

#region --- Data Processing and Export Functions ---
def calculate_win_counts(matches: list) -> dict:
    """Calculates the number of wins for each player, including wins by forfeit."""
    win_counts = {}
    logging.info("Calculating win counts from bracket data...")
    for match in matches:
        try:
            p1_name = match['player1']
            p2_name = match['player2']
            winner = None
            
            # REFACTORED: Determine winner first, then update count once.
            if p1_name.strip().startswith('FF '):
                winner = p2_name
            elif p2_name.strip().startswith('FF '):
                winner = p1_name
            else:
                score_parts = match['score'].split('-')
                if len(score_parts) == 2:
                    score1 = int(score_parts[0].strip())
                    score2 = int(score_parts[1].strip())
                    if score1 > score2:
                        winner = p1_name
                    elif score2 > score1:
                        winner = p2_name
            
            if winner and winner.upper() != 'WO':
                win_counts[winner] = win_counts.get(winner, 0) + 1
        except (ValueError, IndexError):
            continue
    return win_counts

def calculate_tournament_points(matches: list, win_counts: dict, standings: list) -> list:
    logging.info("Calculating detailed points breakdown for the current tournament...")
    all_players = set()
    for match in matches:
        p1 = match['player1']
        p2 = match['player2']
        if p1.upper() != 'WO' and not p1.strip().startswith('FF '): all_players.add(p1)
        if p2.upper() != 'WO' and not p2.strip().startswith('FF '): all_players.add(p2)
    processed_data = []
    for player in all_players:
        participation_points = 30
        wins = win_counts.get(player, 0)
        match_win_points = wins * 5
        top_player_points = 0
        for standing in standings:
            if standing['player'] == player:
                if standing['rank'] == '1.': top_player_points = 2
                elif standing['rank'] == '2.': top_player_points = 3
                elif standing['rank'] == '3.': top_player_points = 4
                break
        final_points = participation_points + match_win_points + top_player_points
        processed_data.append({
            'Player': player,
            'Number of Wins': wins,
            'Points from Wins': match_win_points,
            'Points from Ranking': top_player_points,
            'Total Points': final_points
        })
    return processed_data

def save_tournament_csv(tournament_points: list, final_standings: list, filename: str):
    logging.info(f"Saving detailed tournament report to {filename}...")
    try:
        if not tournament_points:
            logging.warning("No tournament points to save.")
            return
        headers = ['Player', 'Number of Wins', 'Points from Wins', 'Points from Ranking', 'Total Points']
        sorted_data = sorted(tournament_points, key=lambda x: x['Total Points'], reverse=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Top 4 Finishers'])
            if final_standings:
                for standing in final_standings:
                    writer.writerow([f"Rank {standing['rank']}", standing['player']])
            else:
                writer.writerow(['N/A'])
            writer.writerow([])
            writer.writerow(['Player Point Breakdown'])
            dict_writer = csv.DictWriter(csvfile, fieldnames=headers)
            dict_writer.writeheader()
            dict_writer.writerows(sorted_data)
        logging.info(f"Successfully saved detailed report to {filename}.")
    except Exception as e:
        logging.error(f"Error writing detailed tournament CSV to file: {e}")

def update_leaderboard_sheet(tournament_date: str, tournament_points: list, sheet_name: str, creds):
    logging.info(f"Connecting to Google Sheets to update '{sheet_name}'...")
    try:
        if isinstance(creds, str):
            credentials_dict = json.loads(creds)
        else:
            credentials_dict = creds
        gc = gspread.service_account_from_dict(credentials_dict)
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.sheet1
    except Exception as e:
        logging.error(f"Failed to connect to Google Sheets. Check credentials, sheet name, and sharing settings. Error: {e}")
        raise
    
    # Need to import pandas here for this function to work
    import pandas as pd 
    leaderboard_data = [{'Player': p['Player'], 'Total Points': p['Total Points']} for p in tournament_points]
    current_df = pd.DataFrame(leaderboard_data)
    current_df = current_df.rename(columns={'Total Points': tournament_date})
    existing_records = worksheet.get_all_records()
    
    if existing_records:
        total_df = pd.DataFrame(existing_records)
        if tournament_date in total_df.columns:
            logging.warning(f"Tournament date {tournament_date} already exists in Google Sheet. Skipping update.")
            return
        total_df = pd.merge(total_df, current_df, on='Player', how='outer')
    else:
        total_df = current_df
    total_df = total_df.fillna(0)
    
    fixed_cols = ['Player', 'Rank', 'Total Points']
    score_columns = [col for col in total_df.columns if col not in fixed_cols]
    
    date_columns = []
    for col in score_columns:
        try:
            datetime.strptime(str(col), '%d.%m.%Y')
            date_columns.append(str(col))
        except ValueError:
            logging.warning(f"Ignoring non-date column '{col}' during final sorting and display.")
    
    for col in score_columns:
        total_df[col] = pd.to_numeric(total_df[col], errors='coerce').fillna(0).astype(int)
    total_df['Total Points'] = total_df[score_columns].sum(axis=1).astype(int)
    total_df = total_df.sort_values(by='Total Points', ascending=False)
    
    if 'Rank' in total_df.columns:
        total_df = total_df.drop(columns=['Rank'])
    total_df.insert(0, 'Rank', range(1, 1 + len(total_df)))
    
    sorted_date_columns = sorted(date_columns, key=lambda d: datetime.strptime(d, '%d.%m.%Y'))
    final_cols = ['Rank', 'Player'] + sorted_date_columns + ['Total Points']
    total_df = total_df[final_cols]
    try:
        worksheet.clear()
        worksheet.update([total_df.columns.values.tolist()] + total_df.values.tolist())
        logging.info(f"Successfully updated Google Sheet '{sheet_name}'.")
    except Exception as e:
        logging.error(f"Could not write to Google Sheet '{sheet_name}'. Error: {e}")
        raise
#endregion

def main():
    """Main function to parse arguments and run the scraper logic for command-line use."""
    parser = argparse.ArgumentParser(description="Extracts and processes tournament results from tspool.fi.", epilog="Example: python tournament_scraper.py 848")
    parser.add_argument("tournament_id", type=int, help="The integer ID of the tournament (e.g., 848).")
    args = parser.parse_args()
    tournament_id = args.tournament_id
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    tournament_date = extract_tournament_date(tournament_id, headers=HEADERS)
    if not tournament_date:
        logging.error(f"Could not determine tournament date for ID {tournament_id}. Aborting script.")
        sys.exit(1)
    logging.info(f"Processing tournament with ID: {tournament_id}, Date: {tournament_date}")
    BRACKET_URL = f"https://tspool.fi/kisa/{tournament_id}/kaavio/"
    RESULTS_URL = f"https://tspool.fi/kisa/{tournament_id}/tulokset/"
    TOURNAMENT_CSV_FILENAME = f"tournament_{tournament_id}_{tournament_date.replace('.', '-')}.csv"
    final_standings = extract_final_standings(RESULTS_URL, headers=HEADERS, top_n=4)
    if final_standings:
        logging.info("--- Top 4 Final Standings ---")
        for standing in final_standings:
            logging.info(f"Rank {standing['rank']:<3} {standing['player']}")
    match_results = extract_match_data(BRACKET_URL, headers=HEADERS)
    if match_results:
        player_wins = calculate_win_counts(match_results)
        if player_wins:
            sorted_wins = sorted(player_wins.items(), key=lambda item: item[1], reverse=True)
            logging.info("--- Player Win Counts (from bracket) ---")
            for player, wins in sorted_wins:
                win_text = "win" if wins == 1 else "wins"
                logging.info(f"{player:<25} | {wins} {win_text}")
        if final_standings or player_wins:
            current_tournament_points = calculate_tournament_points(match_results, player_wins, final_standings)
            if current_tournament_points:
                save_tournament_csv(current_tournament_points, final_standings, TOURNAMENT_CSV_FILENAME)
                logging.info("Single-tournament CSV saved. To update master leaderboard, use the Streamlit app.")
            else:
                logging.warning("No player points were calculated for this tournament.")
    else:
        logging.warning("Could not retrieve any valid match results from the bracket.")

if __name__ == "__main__":
    main()