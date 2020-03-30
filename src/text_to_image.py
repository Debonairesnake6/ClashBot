"""
This file will create an image from the input as a table
"""

import prettytable
from PIL import Image, ImageDraw, ImageFont


class CreateImage:
    """
    Create an image from the given input
    """
    def __init__(self, titles: list, rows: list, file_name: str, colour: list = False, convert_columns: bool = False,
                 title_colours: list = False):
        """
        Create an image from the given input

        :param titles: List of names to use for the titles of each column
        :param rows: List of rows to add to the table
        :param file_name: Name to save the file as
        :param colour: Dual array of colours to colour each word in the table
        :param convert_columns: Convert the riven rows from columns into rows
        :param title_colours: Array of colours to paint the titles with
        """
        self.titles = titles
        self.rows = rows
        self.table = None
        self.table_to_image = None
        self.file_name = file_name
        self.colour = colour
        self.convert_columns = convert_columns
        self.title_colours = title_colours

        # Setup and add rows to the table
        self.setup()
        self.add_rows()

        # Create the image from the table
        self.turn_into_image()
        self.save_image()

    def setup(self):
        """
        Create the table object and add the titles
        """
        self.table = prettytable.PrettyTable()
        self.table.field_names = self.titles
        if self.convert_columns:
            self.rows = self.convert_columns_to_rows(self.rows)
            if self.colour:
                self.colour = self.convert_columns_to_rows(self.colour)

    def add_rows(self):
        """
        Add each row to the table
        """
        for row in self.rows:
            self.table.add_row(row)

    def turn_into_image(self):
        """
        Turn the table into an image
        """
        if self.title_colours:
            self.table_to_image = TableToImage(self.table.get_string(), self.colour, self.rows, self.titles,
                                               self.title_colours)
        else:
            self.table_to_image = TableToImage(self.table.get_string(), self.colour, self.rows)

    def save_image(self):
        """
        Save the image as the given file name
        """
        self.table_to_image.img.save(self.file_name)

    def convert_columns_to_rows(self, columns: list):
        """
        Convert the given columns into rows to be able to create the image

        :param columns: List of columns to convert
        """
        fixed_rows = self.create_row_for_max_column_length(columns)
        return self.add_data_from_columns_into_rows(columns, fixed_rows)

    @staticmethod
    def create_row_for_max_column_length(columns) -> list:
        """
        Create a rows to match the longest column length in the given array

        :param columns: List of columns to create placeholder rows for
        :return: Array with rows fitting the max length of the given columns
        """
        fixed_rows = []
        for column in range(len(max(columns))):
            fixed_rows.append([])
        return fixed_rows

    @staticmethod
    def add_data_from_columns_into_rows(columns: list, fixed_rows: list):
        """
        Add the given data into the fixed_rows array

        :param columns: List of columns to convert into rows
        :param fixed_rows: Array with fixed positions converting columns into rows
        """
        for column in range(len(max(columns))):
            for row in range(len(columns)):
                try:
                    fixed_rows[column].append(columns[row][column])
                except IndexError:
                    fixed_rows[column].append('')
        return fixed_rows


class TableToImage:
    """
    Create an image from the text table given to it
    """

    def __init__(self, table: str, table_colour: list = False, original_rows: list = False, titles: list = False,
                 title_colours: list = False):
        """
        Create an image from the text table given to it

        :param table: String of table to create
        :param table_colour: Array of colour to print
        :param original_rows: Array of original rows to use for colouring
        :param titles: Name of each title if they need to be coloured
        :param title_colours: What to colour each title
        """
        self.img = None
        self.font = None
        self.draw = None
        self.processed = None
        self.row_cnt = None
        self.column_cnt = None
        self.table = table
        self.table_colour = table_colour
        self.original_rows = original_rows
        self.titles = titles
        self.title_colours = title_colours
        self.colour = None
        self.word = None
        self.colours = {
            '': (255, 255, 255),
            'red': (255, 0, 0),
            'orange': (255, 106, 0),
            'yellow': (255, 255, 0),
            'blue': (50, 150, 255),
            'green': (0, 153, 51),
            'iron': (91, 82, 83),
            'bronze': (136, 75, 48),
            'silver': (134, 158, 166),
            'gold': (201, 136, 52),
            'platinum': (62, 121, 120),
            'diamond': (131, 184, 215),
            'master': (146, 100, 182),
            'grandmaster': (214, 51, 46),
            'challenger': (255, 154, 43),
            'black': (0, 0, 0),
            'unranked': (255, 255, 255)
        }

        self.setup_image()
        if table_colour:
            self.colour_image()
        if title_colours:
            self.colour_titles()

    def setup_image(self):
        """
        Basic setup for the image to set the size, font, background colour, and all of the text in black
        """
        # Create the correct size image for the table
        rows = self.table.count('\n')
        columns = self.table.split('\n')[0].count('-') + self.table.split('\n')[0].count('+')
        self.img = Image.new('RGB', ((columns * 12) + 24, rows * 21 + 48), color=(54, 57, 63))

        # Initialize font and drawing object
        self.font = ImageFont.truetype('../extra_files/cour.ttf', 20)
        self.draw = ImageDraw.Draw(self.img)

        # Draw the table without markings
        for x in range(5):
            self.draw.text((12, 12), self.table, font=self.font, fill=(255, 255, 255))

    def colour_image(self):
        """
        Colour the image based on the array
        """
        for row_cnt, colour_row in enumerate(self.table_colour):
            self.processed = []
            for column_cnt, colour in enumerate(colour_row):
                self.row_cnt = row_cnt + 3
                self.column_cnt = column_cnt
                self.colour = colour
                self.word = self.original_rows[self.row_cnt - 3][self.column_cnt]
                self.colour_specific_word()

    def colour_titles(self):
        """
        Colour the titles based on the information given
        """
        self.processed = []
        for colour_cnt, title_colour in enumerate(self.title_colours):
            self.row_cnt = 1
            self.word = self.titles[colour_cnt]
            self.colour = title_colour
            self.colour_specific_word()

    def colour_specific_word(self):
        """
        Colour the specific word based on the row and column count
        """
        if self.colour != '':
            row_string = self.table.split('\n')[self.row_cnt]

            # If word only appears once
            if row_string.count(self.word) == 1:
                x_position = row_string.index(self.word)

            # If the word appears multiple times
            else:
                x_position = [x_pos for x_pos in range(len(row_string)) if
                              row_string.startswith(self.word, x_pos)][self.processed.count(self.word)]

            # Fill with black first
            for x in range(5):
                self.draw.text(((x_position * 12) + 12, (self.row_cnt * 21) + 12),
                               self.word, font=self.font,
                               fill=self.colours['black'])

            # Fill with the desired colour
            for x in range(5):
                self.draw.text(((x_position * 12) + 12, (self.row_cnt * 21) + 12),
                               self.word, font=self.font,
                               fill=self.colours[self.colour])
        self.processed.append(self.word)


if __name__ == '__main__':

    # # CreateImage
    # data = [['Zilean', '208.7 K', 'Zilean', '301.1 K', 'Zilean', '48.2 K', 'Nami', '601.4 K', 'Talon', '120.6 K'], ['Maokai', '208.2 K', 'LeeSin', '266.2 K', 'Braum', '38.2 K', 'Karma', '332.2 K', 'Orianna', '106.9 K'], ['Brand', '148.0 K', 'Thresh', '240.5 K', 'Malphite', '37.9 K', 'Lulu', '269.2 K', 'Zyra', '50.3 K'], ['Janna', '109.2 K', 'Tristana', '109.9 K', 'LeeSin', '36.9 K', 'Brand', '211.9 K', 'Gangplank', '47.2 K'], ['Ezreal', '95.9 K', 'Zed', '108.3 K', 'Nautilus', '33.8 K', 'Ahri', '139.8 K', 'Kayle', '46.2 K'], ['KogMaw', '91.5 K', 'Graves', '101.3 K', 'Brand', '30.6 K', 'Sona', '87.9 K', 'Fiora', '37.8 K'], ['Gangplank', '81.1 K', 'Lucian', '87.7 K', 'TahmKench', '30.1 K', 'Yuumi', '67.1 K', 'Morgana', '29.9 K'], ['Karthus', '77.9 K', 'Jhin', '78.8 K', 'Graves', '29.9 K', 'Rakan', '43.4 K', 'Illaoi', '27.5 K'], ['DrMundo', '69.9 K', 'Yasuo', '75.0 K', 'Viktor', '24.3 K', 'Sivir', '39.0 K', 'Lulu', '25.6 K'], ['Kaisa', '65.0 K', 'Caitlyn', '73.4 K', 'Orianna', '20.3 K', 'Soraka', '32.8 K', 'Lux', '23.7 K']]
    # colour = [['orange', 'orange', 'red', 'red', 'yellow', 'yellow', 'orange', 'orange', 'orange', 'orange'], ['orange', 'orange', 'red', 'red', '', '', 'orange', 'orange', 'red', 'red'], ['yellow', 'yellow', 'red', 'red', '', '', 'yellow', 'yellow', '', ''], ['', '', '', '', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow'], ['', '', '', '', '', '', '', '', '', ''], ['', '', 'yellow', 'yellow', 'yellow', 'yellow', '', '', '', ''], ['yellow', 'yellow', '', '', '', '', '', '', '', ''], ['', '', '', '', 'yellow', 'yellow', '', '', '', ''], ['', '', '', '', '', '', '', '', 'yellow', 'yellow'], ['', '', '', '', 'yellow', 'yellow', '', '', '', '']]
    # titles = ['Debonairesnake6', '#1', 'In Vänity', '#2', 'Wosko', '#3', 'Smol Squish', '#4', 'Ori Bot', '#5']
    # tmp = CreateImage(titles, data, 'test.png', colour=colour, convert_columns=False)
    # tmp.table_to_image.img.show()
    # print()

    import shelve
    create_image_copy = dict(shelve.open('../extra_files/my_api')['title_colours'])
    titles = ['Debonairesnake6', '#1', 'In Vänity', '#2', 'Wosko', '#3', 'Smol Squish', '#4', 'Ori Bot', '#5']
    title_colours = ['iron', 'bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster', 'challenger', 'iron']
    new = TableToImage(create_image_copy['table'], create_image_copy['table_colour'],
                       create_image_copy['original_rows'], titles, title_colours)
    new.img.save('test.png')
    print()
