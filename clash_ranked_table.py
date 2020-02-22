import prettytable
import globals
import sys

from mastery_shared import get_json
from mastery_shared import get_summoner_by_name
from recent_champion import get_recent_champs, get_shared_champs, format_table
from urllib.error import HTTPError

base_url = globals.base_url
api_key = globals.api_key


# Get the clash and ranked match history
def get_match_history(player_list):

    # Get the encrypted summoner id
    account_id = get_summoner_by_name(player_list)

    # Create holder for match history
    match_history = {}

    # Call to riot's api for clash and ranked
    '''
    Clash: 700
    Ranked Solo: 420
    Ranked Flex: 440
    '''
    for player in account_id:
        try:
            match_history[player] = get_json(f'{base_url}/lol/match/v4/matchlists/by-account/'
                                             f'{account_id[player]["accountId"]}?api_key={api_key}'
                                             f'&queue=700&queue=420&queue=440')

        # Catch if the player have never played that mode
        except HTTPError:
            print(f'Player has not played Clash/Ranked: {player}', file=sys.stderr)
            match_history[player] = None

    # Save the match history for other tables
    globals.player_match_history = match_history

    # Return the match history
    return match_history


# Get the clash and ranked champs for each player
def get_clash_ranked(player_list):

    # Get the match history
    match_history = get_match_history(player_list)

    # Get most common champs in last 100 games
    clash_ranked_champs = get_recent_champs(match_history)

    # Get shared champs
    clash_ranked_champs = get_shared_champs(clash_ranked_champs)

    # Format table
    clash_ranked_champs = format_table(clash_ranked_champs)

    # Return the clash ranked table
    return clash_ranked_champs


# Get the clash ranked table
def clash_ranked_table(player_list=False):

    # Create a cr_table
    cr_table = prettytable.PrettyTable()

    # Get the clash and ranked champions
    clash_ranked = get_clash_ranked(player_list)

    # Create the table
    for player_name in clash_ranked:

        # Check if the player doesn't have 10 different champs played
        if len(clash_ranked[player_name]['Names']) < 10:

            # Insert nothing into the list
            while len(clash_ranked[player_name]['Names']) < 10:
                clash_ranked[player_name]['Names'].append('')
        cr_table.add_column(player_name, clash_ranked[player_name]['Names'])

    return cr_table
