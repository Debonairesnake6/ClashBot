"""
This file gathers all of the information needed to create the champions for role table
"""
import operator

from text_to_image import CreateImage


class ChampionsForRole:
    """
    Handle creating the champions for role table
    """
    def __init__(self, api_results: object, title_colours: list):
        """
        Handle creating the champions for role table

        :param api_results: Results from the api_queries file
        :param title_colours: What to colour each title based ont eh player's rank
        """
        self.api_results = api_results
        self.title_colours = title_colours[:]
        self.titles = None
        self.columns = []
        self.current_column = []
        self.current_column_values = []
        self.colour_columns = []
        self.colour_current_column = []
        self.champions_played = None
        self.current_match = None
        self.champion_info = self.api_results.champion_info
        self.champions_played = {}
        self.champion = None
        self.player_cnt = None
        self.player_champ_cnt = None
        self.matching_cnt = None
        self.other_player_champions = None

        self.setup()

    def setup(self):
        """
        Run the major functions of the object
        """
        self.create_recent_champion_table()
        self.create_image()

    def create_image(self):
        """
        Create the image from the processed results
        """
        CreateImage(self.titles, self.columns, '../extra_files/champions_for_role.png',
                    colour=self.colour_columns, convert_columns=True, title_colours=self.title_colours)

    def create_recent_champion_table(self):
        """
        Create the roll rate table and all of it's components
        """
        # Setup the table
        self.adjust_titles()

        # Gather the recent champions for each player
        for player in self.api_results.player_information:
            self.champions_played = self.api_results.player_information[player]['position_champions']

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
        total_games = sum([int(games) for games in self.current_column_values if games != ''])
        for games_played in self.current_column_values:
            if games_played == '':
                self.colour_current_column.append('')
            elif int(games_played) >= int(total_games / 4):
                self.colour_current_column.append('orange')
            elif int(games_played) >= int(total_games / 6):
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
        for player_cnt, player in enumerate(self.api_results.titles):
            self.titles.append(player)
            self.titles.append(f'#{player_cnt + 1}')

        # Adjust colouring for the titles
        self.title_colours = [colour for copy_list in [[rank, rank] for rank in self.title_colours]
                              for colour in copy_list]

    def add_most_popular_to_column(self):
        """
        Add the most popular champs to the current column
        """
        for x in range(10):
            try:
                champ_name = max(self.champions_played.items(), key=operator.itemgetter(1))[0]

            # If the player has less than 10 champs played
            except ValueError:
                break
            self.current_column.append(champ_name)
            self.current_column_values.append(str(self.champions_played.pop(champ_name)))

        # Pad the column until it reaches a length of 10
        while len(self.current_column) < 10:
            self.current_column.append('')
            self.current_column_values.append('')
        self.columns.append(self.current_column)
        self.columns.append(self.current_column_values)


if __name__ == '__main__':
    import shelve
    shelf = shelve.open('../extra_files/my_api')['champions_for_role']
    tmp = ChampionsForRole(shelf['api_results'], shelf['title_colours'])
    print()
