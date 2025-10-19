"""
This file will run all of the API queries for each access during the processing of each of the tables
"""

import json
import os
# import urllib.request
import operator
import time
from functools import lru_cache

import requests
from dotenv import load_dotenv
from urllib.error import HTTPError
from role_rate import RoleRate
import datetime
from dateutil.relativedelta import relativedelta
import cassiopeia

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
        self.saved_positions = {}
        self.player_list = player_list
        self.base_url = 'https://americas.api.riotgames.com'
        self.base_url_na1 = 'https://na1.api.riotgames.com'
        self.api_key = f'?api_key={os.getenv("RIOT_API")}'
        self.role_list = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
        self.errors = {
            'player_not_found': [],
            'no_ranked_clash': [],
            'no_match_history': [],
            'no_ranked_info': [],
            'no_clash_team': [],
            'no_champion_mastery': []
        }
        # Refer to https://static.developer.riotgames.com/docs/lol/queues.json
        self.queue_id = {  # todo update
            'norm_draft': '&queue=400',
            'clash': '&queue=700',
            'ranked_solo': '&queue=420',
            # 'ranked_solo': '&queue=RANKED_SOLO_5X5',
            'ranked_flex': '&queue=440',
            # 'ranked_flex': '&queue=RANKED_FLEX_SR',
            'norm_blind': '&queue=430',
            # 'poro_king': '&queue=920',
            # 'aram': '&queue=450'
        }
        self.queue_tiers = {  # todo update colours based on emerald being added
            'CHALLENGER': 0,
            'GRANDMASTER': 1,
            'MASTER': 2,
            'DIAMOND': 3,
            'EMERALD': 4,
            'PLATINUM': 5,
            'GOLD': 6,
            'SILVER': 7,
            'BRONZE': 8,
            'IRON': 9,
        }
        self.queue_ranks = {
            'I': 0,
            'II': 1,
            'III': 2,
            'IV': 3
        }

        # Store the information from the queries
        self.player_information = {}

        self.match_start_epoch_time = int((datetime.datetime.now() - relativedelta(months=6)).timestamp())
        cassiopeia.set_riot_api_key(os.getenv("RIOT_API"))

        # Grab information based on the given player list
        if self.clash_api:
            self.use_clash_api()
        else:
            self.process_each_player()

    def use_clash_api(self):
        """
        Use the clash API based on the given player
        """
        self.process_each_player(get_match_history=False)
        self.get_clash_team_id()
        for player in self.player_information:
            self.player_information[player]['position'] = [member for member in self.clash_team_members if member['puuid'] == self.player_information[player]['puuid']][0]['position']
        if len(self.errors['no_clash_team']) == 0:
            self.process_each_clash_member()
            self.get_locked_in_position()
            self.change_order_by_position()
            self.verify_single_player_per_role()

    def verify_single_player_per_role(self):
        """
        Verify only a single player is locked in per role and adjust if need be
        """
        for role in self.role_list:
            locked_in = [player for player in self.player_information
                         if self.player_information[player]['position'] == role]
            if len(locked_in) > 1:
                for player in locked_in:
                    self.saved_positions[player] = role
        if self.saved_positions != {}:
            for player in self.saved_positions:
                self.player_information[player]['position'] = 'FILL'
            self.change_order_by_position()
            for player in self.saved_positions:
                self.player_information[player]['position'] = self.saved_positions[player]

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
        for position in self.role_list:
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
            for cnt, position in enumerate(self.role_list):
                if position not in roles_found:
                    new_order.insert(cnt, [player for player in self.player_information if player not in new_order][0])
                    return new_order
        else:
            role_calc = RoleRate(self, just_using_functions=True)
            missing_players = {}
            missing_roles = [role for role in self.role_list if role not in roles_found]
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
                    new_order.insert(self.role_list.index(role), max(role_score.items(), key=operator.itemgetter(1))[0])
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
                if self.player_information[player]['puuid'] == team_member['puuid']:
                    self.player_information[player]['position'] = team_member['position']

    def process_each_clash_member(self):
        """
        Grab the information from each clash member found
        """
        for player in self.clash_team_members:
            # self.get_summoner_id(player['summonerId'])
            self.get_summoner_object(player['puuid'])
        for player in self.player_information:
            self.get_non_random_match_history(player)
            self.get_player_ranked_clash_match_history(player)
            self.convert_match_history(player)
            self.get_player_champion_mastery(player)
            self.get_ranked_information(player)

    def refresh_op_gg_data(self):
        for player in self.player_information:
            print(f'\tRefreshing OP.GG data for {player}')
            response = requests.post(f'https://op.gg/lol/summoners/na/{player}-{self.player_information[player]['tagline']}?queue_type=NORMAL',
                                     data=f'[{{"region":"na","puuid":"{self.player_information[player]['op_gg_puuid']}","isPremiumPrimary":false}}]',
                                     headers={'Next-Action': '405a04669583947dc03eb8c7f367adf28c8f714e86'})
            response.raise_for_status()
            time.sleep(1)
        time.sleep(20)

    def get_clash_team_id(self):
        """
        Get the clash team id for the given player
        """
        print(f"Getting clash team ID for: {self.player_list[0]}")
        try:

            clash_team_info = self.get_json(f'{self.base_url_na1}/lol/clash/v1/players/by-puuid/'
                                            f'{self.player_information[self.player_list[0]]["puuid"]}{self.api_key}')
        except HTTPError as e:
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
            clash_team_info = self.get_json(f'{self.base_url_na1}/lol/clash/v1/teams/{clash_team_id}{self.api_key}')
        except HTTPError:
            self.errors['no_clash_team'].append(self.player_list[0])
        else:
            self.clash_team_members = clash_team_info['players']

    def process_each_player(self, get_match_history: bool = True):
        """
        Run the API queries for each player given

        :param query_type: Type of query to run to grab summoner id information
        """
        self.get_all_champion_info()
        for player in self.player_list:
            print(f"Processing player: {player}")
            player = self.get_summoner_id(player)
            self.get_summoner_object(self.player_information[player]['puuid'], player)
        self.refresh_op_gg_data()
        if get_match_history:
            role_mapping = {
                0: 'TOP',
                1: 'JUNGLE',
                2: 'MIDDLE',
                3: 'BOTTOM',
                4: 'UTILITY',
            }
            for cnt, player in enumerate(self.player_information):
                self.player_information[player]['position'] = role_mapping[cnt]
                self.get_non_random_match_history(player)
                self.get_player_ranked_clash_match_history(player)
                self.convert_match_history(player)
                self.get_player_champion_mastery(player)
                self.get_ranked_information(player)
        self.cleanup()

    def convert_match_history(self, player: str):
        """
        Convert the match IDs to the actual history of the game
        :param player: The name of the player currently processing
        """
        print(f"\tConverting match history for: {player}")
        for match_type in ['all_match_history', 'ranked_match_history']:
            matches = self.player_information[player][match_type]
            all_matches_updated = {}
            for match in matches:
                # match_info = self.get_json(f'{self.base_url}/lol/match/v5/matches/{match}{self.api_key}')
                # players_data = [participant for participant in match.participants if participant.account.puuid == self.player_information[player]['puuid']][0]
                if match['created_at'] in all_matches_updated:
                    print()
                all_matches_updated[match['created_at']] = {
                    'champion': match['champion']['name'],
                    # 'role': players_data.role.name,
                    # 'lane': players_data.lane.name,
                    'position': match['position'],

                }
            self.player_information[player][match_type] = [value for value in all_matches_updated.values()]

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
        print(f"\tGetting ranked information for: {player}")
        try:
            summoner_info = self.get_json(f'{self.base_url_na1}/lol/league/v4/entries/by-puuid/'
                                          f'{self.player_information[player]["puuid"]}{self.api_key}')
        except HTTPError:
            self.errors['no_ranked_info'].append(player)
            self.player_information[player]['ranked_info'] = {'everything': [], 'queue_score': 9, 'queue_rank': 5,
                                                              'tier': 'UNRANKED'}
        else:
            self.player_information[player]['ranked_info'] = {'everything': summoner_info,
                                                              'queue_score': 9, 'queue_rank': 5}
            self.parse_ranked_information(player)

    def parse_ranked_information(self, player: str):
        """
        Parse the ranked information for the player to determine their highest rank

        :param player: Player name
        """
        print(f"\tParsing ranked information for: {player}")
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


    def get_summoner_object(self, puuid: str, player_name: str = None):
        if player_name is None:
            player_info = self.get_json(f'{self.base_url}/riot/account/v1/accounts/by-puuid/{puuid}{self.api_key}')
            player_name = player_info['gameName']
            tagline = player_info['tagLine']
        else:
            tagline = "NA1" if "#" not in player_name else player_name.split("#")[1]

        region = "NA1"
        summoner = cassiopeia.get_summoner(puuid=puuid, region="NA")
        if player_name not in self.player_information:
            self.player_information[player_name] = {'puuid': puuid}
        self.player_information[player_name]['summoner_object'] = summoner
        self.player_information[player_name]['tagline'] = tagline

        response = requests.get(f'https://op.gg/lol/summoners/na/{player_name}-{tagline}?queue_type=SOLORANKED')
        op_gg_puuid = response.text.split('{\\"puuid\\":\\"')[-1].split('\\')[0]
        self.player_information[player_name]['op_gg_puuid'] = op_gg_puuid

    def get_summoner_id(self, player: str):
        """
        Get the summoner id for the given player

        :param player: Player name
        :return: Correct case name of the player
        """
        print(f"\tGetting summoner ID for: {player}")
        # player_name_url_encoded = urllib.parse.quote(player)
        tag_line = "NA1" if "#" not in player else player.split("#")[1]
        try:
            summoner_info = self.get_json(f'{self.base_url}/riot/account/v1/accounts/by-riot-id/{player}/'
                                          f'{tag_line}{self.api_key}')
        except HTTPError as e:
            self.errors['player_not_found'].append(player)
        else:
            self.player_information[summoner_info['gameName']] = {'puuid': summoner_info['puuid']}
            self.titles.append(summoner_info['gameName'])
            return summoner_info['gameName']

    @staticmethod
    @lru_cache
    def cached_post_request(url: str, data: str):
        headers = {
            'Next-Action': '409a2b9ca50d15e50a4dace93552e3a40113dc2753',
        }
        return requests.post(url, data=data, headers=headers)

    def get_non_random_match_history(self, player: str):
        """
        Get the match history for the player in all non random game queues

        :param player: Player name
        """
        print(f"\tGetting all match history for: {player}")
        all_matches = []

        for queue in ['SOLORANKED', 'FLEXRANKED', 'NORMAL', 'CLASH']:
            end_time = ""
            for cnt in range(5):
                print(f'\t\t{queue} - {cnt + 1} of 5')
                response = self.cached_post_request(f'https://op.gg/lol/summoners/na/{player}-{self.player_information[player]['tagline']}?queue_type={queue}',
                                         data=f'[{{"locale":"en","region":"na","puuid":"{self.player_information[player]['op_gg_puuid']}","gameType":"{queue}","endedAt":"{end_time}","champion":""}}]')
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 502:
                        continue
                data = json.loads(response.text.split('\n')[1][2:])
                if len(data['data']) == 0 and end_time == "":
                    end_time = (datetime.datetime.now() - datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT00:23:00+09:00")
                    continue
                elif len(data['data']) == 0:
                    try:
                        end_time = (datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S+09:00") - datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT00:23:00+09:00")
                    except ValueError as e:
                        print()
                    continue
                all_matches += data['data']
                try:
                    end_time = data['meta']['last_game_created_at']
                except TypeError as e:
                    print()
                time.sleep(0.5)
        # for queue_type in [cassiopeia.Queue.normal_draft_fives, cassiopeia.Queue.clash, cassiopeia.Queue.ranked_solo_fives, cassiopeia.Queue.ranked_flex_fives, cassiopeia.Queue.blind_fives]:
        #     all_matches += cassiopeia.get_match_history(puuid=self.player_information[player]["puuid"],
        #                                            start_time=self.match_start_epoch_time,
        #                                            queue=queue_type, count=20,
        #                                            continent="AMERICAS")
        if len(all_matches) == 0:
            self.errors['no_match_history'].append(player)
            self.titles.remove(player)
        self.player_information[player]['all_match_history'] = all_matches

    def get_player_ranked_clash_match_history(self, player: str):
        """
        Get the match history for the given player

        :param player: Player name
        """
        print(f"\tGetting important match history for: {player}")
        all_matches = []
        for queue in ['SOLORANKED', 'FLEXRANKED', 'CLASH']:
            end_time = ""
            for cnt in range(5):
                print(f'\t\t{queue} - {cnt + 1} of 5')
                response = self.cached_post_request(f'https://op.gg/lol/summoners/na/{player}-{self.player_information[player]['tagline']}?queue_type={queue}',
                                         data=f'[{{"locale":"en","region":"na","puuid":"{self.player_information[player]['op_gg_puuid']}","gameType":"{queue}","endedAt":"{end_time}","champion":""}}]')
                try:
                    response.raise_for_status()
                except HTTPError as e:
                    if response.status_code == 502:
                        continue
                data = json.loads(response.text.split('\n')[1][2:])
                if len(data['data']) == 0 and end_time == "":
                    end_time = (datetime.datetime.now() - datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT00:23:00+09:00")
                    continue
                elif len(data['data']) == 0:
                    end_time = (datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S+09:00") - datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT00:23:00+09:00")
                    continue
                all_matches += data['data']
                try:
                    end_time = data['meta']['last_game_created_at']
                except TypeError as e:
                    print()
                # time.sleep(0.5)
                # time.sleep(1)
        # for queue_type in [cassiopeia.Queue.ranked_solo_fives, cassiopeia.Queue.ranked_flex_fives]:
        #     all_matches += cassiopeia.get_match_history(puuid=self.player_information[player]["puuid"],
        #                                            start_time=self.match_start_epoch_time,
        #                                            queue=queue_type, count=20,
        #                                            continent="AMERICAS")
            # query_url = f'{self.base_url}/lol/match/v5/matches/by-puuid/' \
            #             f'{self.player_information[player]["puuid"]}/ids{self.api_key}&count=100&type={queue_type}' \
            #             f'&startTime={self.match_start_epoch_time}'
                        # f'{self.queue_id["clash"]}{self.queue_id["ranked_solo"]}{self.queue_id["ranked_flex"]}'
            # try:
            #     all_matches += self.get_json(query_url)
            # except HTTPError:
            #     pass
        if len(all_matches) == 0:
            if player not in self.errors['no_match_history']:
                self.errors['no_ranked_clash'].append(player)
        self.player_information[player]['ranked_match_history'] = all_matches

    def get_player_champion_mastery(self, player: str):
        """
        Get all of the champion mastery information for the given player

        :param player: Player name
        """
        print(f"\tGetting champion mastery information for: {player}")
        query_url = f'{self.base_url_na1}/lol/champion-mastery/v4/champion-masteries/by-puuid/' \
                    f'{self.player_information[player]["puuid"]}{self.api_key}'
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
        print(f"\tParsing champion mastery information for: {player}")
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

            if self.champion_info['Aatrox']['version'] != self.get_json('http://ddragon.leagueoflegends.com/api/versions.json')[0]:
                self.download_champion_info()

        # If a new download is needed
        else:
            self.download_champion_info()

    def download_champion_info(self):
        """
        Download the latest champion info from the data dragon and save it
        """
        print("Downloading latest champion info...")
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

    def get_json(self, url: str) -> dict:
        """
        Query the given url to get it's json response

        :return: Json object of the url request
        """
        response = requests.get(url)
        try:
            response.raise_for_status()
        except HTTPError as e:
            if response.status_code == 429:
                time.sleep(2)
                return self.get_json(url)
            raise e
        return response.json()


if __name__ == '__main__':
    tmp = APIQueries([
        # 'iKony',
        # 'Eric1',
        # 'Shorthop',
        'spiderjo',
        # 'Debonairesnake6'
    ], False)
    # tmp = APIQueries(['DebonaireSnake6'], True)
    print()
