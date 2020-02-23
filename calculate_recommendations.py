import prettytable

from PIL import Image, ImageDraw, ImageFont


class Calculate:
    """
    Calculate object for getting the total points of each champion
    """

    def __init__(self, table, ban_list=None):
        self.table = table
        self.img = None
        self.font = None
        self.draw = None
        self.bans_table = None
        self.total_ban_points = 0

        # Check if importing ban_list from previous table
        if ban_list is None:
            self.ban_list = {}
        else:
            self.ban_list = ban_list

        # Get the points of all of the champions
        self.get_champ_from_table()

        # Sort the list
        self.sorted_ban_list = []
        for champion in sorted(self.ban_list, key=self.ban_list.get, reverse=True):
            self.sorted_ban_list.append([champion, self.ban_list[champion]])

        # TODO: Don't do this automatically, wait until all tables have been calculated before creating the image
        # Create the image
        # self.create_table()
        # self.create_image()
        # self.add_colour()

    def get_champ_from_table(self):
        """
        Get the champion name and modifier from the table
        """

        # Split the table into rows
        for champion in self.table.split('\n')[3:-1]:

            # Grab the champion with modifier in each row
            for champion_with_modifier in champion.split('|')[1:-1]:

                # Check if the champion has a modifier
                if ':' in champion_with_modifier:

                    # Get the champion name and modifier
                    champion_name = champion_with_modifier.strip()[3:-3]
                    modifier = champion_with_modifier.strip()[:2]

                else:
                    champion_name = champion_with_modifier.strip()
                    modifier = ''

                # Skip if there is no champion
                if champion_name == '':
                    continue

                if champion_name.isdigit():
                    print()

                # Calculate the points for the champion
                self.calculate_points(champion_name, modifier)

    def calculate_points(self, champion_name, modifier):
        """
        Calculate points based on the modifier
        :param champion_name: Champion name
        :param modifier: Modifier from the table
        """

        # Base points for the champion
        points = 100.0

        # Dictionary holding each rank of modifier
        red = {'60', 'HS', '2S'}
        orange = {'30', 'H ', '2 '}
        yellow = {'S ', '1S'}
        blue = {'1 '}
        green = {'_S'}

        # Calculate points based on modifier (shared champs worth less as they are added multiple times)
        if modifier in red:
            points = points * 1.75
        elif modifier in orange:
            points = points * 2
        elif modifier in yellow:
            points = round(points * 1.15, 2)
        elif modifier in blue:
            points = points * 1.4
        elif modifier in green:
            points = points * 0.75

        # Add the champions points to the dictionary
        if champion_name not in self.ban_list:
            self.ban_list[champion_name] = points
        else:
            self.ban_list[champion_name] = self.ban_list[champion_name] + points

    def create_table(self):
        """
        Create the text version of the table as a string
        """

        # Create the table
        self.bans_table = prettytable.PrettyTable()

        # Add the field names
        self.bans_table.field_names = ['Champion', 'Points']

        # Add each champion to the table
        for champion_cnt, champion in enumerate(self.sorted_ban_list):

            # Quit after 10 champs
            if champion_cnt == 10:
                break

            # Add the current champion to the table
            self.bans_table.add_row([champion[0], champion[1]])

        # Save as a string
        self.bans_table = self.bans_table.get_string()

        # Create the image and add the colour
        self.create_image()
        self.add_colour()

        # Return the image
        return self.img

    def create_image(self):
        """
        Turn the string table into an image
        """

        # Create the correct size image for the table
        rows = self.bans_table.count('\n')
        columns = self.bans_table.split('\n')[0].count('-') + self.bans_table.split('\n')[0].count('+')
        self.img = Image.new('RGB', ((columns * 12), rows * 21 + 21), color=(54, 57, 63))

        # Initialize font and drawing object
        self.font = ImageFont.truetype('cour.ttf', 20)
        self.draw = ImageDraw.Draw(self.img)

        # Draw the table
        self.draw.text((0, 0), self.bans_table, font=self.font, fill=(255, 255, 255))

    def add_colour(self):
        """
        Add colour to the score of each champion
        """

        # Get the total points for the top 10 bans
        for points_cnt, points in enumerate(self.sorted_ban_list):

            # Only grab the first 10
            if points_cnt == 10:
                break
            self.total_ban_points += points[1]

        # Loop through each item in the list to assign colour
        for line_cnt, line in enumerate(self.bans_table.split('\n')):

            # Skip the header and footer
            if line_cnt < 3 or line_cnt == len(self.bans_table.split('\n')) - 1:
                continue

            # Grab the points and colour them
            self.select_colour(score=line.split('|')[2].strip(), line_cnt=line_cnt, line=line)

    def select_colour(self, score, line_cnt, line):
        """
        Select the colour of the score
        :param score: Score to pick the colour of
        :param line_cnt: Line the score appeared on
        :param line: The line the score is located on
        """

        print(f'{score}: {(float(score) / self.total_ban_points) * 100}')

        # Red if +25% of the total
        if float(score) / self.total_ban_points > 0.11:
            for _ in range(5):
                self.draw.text((line.index(score) * 12, line_cnt * 21), score, font=self.font, fill=(255, 0, 0))

        # Orange if +17% of total
        elif float(score) / self.total_ban_points > 0.10:
            for _ in range(5):
                self.draw.text((line.index(score) * 12, line_cnt * 21), score, font=self.font, fill=(255, 51, 0))

        # Yellow if +10% of total
        elif float(score) / self.total_ban_points > 0.09:
            for _ in range(5):
                self.draw.text((line.index(score) * 12, line_cnt * 21), score, font=self.font, fill=(255, 153, 0))

    def get_ban_list(self):
        """
        Return the ban_list
        :return: The ban_list
        """

        return self.ban_list


if __name__ == '__main__':
#     tmp = Calculate('''+--------------+------------------+----------------+--------------+----------------+
# |     ßøé      |      Tempos      |    Gobleeto    |    Anita     | GyrosSteelBall |
# +--------------+------------------+----------------+--------------+----------------+
# | HS:ZileanHS: |   HS:ZileanHS:   |  H :SyndraH :  | HS:ZileanHS: |  HS:ZileanHS:  |
# |    Ezreal    |       Sona       |  HS:ZileanHS:  |   Morgana    |     Twitch     |
# |    Xerath    |       Nami       | H :VladimirH : |    Teemo     |     Rammus     |
# | S :VeigarS : |       Lulu       |     Xayah      |    Nasus     |      Jax       |
# |     Jhin     |   S :KarmaS :    |      Ekko      |    Soraka    |     Kayle      |
# |  Gangplank   |   S :ThreshS :   |     Vayne      |    Janna     |    Shyvana     |
# |    Soraka    |      Rakan       |     Yorick     |  Blitzcrank  |    Alistar     |
# |    Brand     |     Nautilus     |  S :VeigarS :  |    Karma     |     KogMaw     |
# |    Thresh    | S :BlitzcrankS : |     Yasuo      |   Malphite   |      Olaf      |
# |     Ashe     |  S :MorganaS :   |      Bard      |  Cassiopeia  |     Anivia     |
# +--------------+------------------+----------------+--------------+----------------+''')
    tmp = Calculate(''''+-----------------+--------------+---------------+-------------+-------------+
| Debonairesnake6 |  In Vänity   |     Wosko     | Smol Squish |   Ori Bot   |
+-----------------+--------------+---------------+-------------+-------------+
|      Maokai     | H :VayneH :  |  HS:ThreshHS: |  H :NamiH : | H :TalonH : |
|   H :ZileanH :  | HS:LeeSinHS: |     Braum     | H :KarmaH : |   Orianna   |
|   S :BrandS :   | HS:ThreshHS: |    Malphite   |     Lulu    |     Zyra    |
|      Janna      |     Zed      |  S :LeeSinS : |    Brand    |  Gangplank  |
|      Ezreal     |   Tristana   |  S :GravesS : |     Ahri    |    Kayle    |
|      KogMaw     | S :GravesS : |   TahmKench   |     Sona    |    Fiora    |
| S :GangplankS : |    Lucian    |  S :BrandS :  |    Yuumi    |   Morgana   |
|     Karthus     |     Jhin     |     Viktor    |    Rakan    |    Illaoi   |
|     DrMundo     |    Yasuo     |    Nautilus   |    Sivir    |     Lulu    |
|       Zoe       |   Caitlyn    | S :OriannaS : |    Soraka   |     Lux     |
+-----------------+--------------+---------------+-------------+-------------+''')
    print()
