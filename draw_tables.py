from PIL import Image, ImageDraw, ImageFont


class DrawTable:

    def __init__(self, table):
        self.img = None
        self.font = None
        self.draw = None
        self.table = table

        self.setup_image()
        self.colour_image()

    def setup_image(self):

        # Create the correct size image for the table
        rows = self.table.count('\n')
        columns = self.table.split('\n')[0].count('-') + self.table.split('\n')[0].count('+')
        self.img = Image.new('RGB', ((columns * 12), rows * 21 + 21), color=(54, 57, 63))

        # Initialize font and drawing object
        self.font = ImageFont.truetype('cour.ttf', 20)
        self.draw = ImageDraw.Draw(self.img)

        # Draw the table without markings
        self.draw.text((0, 0), self.replace_modifiers(), font=self.font, fill=(255, 255, 255))

    def replace_modifiers(self):

        # Array of modifiers used
        modifier_array = ['30', '60', 'HS', 'H ', 'S ', '2S', '2 ', '1S', '1 ', '_S']

        # Placeholder of the table
        table = self.table

        # Remove each modifier on the table
        for modifier in modifier_array:
            table = table.replace(f'{modifier}:', '   ')

        return table

    def colour_image(self):

        # Loop through each item in the list to assign colour
        for line_cnt, line in enumerate(self.table.split('\n')):

            # Skip the header and footer
            if line_cnt < 3 or line_cnt == len(self.table.split('\n')) - 1:
                continue

            # Grab each word in the row
            for word_cnt, word in enumerate(line.split('|')[1:-1]):

                # Skip if nothing
                if len(word) < 1:
                    continue

                # Skip not special values
                if ':' not in word:
                    continue

                # Get the modifier and colour accordingly
                else:
                    modifier, word, _ = word.strip().split(':')
                    self.select_colour(modifier, word, line, line_cnt, word_cnt)

    def select_colour(self, modifier, word, line, line_cnt, word_cnt):

        # Get the horizontal position of the word
        if not line.index(word) == 1:

            # Get numbers of pixel from the left border to the word
            column_width = [0]
            for champion_name_cnt, champion_name in enumerate(line.split('|')[1:-2]):

                # Add the previous to the total for that word
                if len(column_width) == 1:
                    column_width.append(len(champion_name) + 1)
                else:
                    column_width.append(len(champion_name) + column_width[champion_name_cnt] + 1)

            # Get the pixel to draw the champion name on
            champion_name = line.split('|')[1:-1][word_cnt]
            column_cnt = column_width[word_cnt] + champion_name.\
                index(champion_name.replace(f'{modifier}:', '').strip()) + 1

        # Otherwise just get the index of the word
        else:
            column_cnt = line.index(word)

        # Put black behind the text if it isn't blue
        if modifier != '30' or modifier != 'H ' or modifier != '2 ':

            # Cover with black to bold the colours
            self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(0, 0, 0))

        for cnt in range(5):

            # Lane Play Rate -------------------------------------------------------------------------------------------
            # Colour red for +60 games
            if modifier == '60':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 0, 0))

            # Colour orange for +30 games
            elif modifier == '30':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 51, 0))

            # Mastery Shared--------------------------------------------------------------------------------------------
            # Colour red for high mastery and shared
            elif modifier == 'HS':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 0, 0))

            # Colour orange high mastery
            elif modifier == 'H ':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 51, 0))

            # Colour yellow for shared
            elif modifier == 'S ':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 153, 0))

            # Recent Champion/Clash Ranked------------------------------------------------------------------------------
            # Colour red for +25 games and shared
            elif modifier == '2S':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 0, 0))

            # Colour orange for +25 games
            elif modifier == '2 ':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 51, 0))

            # Colour yellow for shared
            elif modifier == '1S':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(255, 153, 0))

            # Colour blue for +10 games and shared
            elif modifier == '1 ':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(0, 102, 255))

            # Colour green for shared
            elif modifier == '_S':
                self.draw.text((column_cnt * 12, line_cnt * 21), word[:-2], font=self.font, fill=(0, 153, 51))

    def get_image(self):
        return self.img


if __name__ == '__main__':
    draw_table = DrawTable('''+--------------+------------------+----------------+--------------+----------------+
|     ßøé      |      Tempos      |    Gobleeto    |    Anita     | GyrosSteelBall |
+--------------+------------------+----------------+--------------+----------------+
| HS:ZileanHS: |   HS:ZileanHS:   |  H :SyndraH :  | HS:ZileanHS: |  HS:ZileanHS:  |
|    Ezreal    |       Sona       |  HS:ZileanHS:  |   Morgana    |     Twitch     |
|    Xerath    |       Nami       | H :VladimirH : |    Teemo     |     Rammus     |
| S :VeigarS : |       Lulu       |     Xayah      |    Nasus     |      Jax       |
|     Jhin     |   S :KarmaS :    |      Ekko      |    Soraka    |     Kayle      |
|  Gangplank   |   S :ThreshS :   |     Vayne      |    Janna     |    Shyvana     |
|    Soraka    |      Rakan       |     Yorick     |  Blitzcrank  |    Alistar     |
|    Brand     |     Nautilus     |  S :VeigarS :  |    Karma     |     KogMaw     |
|    Thresh    | S :BlitzcrankS : |     Yasuo      |   Malphite   |      Olaf      |
|     Ashe     |  S :MorganaS :   |      Bard      |  Cassiopeia  |     Anivia     |
+--------------+------------------+----------------+--------------+----------------+''')
    draw_table.get_image().show()
