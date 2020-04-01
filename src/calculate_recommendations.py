"""
This file generates a ban list based on the tables given to it
"""

import operator
import shelve

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
        self.current_table_value = None
        self.points = None
        self.column_total_value = None

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
        CreateImage(self.titles, self.columns, '../extra_files/ban_recommendations.png',
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
        self.total_ban_points = sum([float(total) for total in self.points_column if total != ''])
        colours = []
        for points in self.points_column:
            try:
                points = float(points)
            except ValueError:
                colours.append('')
            else:
                if points > self.total_ban_points * 0.09:
                    colours.append('red')
                elif points > self.total_ban_points * 0.07:
                    colours.append('orange')
                elif points > self.total_ban_points * 0.05:
                    colours.append('yellow')
                else:
                    colours.append('')
            # self.colour_columns.append(colours)
        self.colour_columns.append(colours)

    def get_top_champs(self):
        """
        Get the 15 highest scoring champs
        """
        for _ in range(15):
            try:
                champ_name = max(self.ban_dict.items(), key=operator.itemgetter(1))[0]
            except ValueError:
                self.champion_column.append('')
                self.points_column.append('')
            else:
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
            if isinstance(table_type[0][0], list):
                self.current_table = table_type[0]
                self.current_colours = table_type[1]
            else:
                self.current_table = [table_type[0]]
                self.current_colours = [table_type[1]]
            self.process_single_table()

    def process_single_table(self):
        """
        Process a single table at a time
        """
        for column_cnt, column in enumerate(self.current_table[::2]):
            self.calculate_column_total_value(self.current_table[(column_cnt * 2) + 1])
            if not self.current_table[(column_cnt * 2) + 1][0].replace('.', '').strip().isdigit():
                fixed_column_values = self.format_mastery_values(self.current_table[(column_cnt * 2) + 1])
            else:
                fixed_column_values = self.current_table[(column_cnt * 2) + 1]
            for row_cnt, champ_name in enumerate(column):
                if champ_name != '':
                    self.current_champ = champ_name
                    self.current_colour = self.current_colours[column_cnt][row_cnt]
                    self.current_table_value = fixed_column_values[row_cnt]
                    self.calculate_points()

    def calculate_column_total_value(self, column: list):
        """
        Calculate the total value

        :param column: Current column to grab to total value from
        """
        if not column[0].replace('.', '').strip().isdigit():
            column = self.format_mastery_values(column)
            self.calculate_column_total_value(column)
        else:
            self.calculate_column_values(column)

    @staticmethod
    def format_mastery_values(column: list):
        """
        Convert mastery points into actual numbers

        :param column: List containing mastery values
        :return: Column showing values rather than short form
        """
        fixed_column = []
        for row in column:
            if row.split(' ')[1] == 'K':
                fixed_column.append(str(int(float(row.split()[0]) * 1000)))
            elif row.split(' ')[1] == 'M':
                fixed_column.append(str(int(float(row.split()[0]) * 1000000)))
            else:
                fixed_column.append(row)
        return fixed_column

    def calculate_column_values(self, column: list):
        """
        Calculate total value for the given column

        :param column: List containing a column
        """
        self.column_total_value = sum([int(value) for value in column if value != ''])

    def calculate_points(self):
        """
        Calculate points based on the colour of the champion
        """
        self.get_points_by_table_value()
        self.get_points_by_colour()

        # Add the champions points to the dictionary
        self.ban_dict[self.current_champ] = float(f'{self.ban_dict.get(self.current_champ, 0.0) + self.points:.2f}')

    def get_points_by_colour(self):
        """
        Calculate points based on the colour modification
        """
        if self.current_colour == 'red' or self.current_colour == 'yellow':
            self.points = self.points * 1.1

    def get_points_by_table_value(self):
        """
        Calculate points based on the value in the table
        """
        self.points = 1000 * (int(self.current_table_value) / self.column_total_value)


if __name__ == '__main__':
    from api_queries import APIQueries
    shelf = shelve.open('../extra_files/my_api')
    shelf = dict(shelf)['combined_tables']
    calc = CalculateBanRecommendations([shelf])
    print()
