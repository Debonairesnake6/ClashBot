"""
The file will grab the information required to create the roll rate table
"""

import sys

from text_to_image import CreateImage


class RoleRate:
    """
    Handle creating the roll rate table
    """
    def __init__(self, api_results: object = None, title_colours: list = None, just_using_functions: bool = False):
        """
        Handle creating the role rate table

        :param api_results: Results from the api_queries file
        :param title_colours: What to colour each title based ont eh player's rank
        :param just_using_functions: If the intention is to use functions rather than create an image
        """
        if title_colours is None:
            title_colours = []
        self.api_results = api_results
        self.title_colours = title_colours[:]
        self.titles = None
        self.columns = []
        self.current_column = []
        self.colour_columns = []
        self.colour_current_column = []
        self.match_history = None
        self.player_roles = None
        self.current_match = None
        self.player_games_played = None
        self.player_name = None
        self.role_ids = {
            'SOLO - TOP': 'TOP',
            'SOLO - MID': 'MIDDLE',
            'NONE - JUNGLE': 'JUNGLE',
            'DUO_CARRY - BOTTOM': 'BOTTOM',
            'DUO_SUPPORT - BOTTOM': 'UTILITY',
            'TOP': 'TOP',
            'JUNGLE': 'JUNGLE',
            'MID': 'MIDDLE',
            'BOTTOM': 'BOTTOM',
            'DUO': 'BOTTOM',
            'DUO_SUPPORT': 'UTILITY',
            'NONE': 'JUNGLE'
        }

        if not just_using_functions:
            self.setup()

    def setup(self):
        """
        Run the major functions of the object
        """
        self.create_roll_rate_table()
        self.create_image()

    def create_image(self):
        """
        Create the image from the processed results
        """
        CreateImage(self.titles, self.columns, '../extra_files/roll_rate.png',
                    colour=self.colour_columns, convert_columns=True, title_colours=self.title_colours)

    def create_roll_rate_table(self):
        """
        Create the roll rate table and all of it's components
        """
        # Setup the table
        self.adjust_titles()
        self.columns.append(['Top', 'Jng', 'Mid', 'Bot', 'Sup'])
        self.colour_columns.append(['', '', '', '', ''])

        # Collect the play rate information
        for player in self.api_results.player_information:
            self.player_name = player
            self.api_results.player_information[self.player_name]['position_champions'] = {}

            try:
                self.match_history = self.api_results.player_information[player]['all_match_history']

            # If the player has no match history
            except KeyError:
                continue
            self.calculate_all_roles()

        self.add_highlighting_for_high_play_rate()

    def adjust_titles(self):
        """
        Adjust the player list to include columns for number of mastery points
        """
        self.titles = self.api_results.titles[:]
        self.titles.insert(0, 'Role')
        self.title_colours.insert(0, '')

    def add_highlighting_for_high_play_rate(self):
        """
        Highlight play rates that are above a certain percentage
        """
        for player in self.columns[1:]:
            self.player_games_played = player
            self.add_highlighting_for_current_player()

    def add_highlighting_for_current_player(self):
        """
        Add highlighting for the current player based on games played
        """
        self.colour_current_column = []
        for games_played in self.player_games_played:
            if int(games_played) >= 50:
                self.colour_current_column.append('red')
            elif int(games_played) >= 25:
                self.colour_current_column.append('orange')
            else:
                self.colour_current_column.append('')
        self.colour_columns.append(self.colour_current_column)

    def calculate_all_roles(self, player_name: str = None):
        """
        Calculate the roles for the current player

        @param player_name: Name of the player who's match history is being processed
        """
        self.player_roles = {
            'TOP': 0,
            'JUNGLE': 0,
            'MIDDLE': 0,
            'BOTTOM': 0,
            'UTILITY': 0
        }
        if player_name:
            self.player_name = player_name

        # Get the role for each game
        for match in self.match_history:
            self.current_match = match
            if 'position_champions' not in self.api_results.player_information[self.player_name]:
                self.api_results.player_information[self.player_name]['position_champions'] = {}
            self.determine_role_played()

        # Add the final list to the columns set
        self.columns.append([str(self.player_roles['TOP']), str(self.player_roles['JUNGLE']),
                             str(self.player_roles['MIDDLE']), str(self.player_roles['BOTTOM']),
                             str(self.player_roles['UTILITY'])])

    def determine_role_played(self):
        """
        Determine the role played based on the match history
        """
        if f'{self.current_match["role"]} - {self.current_match["lane"]}' in self.role_ids:
            self.player_roles[self.role_ids[f'{self.current_match["role"]} - {self.current_match["lane"]}']] += 1
            self.track_champions_played_in_locked_in_position(self.role_ids[f'{self.current_match["role"]} - '
                                                                            f'{self.current_match["lane"]}'])
        elif self.current_match['lane'] in self.role_ids:
            self.player_roles[self.role_ids[self.current_match['lane']]] += 1
            self.track_champions_played_in_locked_in_position(self.role_ids[self.current_match['lane']])
        elif self.current_match['role'] in self.role_ids:
            self.player_roles[self.role_ids[self.current_match['role']]] += 1
            self.track_champions_played_in_locked_in_position(self.role_ids[self.current_match['role']])
        else:
            print(f'Undetermined role:\t{self.current_match["role"]} - {self.current_match["lane"]}', file=sys.stderr)

    def track_champions_played_in_locked_in_position(self, position: str):
        """
        Keep track of the champions played in the locked in position for clash

        :param position: Position the player locked in
        """
        if 'position' in self.api_results.player_information[self.player_name] \
                and position == self.api_results.player_information[self.player_name]['position']\
                and 'real_position' not in self.api_results.player_information[self.player_name]:
            self.add_champ_to_current_position()
        elif 'real_position' in self.api_results.player_information[self.player_name] \
                and position == self.api_results.player_information[self.player_name]['real_position']:
            self.add_champ_to_current_position()

    def add_champ_to_current_position(self):
        """
        Add the champion to the list if played in the same role the player locked in
        """
        for champion_name in self.api_results.champion_info:
            if str(self.current_match['champion']) == self.api_results.champion_info[champion_name]['key']:
                self.api_results.player_information[self.player_name]['position_champions'][champion_name] = \
                    self.api_results.player_information[self.player_name]['position_champions'].get(champion_name, 0) + 1
