import requests
import os
from dotenv import load_dotenv

import base64

API_ENDPOINT = 'https://discord.com/api/v8'
CLIENT_ID = '731973634519728168'
CLIENT_SECRET = 'n-ZsqL0fFh64jxUQTu3oxZ2P19dHsZUX'

def get_token():
  data = {
    'grant_type': 'client_credentials',
    'scope': 'identify connections'
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  r = requests.post(f'{API_ENDPOINT}/oauth2/token', data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
  r.raise_for_status()
  return r.json()


# Load environment variables
load_dotenv()

application_id = f'731973634519728168'
guild_id = f'143193976709578752'
command_id = '829525225950937119'
# url = f"https://discord.com/api/v8/applications/{application_id}/guilds/{guild_id}/commands"
url = f"https://discord.com/api/v8/applications/{application_id}/guilds/{guild_id}/commands/{command_id}"

json = {
    "name": "clash",
    "description": "Gather information about a player's clash team",
    "options": [
        {
            "name": "player_name",
            "description": "A name of a single player on a clash team",
            "type": 3,
            "required": True
        }
    ]
}

headers = {
    "Authorization": f"Bot {os.getenv('DISCORD_TOKEN')}"
}

# r = requests.post(url, headers=headers, json=json)
r = requests.delete(url, headers=headers, json=json)

if r.status_code not in [201, 204]:
    print('Success!')
else:
    print(f'{r.status_code=}')
    print(f'{r.text=}')
    print()