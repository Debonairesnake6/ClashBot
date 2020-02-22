import os

from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# API Key for Riot's API from the .env file
api_key = os.getenv('RIOT_API')

# Base URL for requests to the NA server
base_url = 'https://na1.api.riotgames.com'

# Download folder to store large, often accessed json files
download = 'Discord_Bot_Downloads'

# Save the player match history page
player_match_history = None

# Save the champion info page
champion_info = None

# Save the mastery shared information
mastery_shared_info = None

# Save the roll rate information
roll_rate_info = None

# Save the recent champion information
recent_champion_info = None

# Save the clash and ranked information
clash_ranked_info = None

# Save if players couldn't be found
players_not_found = ''
