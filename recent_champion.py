"""
This file gathers all of the information needed to create the recent champion table
"""
import operator

from text_to_image import CreateImage


class BadTableType(Exception):
    """
    Custom error message for bad table types
    """
    def __init__(self, message):
        super().__init__(message)


class RecentChampion:
    """
    Handle creating the recent champion table
    """
    def __init__(self, api_results: object, table_type: str):
        """
        Handle creating the recent champion table

        :param api_results: Results from the api_queries file
        :param table_type: Type of table to create: ranked_match_ranked, all_match_history
        """
        self.api_results = api_results
        self.titles = None
        self.columns = []
        self.current_column = []
        self.current_column_values = []
        self.colour_columns = []
        self.colour_current_column = []
        self.match_history = None
        self.current_match = None
        self.champion_info = self.api_results.champion_info
        self.champions_played = {}
        self.champion = None
        self.player_cnt = None
        self.player_champ_cnt = None
        self.matching_cnt = None
        self.other_player_champions = None
        self.table_type = table_type

        self.setup()

    def setup(self):
        """
        Run the major functions of the object
        """
        self.verify_correct_table_type()
        self.create_recent_champion_table()
        self.create_image()

    def verify_correct_table_type(self):
        """
        If the table type is incorrect then fail
        """
        valid_table_types = ['all_match_history', 'ranked_match_history']
        if self.table_type not in valid_table_types:
            raise BadTableType('Table type needs to be of: all_match_history, ranked_match_history')

    def create_image(self):
        """
        Create the image from the processed results
        """
        CreateImage(self.titles, self.columns, 'extra_files/recent_champion.png',
                    colour=self.colour_columns, convert_columns=True)

    def create_recent_champion_table(self):
        """
        Create the roll rate table and all of it's components
        """
        # Setup the table
        self.adjust_titles()

        # Gather the recent champions for each player
        for player in self.api_results.player_information:
            self.match_history = self.api_results.player_information[player][self.table_type]
            self.get_recent_champions()
            self.add_most_popular_to_column()
            self.add_high_games_played_colour()
            self.reset_column_values()

        self.add_highlighting_for_shared_champs()

    def reset_column_values(self):
        """
        Reset the values to the current column before processing the next player
        """
        self.current_column = []
        self.current_column_values = []
        self.colour_current_column = []

    def add_high_games_played_colour(self):
        """
        Add highlighting for lots of games played
        """
        for games_played in self.current_column_values:
            if int(games_played) >= 25:
                self.colour_current_column.append('orange')
            elif int(games_played) >= 10:
                self.colour_current_column.append('blue')
            else:
                self.colour_current_column.append('')
        self.colour_columns.append(self.colour_current_column)
        self.colour_columns.append(self.colour_current_column)

    def add_highlighting_for_shared_champs(self):
        """
        Add highlighting to each column for shared champs
        """
        for player_cnt, player_champions in enumerate(self.columns[::2]):
            for player_champ_cnt, champion in enumerate(player_champions):
                self.champion = champion
                self.player_cnt = player_cnt
                self.player_champ_cnt = player_champ_cnt
                self.match_champ_with_other_player()

    def match_champ_with_other_player(self):
        """
        Highlight if the current champ is shared with other players
        """
        for matching_cnt, other_player_champions in enumerate(self.columns[2 + (self.player_cnt * 2)::2]):
            if self.champion in other_player_champions:
                self.matching_cnt = matching_cnt
                self.other_player_champions = other_player_champions
                self.set_colours_for_champions()

    def set_colours_for_champions(self):
        """
        Colour the original champion and it's matching champion name
        """
        # Colour the original player
        if self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] == 'orange':
            self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] = 'red'
        elif self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] == 'blue':
            self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] = 'yellow'
        else:
            self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] = 'green'

        # Colour the matched player
        matched_champ_cnt = self.other_player_champions.index(self.champion)
        if self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] == 'orange':
            self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] = 'red'
        elif self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] == 'blue':
            self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] = 'yellow'
        else:
            self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] = 'green'

    def adjust_titles(self):
        """
        Adjust the player list to include columns for number of mastery points
        """
        self.titles = []
        for player_cnt, player in enumerate(self.api_results.player_list):
            self.titles.append(player)
            self.titles.append(f'#{player_cnt + 1}')

    def add_most_popular_to_column(self):
        """
        Add the most popular champs to the current column
        """
        for x in range(10):
            champ_name = max(self.champions_played.items(), key=operator.itemgetter(1))[0]
            self.current_column.append(champ_name)
            self.current_column_values.append(str(self.champions_played.pop(champ_name)))
        self.columns.append(self.current_column)
        self.columns.append(self.current_column_values)

    def get_recent_champions(self):
        """
        Count the number of champions recently played by the current player
        """
        for match in self.match_history:
            self.current_match = match
            self.determine_champion_played()

    def determine_champion_played(self):
        """
        Determine the champion played int he current game
        """
        for champion_name in self.champion_info:
            if str(self.current_match['champion']) == self.champion_info[champion_name]['key']:
                self.champions_played[champion_name] = self.champions_played.get(champion_name, 0) + 1
