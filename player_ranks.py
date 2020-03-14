"""
This file will gather all of the information needed to create a table showing each player's rank
"""

from text_to_image import CreateImage


class PlayerRanks:
    """
    Handle creating the player ranks table
    """
    def __init__(self, api_results: object):
        """
        Handle creating the player ranks table

        :param api_results: Results from the api_queries file
        """
        self.api_results = api_results
        self.titles = None
        self.columns = []
        self.player_column = []
        self.rank_column = []
        self.colour_columns = []
        self.titles = ['Player', 'Rank']
        self.player_ranked_info = None
        self.player_name = None

        self.setup()

    def setup(self):
        """
        Run the major functions of the object
        """
        self.process_every_player()
        self.set_colour_columns()
        self.create_image()

    def create_image(self):
        """
        Create the image from the processed results
        """
        CreateImage(self.titles, self.columns, 'extra_files/player_ranks.png',
                    colour=self.colour_columns, convert_columns=True)

    def process_every_player(self):
        """
        Process every player to grab their rank
        """
        for player_name in self.api_results.player_information:
            self.player_name = player_name
            self.player_ranked_info = self.api_results.player_information[player_name]['ranked_info']
            self.process_single_player()
        self.columns.append(self.player_column)
        self.columns.append(self.rank_column)

    def process_single_player(self):
        """
        Process a single player to grab their rank
        """
        self.player_column.append(self.player_name)
        self.rank_column.append(f'{self.player_ranked_info["tier"]} {self.player_ranked_info["rank"]}')

    def set_colour_columns(self):
        """
        Set the colour depending on the player ranks
        """
        colours = []
        for row in self.rank_column:
            colours.append(row.split()[0].lower())
        self.colour_columns.append(colours)
        self.colour_columns.append(colours)


if __name__ == '__main__':
    import shelve
    from api_queries import APIQueries
    api_info = shelve.open('my_api')['api']
    tmp = PlayerRanks(api_info)
    print()
