import os
import urllib
import time
import sys
import api_queries

from discord import File
from discord.ext import commands
from calculate_recommendations import CalculateBanRecommendations
from mastery_shared import MasteryShared
from role_rate import RoleRate
from recent_champion import RecentChampion
from player_ranks import PlayerRanks


class ClashBot:
    """
    Clash Discord bot
    """
    def __init__(self):

        # Placeholder variables
        self.bot = commands.Bot(command_prefix='!')
        self.message = None
        self.legend = None
        self.player_list = []
        self.severity = ['Red', 'Orange', 'Yellow', 'Blue', 'Green']
        self.api_info = None
        self.roll_rate = None
        self.mastery_shared = None
        self.recent_champion = None
        self.clash_ranked = None

    async def get_role_rate_table(self):
        """
        Parse the player list to generate the role rate table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Lane Play Rate Legend:' \
                      f'\n\t- {self.severity[0]}:\t>50% play rate' \
                      f'\n\t- {self.severity[1]}:\t>25% play rate'
        self.roll_rate = RoleRate(self.api_info)
        await self.post_to_discord()

    async def get_mastery_shared_table(self):
        """
        Parse the player list to generate the mastery shared table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Mastery/Shared Pool Legend:' \
                      f'\n\t- {self.severity[0]}:\tHigh mastery points and shared champ' \
                      f'\n\t- {self.severity[1]}:\tHigh mastery points' \
                      f'\n\t- {self.severity[2]}:\tShared champ' \
                      '\nNOTE: Champions not played with the past 30 days have their highlighting removed'
        self.mastery_shared = MasteryShared(self.api_info)
        await self.post_to_discord()

    async def get_recent_champion_table(self):
        """
        Parse the player list to generate the recent champion table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Recent Champion Legend:' \
                      f'\n\t- {self.severity[0]}:\t+25 games and shared champ' \
                      f'\n\t- {self.severity[1]}:\t+25 games' \
                      f'\n\t- {self.severity[2]}:\t+10 games and shared champ' \
                      f'\n\t- {self.severity[3]}:\t+10 games' \
                      f'\n\t- {self.severity[4]}:\tShared champ' \
                      f'\nNOTE: This list does not include ARAM or Poro King games'
        self.recent_champion = RecentChampion(self.api_info, 'all_match_history')
        await self.post_to_discord()

    async def get_clash_ranked_table(self):
        """
        Parse the player list to generate the clash ranked table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Clash and Ranked Legend:' \
                      f'\n\t- {self.severity[0]}:\t+25 games and shared champ' \
                      f'\n\t- {self.severity[1]}:\t+25 games' \
                      f'\n\t- {self.severity[2]}:\t+10 games and shared champ' \
                      f'\n\t- {self.severity[3]}:\t+10 games' \
                      f'\n\t- {self.severity[4]}:\tShared champ'
        self.clash_ranked = RecentChampion(self.api_info, 'ranked_match_history')
        await self.post_to_discord()

    async def get_player_ranks_table(self):
        """
        Parse the player list to get the player ranks table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Player Ranks Table:'
        PlayerRanks(self.api_info)
        await self.post_to_discord()

    async def get_ban_recommendation_table(self):
        """
        Parse the player list to generate the ban recommendation table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Ban List Legend:' \
                      f'\n\t- {self.severity[0]}:\t+11% of top 10 score' \
                      f'\n\t- {self.severity[1]}:\t+10% of top 10 score' \
                      f'\n\t- {self.severity[2]}:\t+9% of top 10 score'
        combined_tables = [[self.mastery_shared.columns[::2], self.mastery_shared.colour_columns[::2]],
                           [self.recent_champion.columns[::2], self.recent_champion.colour_columns[::2]],
                           [self.clash_ranked.columns[::2], self.clash_ranked.colour_columns[::2]]]
        CalculateBanRecommendations(combined_tables)
        await self.post_to_discord()

    async def post_to_discord(self):
        """
        Post the gathered information to discord
        """
        message_sent = False
        for _, _, filenames in os.walk('extra_files'):
            for file in filenames:
                if file[-4:] == '.png':
                    await self.message.channel.send(self.legend, file=File(f'extra_files/{file}', filename=file))
                    os.remove(f'extra_files/{file}')
                    message_sent = True

        if not message_sent:
            await self.message.channel.send(self.legend)

    async def get_all_tables(self):
        """
        Get all of the different types of tables for each player given
        """
        await self.get_role_rate_table()
        await self.get_mastery_shared_table()
        await self.get_recent_champion_table()
        await self.get_clash_ranked_table()
        await self.get_player_ranks_table()
        await self.get_ban_recommendation_table()

    async def parse_discord_message(self):
        """
        Parse the discord message to grab each summoner name given
        """
        # Get the first 5 player names give
        for player_name_cnt, player_name in enumerate(self.message.content[7:].split(',')):
            if player_name_cnt >= 5:
                continue
            else:
                self.player_list.append(player_name.replace(',', '').strip())

        # Use the default list of players if none were given
        if self.player_list == ['']:
            self.player_list = ['Debonairesnake6',
                                'In Vänity',
                                'Wosko',
                                'Smol Squish',
                                'Ori Bot']

        # Notify the user tables are being created
        player_message = '\n\t-\t'.join(self.player_list)
        await self.message.channel.send(f'Attempting to create tables for:\n'
                                        f'\t-\t{player_message}')

    def get_api_information_for_each_player(self):
        """
        Run the API queries for each player
        """
        self.api_info = api_queries.APIQueries(self.player_list)

    async def process_discord_message(self):
        """
        Process the given discord message and run the appropriate functions
        """
        await self.parse_discord_message()
        self.get_api_information_for_each_player()
        await self.get_all_tables()

    def start_bot(self):
        """
        Start the bot
        """
        @self.bot.event
        async def on_message(message):
            """
            Receive and parse any message

            :param message: Context of the message
            """
            if message.content == '!clash help':
                await message.channel.send(''
                                           'Clash Bot commands:\n\n'
                                           ''
                                           '!clash\n'
                                           '\t-\tBasic command to pull all of the tables from the default list.\n'
                                           '\t-\tDebonairesnake6, In Vänity, Wosko, Smol Squish, Ori Bot.\n\n'
                                           ''
                                           '!clash [player1], [player2], [player3], [player4], [player5]\n'
                                           '\t-\tInsert each summoner name separated by a comma.\n'
                                           '\t-\tThis will pull every table for all of the given summoners in NA.\n'
                                           '\t-\tYou do not need to put all 5 summoner names.')
            elif message.content[:6] == '!clash':
                self.message = message
                await self.process_discord_message()

        # Run the bot
        if os.name == 'nt':
            print('Ready')
        self.bot.run(os.getenv('DISCORD_TOKEN'))


def main():
    """
    Holds the high level logic of the program
    """

    # Prefix to read_chat messages with
    bot = commands.Bot(command_prefix='!')

    # Start to read_chat messages on the server
    # read_messages(bot)
    clash_bot = ClashBot()
    clash_bot.start_bot()


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # TODO:
            #   -   Possible counters
            #   -   Account for player ranks
            #   -   Win rate of champions
            #   -   Add a !remove function to remove posts
            #   -   Swap row/column header in play rate table

            main()

            player_list = ['Debonairesnake6',
                           'In Vänity',
                           'Wosko',
                           'Smol Squish',
                           'Ori Bot']

            # player_list = ['ßøé',
            #                'Tempos',
            #                'Gobleeto',
            #                'Anita',
            #                'GyrosSteelBall']

            # player_list = ['Farcast']

            # rr_table = role_rate_table(player_list)
            # ms_table = mastery_shared_table(player_list)
            # rc_table = recent_champion_table()
            # cr_table = clash_ranked_table(player_list)
            #
            # ban_list = Calculate(ms_table.get_string()).get_ban_list()
            # ban_list = Calculate(rc_table.get_string(), ban_list).get_ban_list()
            # ban_list = Calculate(cr_table.get_string(), ban_list)
            # ban_list.create_table()

            # tmp = cr_table.get_string()
            # print(tmp)
            #
            # draw_tables.rr_table_picture(ms_table.get_string())
            #
            # print(rr_table.get_string())
            # print(ms_table.get_string())
            # print(rc_table.get_string())
            # print(cr_table.get_string())
            break

        # Catch if service is down
        except urllib.error.HTTPError as e:
            error_msg = "Service Temporarily Down"
            print(error_msg)
            print(e)
            time.sleep(60)

        # Catch random OS error
        except OSError as e:
            print(e, file=sys.stderr)
            time.sleep(60)
