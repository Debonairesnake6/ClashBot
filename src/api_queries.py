"""
This file will run all of the API queries for each access during the processing of each of the tables
"""

import json
import os
import urllib.request
import operator

from dotenv import load_dotenv
from urllib.error import HTTPError
from role_rate import RoleRate

# Load environment variables
load_dotenv()


class APIQueries:
    """
    Run and save each API query
    """
    def __init__(self, player_list: list, clash_api: bool = False):
        """
        Run and save each API query

        :param player_list: List of each player to process
        :param clash_api: If using the clash api the player list should only contain a single player
        """
        # Placeholder variables
        self.response = None
        self.champion_info = None
        self.clash_team_id = None
        self.clash_team_members = None
        self.clash_api = clash_api
        self.titles = []
        self.player_list = player_list
        self.base_url = 'https://na1.api.riotgames.com'
        self.api_key = f'?api_key={os.getenv("RIOT_API")}'
        self.errors = {
            'player_not_found': [],
            'no_ranked_clash': [],
            'no_match_history': [],
            'no_ranked_info': [],
            'no_clash_team': [],
            'no_champion_mastery': []
        }
        self.queue_id = {
            'norm_draft': '&queue=400',
            'clash': '&queue=700',
            'ranked_solo': '&queue=420',
            'ranked_flex': '&queue=440',
            'norm_blind': '&queue=430',
            'poro_king': '&queue=920',
            'aram': '&queue=450'
        }
        self.queue_tiers = {
            'CHALLENGER': 0,
            'GRANDMASTER': 1,
            'MASTER': 2,
            'DIAMOND': 3,
            'PLATINUM': 4,
            'GOLD': 5,
            'SILVER': 6,
            'BRONZE': 7,
            'IRON': 8
        }
        self.queue_ranks = {
            'I': 0,
            'II': 1,
            'III': 2,
            'IV': 3
        }

        # Store the information from the queries
        self.player_information = {}

        # Grab information based on the given player list
        if self.clash_api:
            self.use_clash_api()
        else:
            self.process_each_player()

    def use_clash_api(self):
        """
        Use the clash API based on the given player
        """
        self.process_each_player()
        for player in self.player_information:
            self.player_list = [player]
        self.get_clash_team_id()
        if len(self.errors['no_clash_team']) == 0:
            self.process_each_clash_member()
            self.get_locked_in_position()
            self.change_order_by_position()

    def change_order_by_position(self):
        """
        Reorder the dictionary based on the position each player plays
        """
        new_order, roles_found = self.get_new_order()
        new_order = self.place_filled_players(new_order, roles_found)
        self.switch_to_new_order(new_order)
        self.fix_titles()

    def get_new_order(self):
        """
        Get the new order based on the positions locked in
        """
        new_order = []
        roles_found = []
        for position in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
            for player in self.player_information:
                if self.player_information[player]['position'] == position:
                    new_order.append(player)
                    roles_found.append(position)
        return new_order, roles_found

    def place_filled_players(self, new_order: list, roles_found: list):
        """
        Add players into the new order who locked in as fill

        :param new_order: Player names in order of position
        :param roles_found: Roles successfully grabbed
        """
        if len(roles_found) == len(self.player_information):
            return new_order
        elif len(roles_found) == len(self.player_information) - 1:
            for cnt, position in enumerate(['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']):
                if position not in roles_found:
                    new_order.insert(cnt, [player for player in self.player_information if player not in new_order][0])
                    return new_order
        else:
            role_calc = RoleRate(self, just_using_functions=True)
            missing_players = {}
            missing_roles = [role for role in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'] if role not in roles_found]
            for player in [player for player in self.player_information if player not in new_order]:
                role_calc.match_history = self.player_information[player]['all_match_history']
                role_calc.calculate_all_roles(player)
                missing_players[player] = {'TOP': role_calc.player_roles['TOP'],
                                           'JUNGLE': role_calc.player_roles['JUNGLE'],
                                           'MIDDLE': role_calc.player_roles['MIDDLE'],
                                           'BOTTOM': role_calc.player_roles['BOTTOM'],
                                           'UTILITY': role_calc.player_roles['UTILITY']}
            for role in missing_roles:
                if missing_players != {}:
                    role_score = {}
                    for player in missing_players:
                        role_score[player] = missing_players[player][role] - sum([missing_players[player][position] for
                                                                                  position in missing_players[player] if
                                                                                  position in missing_roles and position
                                                                                  != role])
                    new_order.insert(['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'].index(role),
                                     max(role_score.items(), key=operator.itemgetter(1))[0])
                    missing_players.pop(max(role_score.items(), key=operator.itemgetter(1))[0])
            return new_order

    def switch_to_new_order(self, new_order: list):
        """
        Switch the current order to the new on

        :param new_order: Player names in order of position
        """
        position_matrix = {
            0: 'TOP',
            1: 'JUNGLE',
            2: 'MIDDLE',
            3: 'BOTTOM',
            4: 'UTILITY'
        }
        player_information_copy = self.player_information.copy()
        self.player_information = {}
        for position_count, player in enumerate(new_order):
            self.player_information[player] = player_information_copy[player]
            self.player_information[player]['real_position'] = position_matrix[position_count]

    def fix_titles(self):
        """
        Set the titles in the new order
        """
        self.titles = []
        for player in self.player_information:
            self.titles.append(player)

    def get_locked_in_position(self):
        """
        Use the add the player's locked in position to the player_information dictionary
        """
        for player in self.player_information:
            for team_member in self.clash_team_members:
                if self.player_information[player]['id'] == team_member['summonerId']:
                    self.player_information[player]['position'] = team_member['position']

    def process_each_clash_member(self):
        """
        Grab the information from each clash member found
        """
        for player in self.clash_team_members:
            self.get_summoner_id(player['summonerId'], query_type='')
        for player in self.player_information:
            self.get_non_random_match_history(player)
            self.get_player_ranked_clash_match_history(player)
            self.get_player_champion_mastery(player)
            self.get_ranked_information(player)

    def get_clash_team_id(self):
        """
        Get the clash team id for the given player
        """
        try:
            clash_team_info = self.get_json(f'{self.base_url}/lol/clash/v1/players/by-summoner/'
                                            f'{self.player_information[self.player_list[0]]["id"]}{self.api_key}')
        except HTTPError:
            self.errors['no_clash_team'].append(self.player_list[0])
        else:
            if clash_team_info:
                self.get_clash_team_players(clash_team_info[0]['teamId'])
            else:
                self.errors['no_clash_team'].append(self.player_list[0])

    def get_clash_team_players(self, clash_team_id: str):
        """
        Get the clash team players for the given team id

        :param clash_team_id: Id of the clash team to scrape info from
        """
        try:
            clash_team_info = self.get_json(f'{self.base_url}/lol/clash/v1/teams/{clash_team_id}{self.api_key}')
        except HTTPError:
            self.errors['no_clash_team'].append(self.player_list[0])
        else:
            self.clash_team_members = clash_team_info['players']

    def process_each_player(self, query_type: str = 'by-name/'):
        """
        Run the API queries for each player given

        :param query_type: Type of query to run to grab summoner id information
        """
        self.get_all_champion_info()
        for player in self.player_list:
            player = self.get_summoner_id(player, query_type)
            if player in self.player_information:
                self.get_non_random_match_history(player)
                self.get_player_ranked_clash_match_history(player)
                self.get_player_champion_mastery(player)
                self.get_ranked_information(player)
        self.cleanup()

    def cleanup(self):
        """
        Remove players for the player_information dictionary if they have no match history
        """
        remove = []
        for player in self.player_information:
            if player in self.errors['no_match_history']:
                remove.append(player)
        for player in remove:
            self.player_information.pop(player)

    def get_ranked_information(self, player: str):
        """
        Get the current rank of the given player

        :param player: Player name
        """
        try:
            summoner_info = self.get_json(f'{self.base_url}/lol/league/v4/entries/by-summoner/'
                                          f'{self.player_information[player]["id"]}{self.api_key}')
        except HTTPError:
            self.errors['no_ranked_info'].append(player)
        else:
            self.player_information[player]['ranked_info'] = {'everything': summoner_info,
                                                              'queue_score': 9, 'queue_rank': 5}
            self.parse_ranked_information(player)

    def parse_ranked_information(self, player: str):
        """
        Parse the ranked information for the player to determine their highest rank

        :param player: Player name
        """
        for queue_type in self.player_information[player]['ranked_info']['everything']:
            if self.queue_tiers[queue_type['tier']] < self.player_information[player]['ranked_info']['queue_score']:
                self.player_information[player]['ranked_info']['queue_score'] = self.queue_tiers[queue_type['tier']]
                self.player_information[player]['ranked_info']['queue_rank'] = self.queue_ranks[queue_type['rank']]
                self.player_information[player]['ranked_info']['tier'] = queue_type['tier']
                self.player_information[player]['ranked_info']['rank'] = queue_type['rank']
            elif self.queue_ranks[queue_type['rank']] < self.player_information[player]['ranked_info']['queue_rank']\
                    and self.queue_tiers[queue_type['tier']] == \
                    self.player_information[player]['ranked_info']['queue_score']:
                self.player_information[player]['ranked_info']['queue_rank'] = self.queue_ranks[queue_type['rank']]
                self.player_information[player]['ranked_info']['rank'] = queue_type['rank']

    def get_summoner_id(self, player: str, query_type: str):
        """
        Get the summoner id for the given player

        :param player: Player name
        :param query_type: Indicate querying by name or by ID
        :return: Correct case name of the player
        """
        if query_type == 'by-name/':
            player_name_url_encoded = urllib.parse.quote(player)
        else:
            player_name_url_encoded = player
        try:
            summoner_info = self.get_json(f'{self.base_url}/lol/summoner/v4/summoners/{query_type}'
                                          f'{player_name_url_encoded}{self.api_key}')
        except HTTPError:
            self.errors['player_not_found'].append(player)
        else:
            self.player_information[summoner_info['name']] = {'id': summoner_info['id'],
                                                              'accountId': summoner_info['accountId']}
            self.titles.append(summoner_info['name'])
            return summoner_info['name']

    def get_non_random_match_history(self, player: str):
        """
        Get the match history for the player in all non random game queues

        :param player: Player name
        """
        query_url = f'{self.base_url}/lol/match/v4/matchlists/by-account/' \
                    f'{self.player_information[player]["accountId"]}{self.api_key}' \
                    f'{self.queue_id["clash"]}{self.queue_id["ranked_solo"]}{self.queue_id["ranked_flex"]}' \
                    f'{self.queue_id["norm_draft"]}{self.queue_id["norm_blind"]}'
        try:
            self.player_information[player]['all_match_history'] = self.get_json(query_url)['matches']
        except HTTPError:
            self.errors['no_match_history'].append(player)
            self.titles.remove(player)

    def get_player_ranked_clash_match_history(self, player: str):
        """
        Get the match history for the given player

        :param player: Player name
        """
        query_url = f'{self.base_url}/lol/match/v4/matchlists/by-account/' \
                    f'{self.player_information[player]["accountId"]}{self.api_key}' \
                    f'{self.queue_id["clash"]}{self.queue_id["ranked_solo"]}{self.queue_id["ranked_flex"]}'
        try:
            self.player_information[player]['ranked_match_history'] = self.get_json(query_url)['matches']
        except HTTPError:
            if player not in self.errors['no_match_history']:
                self.errors['no_ranked_clash'].append(player)

    def get_player_champion_mastery(self, player: str):
        """
        Get all of the champion mastery information for the given player

        :param player: Player name
        """
        query_url = f'{self.base_url}/lol/champion-mastery/v4/champion-masteries/by-summoner/' \
                    f'{self.player_information[player]["id"]}{self.api_key}'
        try:
            self.parse_champion_mastery_information(player, self.get_json(query_url))
        except HTTPError:
            self.errors['no_champion_mastery'].append(player)

    def parse_champion_mastery_information(self, player: str, mastery_information: dict):
        """
        Parse the champion mastery information

        :param player: Player name
        :param mastery_information: Dict of the champion mastery for the given player
        """
        self.check_all_champs_in_champion_info(mastery_information)
        self.player_information[player]['mastery_information'] = {}
        for champion in mastery_information:
            for champ_id in self.champion_info.values():
                if int(champ_id['key']) == champion['championId']:
                    self.player_information[player]['mastery_information'][champ_id['id']] = \
                        {'mastery': champion['championPoints'], 'last_play_time': champion['lastPlayTime']}
                    break

    def check_all_champs_in_champion_info(self, mastery_information: dict):
        """
        Verify all of the champions in the champion mastery information are in the champion info dictionary. If there
        is a missing champion then re-download the latest champion info

        :param mastery_information: Dictionary of champion mastery information
        """
        champion_info_keys = [int(self.champion_info[champ]['key']) for champ in self.champion_info]
        mastery_info_keys = [champ['championId'] for champ in mastery_information]
        for key in mastery_info_keys:
            if key not in champion_info_keys:
                self.download_champion_info()

    def get_all_champion_info(self):
        """
        Get all of the latest champion info from the data dragon or saved file
        """
        self.create_folder_if_it_does_not_exists('../extra_files')

        # If there is already a saved file
        if os.path.isfile('../extra_files/champion_info.json'):
            with open('../extra_files/champion_info.json') as champion_info_file:
                self.champion_info = json.load(champion_info_file)

        # If a new download is needed
        else:
            self.download_champion_info()

    def download_champion_info(self):
        """
        Download the latest champion info from the data dragon and save it
        """
        version = self.get_json('http://ddragon.leagueoflegends.com/api/versions.json')[0]
        self.champion_info = self.get_json(f'http://ddragon.leagueoflegends.com/cdn/'
                                           f'{version}/data/en_US/champion.json')['data']
        with open('../extra_files/champion_info.json', 'w') as champion_info_file:
            json.dump(self.champion_info, champion_info_file)

    @staticmethod
    def create_folder_if_it_does_not_exists(path: str):
        """
        Create the folder in the given path if it does not exist

        :param path: Path to create the folder in
        """
        if not os.path.isdir(path):
            os.mkdir(path)

    @staticmethod
    def get_json(url: str) -> dict:
        """
        Query the given url to get it's json response

        :return: Json object of the url request
        """
        with urllib.request.urlopen(url) as url_request:
            return json.loads(url_request.read().decode())


if __name__ == '__main__':
    tmp = APIQueries(['DebonaireSnake6'], True)
    print()
