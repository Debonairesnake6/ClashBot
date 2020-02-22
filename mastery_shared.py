import os
import prettytable
import urllib.request
import json
import sys
import time
import globals

# Get environment variables
api_key = globals.api_key
base_url = globals.base_url
download = globals.download


# Return just the champion name
def get_champ_name(champion):

    # Return just the champion name
    return champion.split(':')[0]


# Get top played champs for each player
def get_top_champs(player_champs, amount):
    # Placeholder for each player's list
    mastery_list = []

    # Keep track of loops
    champion_cnt = 0

    # Loop through each player
    for player_name, player_dict in player_champs.items():

        # Hold current champion list
        current_list = []

        # Loop through each player's champions
        for champion_name, _ in player_dict.items():

            # Add current champion to the dictionary
            current_list.append(champion_name)

            # Increase the loop count
            champion_cnt += 1

            # Break after specified amount
            if champion_cnt == amount:
                champion_cnt = 0
                break

        # Hold the total mastery points for top
        top_mastery_total = 0

        # Get the total mastery points for the top 10
        for champion_name in current_list:
            # Add the mastery for the current champ
            top_mastery_total += player_champs[player_name][champion_name]['mastery']

        # Check if champions have a large portion of the total amount
        for champion_name in current_list:

            # Check if the mastery points are a large percentage (15% for 10) of the total for top champs
            if player_champs[player_name][champion_name]['mastery'] > int(top_mastery_total / amount * 1.5):

                # Add brackets around the champion name for discord highlighting
                current_list[current_list.index(champion_name)] = f'{champion_name}:top'

        mastery_list.append(current_list)

    # Return the mastery_list
    return mastery_list


# Highlight the same champ being used
def highlight_same_champ(mastery_list):

    # Highlight if multiple players play the same champion
    for mastery_list_cnt, champ_list in enumerate(mastery_list):

        # Break if last list since already compared
        if mastery_list_cnt == len(champ_list):
            break

        # Loop through each champion on the list
        for champ_list_cnt, champion in enumerate(champ_list):

            # Remove the brackets for comparison
            orig_champion = get_champ_name(champion)

            # Check other lists for matches
            for other_list_cnt, other_list in enumerate(mastery_list[mastery_list_cnt + 1:]):

                # Loop through each champion
                for other_champ_cnt, other_champion in enumerate(other_list):

                    # Remove the brackets for comparison
                    orig_other_champion = get_champ_name(other_champion)

                    # Check if they match
                    if orig_champion == orig_other_champion:

                        # Check if it already matched
                        if 'match' not in champion.split(':'):
                            # Adjust the first champ
                            mastery_list[mastery_list_cnt][champ_list_cnt] = f'{champion}:match'

                        # Check if it already matched
                        if 'match' not in other_champion.split(':'):
                            # Adjust second champ
                            mastery_list[mastery_list_cnt + other_list_cnt + 1][other_champ_cnt] = \
                                f'{other_champion}:match'

    # Return the mastery_list
    return mastery_list


# Remove champions not played recently
def remove_old_champs(mastery_list, player_champs, player_names):
    # Loop through each player
    for champion_list_cnt, champion_list in enumerate(mastery_list):

        # Loop through each champion in the list
        for champion_cnt, champion in enumerate(champion_list):

            # Check if the current champion is highlighted
            if len(champion.split(':')) > 0:

                # Check the recent play time of the champion for the player
                last_played = player_champs[player_names[champion_list_cnt]][champion.split(':')[0]]['last_play_time']

                # Get the current time
                current_time = int(round(time.time() * 1000))

                # Find the difference in time
                time_since = current_time - last_played

                # Check if played more than 30 days ago
                if time_since > (86400000 * 30):
                    # Remove highlighting for champ not played recently
                    mastery_list[champion_list_cnt][champion_cnt] = champion.split(':')[0]

    # Return the mastery list
    return mastery_list


# Add highlighting to the table
def insert_highlighting(mastery_list):
    # Cycle through each player
    for champ_list_cnt, champ_list in enumerate(mastery_list):

        # Cycle through each champion
        for champion_cnt, champion in enumerate(champ_list):

            # Get just the champ name
            champ_name = champion.split(':')[0]

            # Check if no highlighting needed
            if len(champion.split(':')) == 1:
                continue

            # Check if top and match
            elif len(champion.split(':')) == 3:

                # Add highlighting
                mastery_list[champ_list_cnt][champion_cnt] = f'HS:{champ_name}HS:'

            # Check if top
            elif champion.split(':')[1] == 'top':

                # Add highlighting
                mastery_list[champ_list_cnt][champion_cnt] = f'H :{champ_name}H :'

            # Check if match
            elif champion.split(':')[1] == 'match':

                # Add highlighting
                mastery_list[champ_list_cnt][champion_cnt] = f'S :{champ_name}S :'

    # Return the mastery list
    return mastery_list


# Create a table of the top mastery for each player
def get_mastery_table(player_champs, amount):
    # Create the table
    mastery_table = prettytable.PrettyTable()

    # Placeholder for table titles
    mastery_table_titles = []

    # Add each player to the title
    for player_name, _ in player_champs.items():
        mastery_table_titles.append(player_name)

    # Get each player's top 10
    mastery_list = get_top_champs(player_champs, amount)

    # Highlight common champions
    mastery_list = highlight_same_champ(mastery_list)

    # Remove if not played recently
    mastery_list = remove_old_champs(mastery_list, player_champs, mastery_table_titles)

    # Add correct highlighting
    mastery_list = insert_highlighting(mastery_list)

    # Add the champions to the table
    for cnt, champion_list in enumerate(mastery_list):
        mastery_table.add_column(mastery_table_titles[cnt], champion_list)

    # Return the table
    return mastery_table


# Get the JSON file from the url
def get_json(url):
    # Open the url
    with urllib.request.urlopen(url) as url_request:
        # Save the JSON to the version placeholder
        response = json.loads(url_request.read().decode())

    # Return the response
    return response


# Get the current patch version
def get_version():
    # Get the current version
    version = get_json('http://ddragon.leagueoflegends.com/api/versions.json')

    # Return the current version
    return version[0]


# Get the champion info
def get_champion_info(version):
    # Create downloads folder if it doesn't exist
    for (_, dir_names, _) in os.walk(os.getcwd()):

        # Check for the downloads folder
        if download not in dir_names:
            # Create the folder
            os.makedirs(download)

        # Break after current folder is searched
        break

    # Check if the most recent version matches the saved one
    for (_, _, filenames) in os.walk(f'{os.getcwd()}\\{download}'):

        # Loop through each file
        for filename in filenames:

            try:
                # Check if the file is the one we are looking for
                if filename.split('_')[1] == 'Champion' and filename.split('_')[2] == 'Info.json':

                    # Check if the version number is correct
                    if filename.split('_')[0] == version:
                        # Load the file
                        with open(f'{download}\\{filename}', 'r') as champion_file:
                            data = champion_file.read()

                        # Covert to json
                        champion_info = json.loads(data)

                        # Save the champion info page
                        globals.champion_info = champion_info

                        # Return the json file
                        return champion_info

            # If the filename does have have 2 underscores move to the next
            except IndexError:
                pass

    # If the file is not saved then grab it
    champion_info = get_json(f'http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json')

    # Saved the file for future use
    with open(f'{download}\\{version}_Champion_Info.json', 'w') as champion_file:
        json.dump(champion_info, champion_file)

    # Save the champion info page
    globals.champion_info = champion_info

    # Return the champion information page
    return champion_info


# Get summoner champ information
def get_player_champs(player_list, encrypted_player, version):
    # Place holder for the champions each player plays
    player_champs = {}

    # Get the champion info page
    champion_info = get_champion_info(version)

    # Cycle through each player
    for cnt, player_name in enumerate(player_list):

        # Add dictionary entry for the current player
        player_champs[player_name] = {}

        # Get the mastery information for the current player
        mastery = get_json(f'{base_url}/lol/champion-mastery/v4/champion-masteries/by-summoner/'
                           f'{encrypted_player[player_name]["id"]}?api_key={api_key}')

        # Get the information for each champ
        for champion in mastery:

            # Match the champion id to the mastery champion
            for _, champ_id in champion_info['data'].items():
                if int(champ_id['key']) == champion['championId']:
                    # Add key for current champion
                    player_champs[player_name][champ_id['id']] = {'mastery': champion['championPoints'],
                                                                  'last_play_time': champion['lastPlayTime']}
                    break

    # Return the array of champions and last play time
    return player_champs


# Get the encrypted player id
def get_summoner_by_name(player_list):

    # Hold the encrypted player id for each summoner
    summoner_list = {}

    # Cycle through each player
    for player_name in player_list:

        try:
            # URL encode the player name
            player_name_url = urllib.parse.quote(player_name)

            # Url to get the information for the specific summoner
            summoner_info = get_json(
                f'{base_url}/lol/summoner/v4/summoners/by-name/{player_name_url}?api_key={api_key}')

            # Add the current encrypted ID to the list
            summoner_list[player_name] = {'id': summoner_info['id'],
                                          'accountId': summoner_info['accountId']}

        # If the player cannot be found
        except urllib.error.HTTPError as e:
            print(f'Could not find player: {player_name}', file=sys.stderr)
            print(f'{e}')
            globals.players_not_found += f'{player_name}, '

    # Return the encrypted player id
    return summoner_list


# Remove players not found from the player list
def remove_not_found(player_list, encrypted_player):

    # Loop through each player
    for player_name in player_list:

        if player_name not in encrypted_player:

            player_list.remove(player_name)

    return player_list


# Get a mastery table for each player
def mastery_shared_table(player_list):

    # Get the current version of the game
    version = get_version()

    # Get the encrypted account id for each player
    encrypted_player = get_summoner_by_name(player_list)

    # Remove players not found
    player_list = remove_not_found(player_list, encrypted_player)

    # Get summoner mastery information
    player_champs = get_player_champs(player_list, encrypted_player, version)

    # Create table of top 10 mastery champions
    amount = 10
    mastery_table = get_mastery_table(player_champs, amount)
    return mastery_table
