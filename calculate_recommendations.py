"""
This file generates a ban list based on the tables given to it
"""

import operator

from text_to_image import CreateImage


class CalculateBanRecommendations:
    """
    Calculate object for getting the total points of each champion
    """

    def __init__(self, combined_tables: list):
        """
        Calculate object for getting the total points of each champion

        :param combined_tables: Array of each table for the other queries along with their colour codes
        """
        self.combined_tables = combined_tables
        self.titles = ['Champion', 'Points']
        self.current_table = None
        self.current_colours = None
        self.current_champ = None
        self.current_colour = None
        self.ban_dict = {}
        self.total_ban_points = 0
        self.columns = []
        self.colour_columns = []
        self.champion_column = []
        self.points_column = []

        self.setup()

    def setup(self):
        """
        Run the main functions of the object
        """
        self.process_every_table()
        self.process_top_ten_champs()
        self.create_image()

    def create_image(self):
        """
        Create image from the processed results
        """
        CreateImage(self.titles, self.columns, 'extra_files/ban_recommendations.png',
                    colour=self.colour_columns, convert_columns=True)

    def process_top_ten_champs(self):
        """
        Create a list of the top 10 champs and colour them accordingly
        """
        self.get_top_champs()
        self.colour_top_ten_champs()

    def colour_top_ten_champs(self):
        """
        Colour the top 10 champs based on how much score they have
        """
        self.total_ban_points = sum([float(total) for total in self.points_column])
        colours = []
        for points in self.points_column:
            points = float(points)
            if points > self.total_ban_points * 0.09:
                colours.append('red')
            elif points > self.total_ban_points * 0.08:
                colours.append('orange')
            elif points > self.total_ban_points * 0.06:
                colours.append('yellow')
            else:
                colours.append('')
        self.colour_columns.append(colours)
        self.colour_columns.append(colours)

    def get_top_champs(self):
        """
        Get the 15 highest scoring champs
        """
        for _ in range(15):
            champ_name = max(self.ban_dict.items(), key=operator.itemgetter(1))[0]
            points = str(self.ban_dict.pop(champ_name))
            self.champion_column.append(champ_name)
            self.points_column.append(points)
        self.columns.append(self.champion_column)
        self.columns.append(self.points_column)

    def process_every_table(self):
        """
        Process every table given in the combined tables list
        """
        for table_type in self.combined_tables:
            self.current_table = table_type[0]
            self.current_colours = table_type[1]
            self.process_single_table()

    def process_single_table(self):
        """
        Process a single table at a time
        """
        for column_cnt, column in enumerate(self.current_table):
            for row_cnt, champ_name in enumerate(column):
                if champ_name != '':
                    self.current_champ = champ_name
                    self.current_colour = self.current_colours[column_cnt][row_cnt]
                    self.calculate_points()

    def calculate_points(self):
        """
        Calculate points based on the colour of the champion
        """

        # Base points for the champion
        points = 100.0

        # Calculate points based on modifier (shared champs worth less as they are added multiple times)
        if self.current_colour == 'red':
            points = points * 1.75
        elif self.current_colour == 'orange':
            points = points * 2
        elif self.current_colour == 'yellow':
            points = round(points * 1.15, 2)
        elif self.current_colour == 'blue':
            points = points * 1.4
        elif self.current_colour == 'green':
            points = points * 0.75

        # Add the champions points to the dictionary
        self.ban_dict[self.current_champ] = self.ban_dict.get(self.current_champ, 0) + points
