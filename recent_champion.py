import prettytable
import globals

from mastery_shared import highlight_same_champ

# Get globals
base_url = globals.base_url
api_key = globals.api_key


# Get the champion names from the ids
def get_champion_info():

    # Get the champion info page
    champion_info = globals.champion_info

    # Hold champion id values
    champ_ids = {}

    # Get the information for each champ
    for champion in champion_info:

        # Match the champion id to the mastery champion
        for champ_name, _ in champion_info['data'].items():

            # Save the champ id
            champ_ids[champion_info['data'][champ_name]['key']] = champ_name

    # Return the champ ids
    return champ_ids


# Get the champion name
def get_recent_champs(match_history, amount=10):

    # Hold the champion names
    champ_names = {}

    # Get the champion info
    champion_ids = get_champion_info()

    # Loop through each player
    for player_cnt, player in enumerate(match_history):

        # Add player to dictionary
        champ_names[player] = {}

        # Return empty list if the
        if match_history[player] is None:
            return {'Games': [], 'Names': []}

        # Create an array to hold current champions in order
        current_champion_names = []
        current_games_played = []

        if match_history[player] is None:
            print()

        # Loop through each match
        for match_cnt, match in enumerate(match_history[player]['matches']):

            # Grab the champion name
            champion_name = champion_ids[str(match['champion'])]

            # Add a game to the current count of the current champion if it exists
            if champion_name in champ_names[player]:
                champ_names[player][champion_name] = champ_names[player][champion_name] + 1

            # Otherwise add it to the list
            else:
                champ_names[player][champion_name] = 1

        # Create a sorted list
        for champion in champ_names[player]:

            # If list is empty, add to array
            if len(current_champion_names) == 0:
                current_champion_names.append(champion)
                current_games_played.append(champ_names[player][champion])

            # Add to array in order
            else:

                # Grab the new games played for the current champion
                new_games_played = champ_names[player][champion]

                # Loop through each champion played
                for games_played_cnt, old_games_played in enumerate(current_games_played):

                    # Add in current spot if higher than the current
                    if new_games_played > old_games_played:
                        current_champion_names.insert(games_played_cnt, champion)
                        current_games_played.insert(games_played_cnt, new_games_played)

                        # Remove last champ if list was full
                        if len(current_games_played) > amount:
                            current_champion_names.pop(len(current_champion_names) - 1)
                            current_games_played.pop(len(current_games_played) - 1)
                        break

                    # Add to end if not higher than any and list isn't full
                    elif amount > len(current_games_played) == (games_played_cnt + 1):
                        current_champion_names.append(champion)
                        current_games_played.append(new_games_played)
                        break

        # Replace old dictionary with sorted values
        champ_names[player] = {'Names': current_champion_names, 'Games': current_games_played}

    # Return the champion names
    return champ_names


# Format the table accordingly
def format_table(recent_champions):

    # Loop through each player
    for player_name in recent_champions:

        # Loop through each champion
        for games_played_cnt, games_played in enumerate(recent_champions[player_name]['Games']):

            # Get the champ name
            champ_name = recent_champions[player_name]['Names'][games_played_cnt]

            # Over 25 games and shared
            if games_played > 25 and len(champ_name.split(':')) > 1:
                recent_champions[player_name]['Names'][games_played_cnt] = f'2S:{champ_name.split(":")[0]}2S:'

            # Over 25
            elif games_played > 25:
                recent_champions[player_name]['Names'][games_played_cnt] = f'2 :{champ_name.split(":")[0]}2 :'

            # Over 10 and shared
            elif games_played > 10 and len(champ_name.split(':')) > 1:
                recent_champions[player_name]['Names'][games_played_cnt] = f'1S:{champ_name.split(":")[0]}1S:'

            # Over 10
            elif games_played > 10:
                recent_champions[player_name]['Names'][games_played_cnt] = f'1 :{champ_name.split(":")[0]}1 :'

            # If shared champ
            elif len(champ_name.split(':')) > 1:
                recent_champions[player_name]['Names'][games_played_cnt] = f'_S:{champ_name.split(":")[0]}_S:'

    # Return the recent champions
    return recent_champions


# Get the shared champions played
def get_shared_champs(recent_champions):

    # Get the player names
    player_names = [name for name in recent_champions]

    # Highlight if multiple players play the same champion
    for player_name_cnt, player_name in enumerate(recent_champions):

        # Break if last list since already compared
        if player_name_cnt == len(recent_champions):
            break

        # Remove current player from the comparison list
        player_names.remove(player_name)

        # Cycle through each champion the player plays
        for recent_champions_cnt, champion_name in enumerate(recent_champions[player_name]['Names']):

            # Loop through each champion on the list
            for champ_list_cnt, other_player in enumerate(player_names):

                # Check other lists for matches
                for other_list_cnt, other_champion in enumerate(recent_champions[other_player]['Names']):

                    # Remove the brackets for comparison
                    orig_champion = champion_name.split(':')[0]

                    # Remove the brackets for comparison
                    orig_other_champion = other_champion.split(':')[0]

                    # Check if they match
                    if orig_champion == orig_other_champion:

                        # Check if it already matched
                        if 'match' not in champion_name.split(':'):
                            # Adjust the first champ
                            recent_champions[player_name]['Names'][recent_champions_cnt] = f'{champion_name}:match'

                        # Check if it already matched
                        if 'match' not in other_champion.split(':'):
                            # Adjust second champ
                            recent_champions[other_player]['Names'][other_list_cnt] = f'{other_champion}:match'
                            break

    # Return the mastery_list
    return recent_champions


# Get the recent champion table
def recent_champion_table():

    # Create a rr_table
    rc_table = prettytable.PrettyTable()

    # Number of champs to grab
    amount = 10

    # Get the player's match history
    match_history = globals.player_match_history

    # Get the most recent champs
    recent_champions = get_recent_champs(match_history, amount)

    # Get shared champs
    recent_champions = get_shared_champs(recent_champions)

    # Format table
    recent_champions = format_table(recent_champions)

    # Create the table
    for player_name in recent_champions:

        # Check if the player doesn't have 10 different champs played
        if len(recent_champions[player_name]['Names']) < amount:
            
            # Insert nothing into the list
            while len(recent_champions[player_name]['Names']) < amount:
                recent_champions[player_name]['Names'].append('')
        rc_table.add_column(player_name, recent_champions[player_name]['Names'])

    return rc_table
