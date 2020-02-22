import prettytable
import globals

from mastery_shared import get_json
from mastery_shared import get_summoner_by_name

# Get globals
base_url = globals.base_url
api_key = globals.api_key


# Calculate the role for each player
def calculate_roles(match_history):

    # Hold the player roles
    player_roles = {}

    # Get games played in each role
    for player_name, player_matches in match_history.items():

        # Add the player to the dictionary
        player_roles[player_name] = {'top': 0,
                                     'jng': 0,
                                     'mid': 0,
                                     'bot': 0,
                                     'sup': 0}

        # Loop through all of the matches
        for match in player_matches['matches']:

            # Check if solo lane
            if match['role'] == 'SOLO':

                # If top
                if match['lane'] == 'TOP':
                    player_roles[player_name]['top'] = player_roles[player_name]['top'] + 1

                # If mid
                elif match['lane'] == 'MID':
                    player_roles[player_name]['mid'] = player_roles[player_name]['mid'] + 1

            # If jng
            elif match['role'] == 'NONE':
                if match['lane'] == 'JUNGLE':
                    player_roles[player_name]['jng'] = player_roles[player_name]['jng'] + 1

            # If bot
            elif match['role'] == 'DUO_CARRY':
                if match['lane'] == 'BOTTOM':
                    player_roles[player_name]['bot'] = player_roles[player_name]['bot'] + 1

            # If sup
            elif match['role'] == 'DUO_SUPPORT':
                if match['lane'] == 'BOTTOM':
                    player_roles[player_name]['sup'] = player_roles[player_name]['sup'] + 1

            # Just add based on one criteria
            else:

                # If top
                if match['lane'] == 'TOP':
                    player_roles[player_name]['top'] = player_roles[player_name]['top'] + 1

                # If mid
                elif match['lane'] == 'MID':
                    player_roles[player_name]['mid'] = player_roles[player_name]['mid'] + 1

                # If jng
                elif match['lane'] == 'JUNGLE':
                    player_roles[player_name]['jng'] = player_roles[player_name]['jng'] + 1

                # If bot
                elif match['role'] == 'DUO_CARRY':
                    player_roles[player_name]['bot'] = player_roles[player_name]['bot'] + 1

                # If sup
                elif match['role'] == 'DUO_SUPPORT':
                    player_roles[player_name]['sup'] = player_roles[player_name]['sup'] + 1

                # If jng
                elif match['role'] == 'DUO':
                    player_roles[player_name]['bot'] = player_roles[player_name]['bot'] + 1

    # Get percentage of each role
    for player_name, role_list in player_roles.items():

        # Hold total games calculated
        total_games = 0

        # Grab games from each position
        for _, games_played in role_list.items():
            total_games += games_played

        # Change each number into a percentage
        for role, games_played in role_list.items():
            player_roles[player_name][role] = int(games_played / total_games * 100)

    # Calculate roles
    return player_roles


# Get the match history for the given player
def get_match_history(player_list):

    # Get the encrypted summoner id
    account_id = get_summoner_by_name(player_list)

    # Create holder for match history
    match_history = {}

    # Call to riot's api for each player (Not ARAM/Poro King)
    '''
    Norms Draft: 400
    Clash: 700
    Ranked Solo: 420
    Ranked Flex: 440
    Norms Blind: 430
    Poro King: 920
    Aram: 450
    '''
    for player in account_id:
        match_history[player] = get_json(f'{base_url}/lol/match/v4/matchlists/by-account/'
                                         f'{account_id[player]["accountId"]}?api_key={api_key}'
                                         f'&queue=400&queue=700&queue=420&queue=440&queue=430')

    # Save the match history for other tables
    globals.player_match_history = match_history

    # Return the match history
    return match_history


# Format array for the table
def table_format(player_roles):

    # Loop through each player
    for player_name, roll_list in player_roles.items():

        # Loop through each role
        for role_name, games_played in roll_list.items():

            # If high games played
            if games_played > 60:
                player_roles[player_name][role_name] = f'60:{player_roles[player_name][role_name]}60:'

            # If medium games played
            elif games_played > 30:
                player_roles[player_name][role_name] = f'30:{player_roles[player_name][role_name]}30:'

    return player_roles


# Get the odds a player will play a role
def get_player_roles(player_list):

    # Get the match history
    match_history = get_match_history(player_list)

    # Calculate the roles
    player_roles = calculate_roles(match_history)

    # Return array of odds
    return player_roles


# Get the role rate table
def role_rate_table(player_list):

    # Create a rr_table
    rr_table = prettytable.PrettyTable()
    rr_table.field_names = ['Player', 'Top', 'Jng', 'Mid', 'Bot', 'Sup']

    # Get positional amounts for each player
    player_roles = get_player_roles(player_list)

    # Format rr_table
    player_roles = table_format(player_roles)

    # Add each player to the rr_table
    for player_name in player_roles:
        rr_table.add_row([f'{player_name}',
                          player_roles[player_name]['top'],
                          player_roles[player_name]['jng'],
                          player_roles[player_name]['mid'],
                          player_roles[player_name]['bot'],
                          player_roles[player_name]['sup']])

    # Return the rr_table
    return rr_table
