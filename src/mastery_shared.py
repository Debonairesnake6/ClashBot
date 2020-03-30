"""
This file will grab the mastery information from the players to create the mastery shared table
"""

from text_to_image import CreateImage


class MasteryShared:
    """
    Handle creating the mastery shared table
    """
    def __init__(self, api_results: object, title_colours: list):
        """
        Handle creating the mastery shared table

        :param api_results: Results from the api_queries file
        :param title_colours: Title colour for each player based on the player rank
        """
        self.api_results = api_results
        self.title_colours = title_colours[:]
        self.titles = None
        self.columns = []
        self.current_column = []
        self.current_column_amount = []
        self.colour_columns = []
        self.colour_current_column = []
        self.total_mastery_score = 0
        self.column_mastery_scores = []
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
        self.create_mastery_shared_table()
        self.create_image()

    def create_image(self):
        """
        Create image from the processed results
        """
        CreateImage(self.titles, self.columns, '../extra_files/mastery_shared.png',
                    colour=self.colour_columns, convert_columns=True, title_colours=self.title_colours)

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

    def create_mastery_shared_table(self):
        """
        Create the mastery shared table
        """
        self.adjust_titles()

        # Get the champion mastery information high high mastery colour
        for player in self.api_results.player_information:
            self.get_top_champs(self.api_results.player_information[player]['mastery_information'])
            self.add_high_mastery_colour()
            self.reset_current_column_info()

        self.add_highlighting_for_shared_champs()

    def add_highlighting_for_shared_champs(self):
        """
        Add highlighting to each column for shared champs
        """
        # Go through each champion starting with the first player
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
                if self.champion != '':
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
        else:
            self.colour_columns[self.player_cnt * 2][self.player_champ_cnt] = 'yellow'

        # Colour the matched player
        matched_champ_cnt = self.other_player_champions.index(self.champion)
        if self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] == 'orange':
            self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] = 'red'
        else:
            self.colour_columns[2 + (self.player_cnt * 2) + (self.matching_cnt * 2)][matched_champ_cnt] = 'yellow'

    def reset_current_column_info(self):
        """
        Clear all of the current column info before processing the next player
        """
        self.current_column = []
        self.current_column_amount = []
        self.colour_current_column = []
        self.total_mastery_score = 0
        self.column_mastery_scores = []

    def get_top_champs(self, mastery_information: dict):
        """
        Get the 10 highest mastery champions

        :param mastery_information: Mastery information for the current player
        """
        for cnt, champion_info in enumerate(mastery_information.items()):
            if cnt == 10:
                break

            # For regular table
            self.current_column.append(champion_info[0])
            self.current_column_amount.append(self.format_mastery_points(champion_info[1]['mastery']))

            # For colouring
            self.total_mastery_score += champion_info[1]['mastery']
            self.column_mastery_scores.append(champion_info[1]['mastery'])

        # Pad the column if they have less than 10 champs played
        while len(self.current_column) < 10:
            self.current_column.append('')
            self.current_column_amount.append('')

        self.columns.append(self.current_column)
        self.columns.append(self.current_column_amount)

    @staticmethod
    def format_mastery_points(amount: int) -> str:
        """
        Format the number of mastery points into a short form

        :param amount: Number of mastery points
        :return: Formatted number of mastery points
        """
        if amount > 1000000:
            return f'{amount/1000000:.1f} M'
        elif amount > 1000:
            return f'{amount/1000:.1f} K'
        else:
            return f'{amount}'

    def add_high_mastery_colour(self):
        """
        Create the colour table for the mastery shared table
        """
        for cnt, mastery_amount in enumerate(self.column_mastery_scores):
            if mastery_amount >= self.total_mastery_score * .15:
                self.column_mastery_scores[cnt] = 'orange'
            else:
                self.column_mastery_scores[cnt] = ''

        # Add padding for players with less than 10 champs played
        while len(self.column_mastery_scores) < 10:
            self.column_mastery_scores.append('')
        self.colour_columns.append(self.column_mastery_scores)
        self.colour_columns.append(self.column_mastery_scores)
