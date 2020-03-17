"""
The file will grab the information required to create the roll rate table
"""

import sys

from text_to_image import CreateImage


class RoleRate:
    """
    Handle creating the roll rate table
    """
    def __init__(self, api_results: object, title_colours: list):
        """
        Handle creating the role rate table

        :param api_results: Results from the api_queries file
        :param title_colours: What to colour each title based ont eh player's rank
        """
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
        self.role_ids = {
            'SOLO - TOP': 'top',
            'SOLO - MID': 'mid',
            'NONE - JUNGLE': 'jng',
            'DUO_CARRY - BOTTOM': 'bot',
            'DUO_SUPPORT - BOTTOM': 'sup',
            'TOP': 'top',
            'JUNGLE': 'jng',
            'MID': 'mid',
            'BOTTOM': 'bot',
            'DUO': 'bot',
            'DUO_SUPPORT': 'sup',
            'NONE': 'jng'
        }

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
        CreateImage(self.titles, self.columns, 'extra_files/roll_rate.png',
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

    def calculate_all_roles(self):
        """
        Calculate the roles for the current player
        """
        self.player_roles = {
            'top': 0,
            'jng': 0,
            'mid': 0,
            'bot': 0,
            'sup': 0
        }

        # Get the role for each game
        for match in self.match_history:
            self.current_match = match
            self.determine_role_played()

        # Add the final list to the columns set
        self.columns.append([str(self.player_roles['top']), str(self.player_roles['jng']),
                             str(self.player_roles['mid']), str(self.player_roles['bot']),
                             str(self.player_roles['sup'])])

    def determine_role_played(self):
        """
        Determine the role played based on the match history
        """
        if f'{self.current_match["role"]} - {self.current_match["lane"]}' in self.role_ids:
            self.player_roles[self.role_ids[f'{self.current_match["role"]} - {self.current_match["lane"]}']] += 1
        elif self.current_match['lane'] in self.role_ids:
            self.player_roles[self.role_ids[self.current_match['lane']]] += 1
        elif self.current_match['role'] in self.role_ids:
            self.player_roles[self.role_ids[self.current_match['role']]] += 1
        else:
            print(f'Undetermined role:\t{self.current_match["role"]} - {self.current_match["lane"]}', file=sys.stderr)
