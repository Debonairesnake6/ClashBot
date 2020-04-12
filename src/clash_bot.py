import os
import urllib
import time
import sys
import api_queries

from discord import File
from discord.ext import commands
from discord import ActivityType
from discord import Activity
from calculate_recommendations import CalculateBanRecommendations
from mastery_shared import MasteryShared
from role_rate import RoleRate
from recent_champion import RecentChampion
from player_ranks import PlayerRanks
from player_locked_in_position import PlayerLockedInPosition
from champions_for_role import ChampionsForRole


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
        self.player_ranks = None
        self.champions_for_role = None

    async def get_role_rate_table(self):
        """
        Parse the player list to generate the role rate table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Lane Play Rate Legend:' \
                      f'\n\t- {self.severity[0]}:\t>50% play rate' \
                      f'\n\t- {self.severity[1]}:\t>25% play rate'
        self.roll_rate = RoleRate(self.api_info, self.player_ranks.colour_columns[0])
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
        self.mastery_shared = MasteryShared(self.api_info, self.player_ranks.colour_columns[0])
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
        self.recent_champion = RecentChampion(self.api_info, 'all_match_history', self.player_ranks.colour_columns[0])
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
        self.clash_ranked = RecentChampion(self.api_info, 'ranked_match_history', self.player_ranks.colour_columns[0])
        await self.post_to_discord()

    async def get_player_ranks_table(self):
        """
        Parse the player list to get the player ranks table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Player Ranks Table:'
        self.player_ranks = PlayerRanks(self.api_info)
        await self.post_to_discord()

    async def get_player_locked_in_position(self):
        """
        Parse the player list to get the lock in position table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Player Position Table:' \
                      f'\n\t- These are the positions each player has locked in with.' \
                      f'\n\t- If multiple players chose the same role it will try to calculate their ' \
                      f'actual role and order them accordingly.'
        PlayerLockedInPosition(self.api_info)
        await self.post_to_discord()

    async def get_champions_for_locked_in_role(self):
        """
        Get the table to display played champions in the locked in role
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Recent Champions For Locked In Role:' \
                      f'\n\t- {self.severity[0]}:\t+25% total games and shared champ' \
                      f'\n\t- {self.severity[1]}:\t+25% total games' \
                      f'\n\t- {self.severity[2]}:\t+16% total games and shared champ' \
                      f'\n\t- {self.severity[3]}:\t+16% total games' \
                      f'\n\t- {self.severity[4]}:\tShared champ'
        self.champions_for_role = ChampionsForRole(self.api_info, self.player_ranks.colour_columns[0])
        await self.post_to_discord()

    async def get_ban_recommendation_table(self, know_position: bool = False):
        """
        Parse the player list to generate the ban recommendation table

        :param know_position: If the positions of the players are known use the champions_for_role table
        """
        self.legend = f'--------------------------------------------------------------------\n' \
                      f'Ban List Legend:' \
                      f'\n\t- {self.severity[0]}:\t+9% of top 15 score' \
                      f'\n\t- {self.severity[1]}:\t+7% of top 15 score' \
                      f'\n\t- {self.severity[2]}:\t+5% of top 15 score'
        combined_tables = [[self.mastery_shared.columns, self.mastery_shared.colour_columns],
                           [self.recent_champion.columns, self.recent_champion.colour_columns],
                           [self.clash_ranked.columns, self.clash_ranked.colour_columns]]
        if know_position:
            combined_tables.append([self.champions_for_role.columns, self.champions_for_role.colour_columns])
            CalculateBanRecommendations(combined_tables, locked_in_role=True)
        else:
            CalculateBanRecommendations(combined_tables, locked_in_role=False)
        await self.post_to_discord()

    async def post_to_discord(self):
        """
        Post the gathered information to discord
        """
        message_sent = False
        for _, _, filenames in os.walk('../extra_files'):
            for file in filenames:
                if file[-4:] == '.png':
                    await self.message.channel.send(self.legend, file=File(f'../extra_files/{file}', filename=file))
                    os.remove(f'../extra_files/{file}')
                    message_sent = True

        if not message_sent:
            await self.message.channel.send(self.legend)

    async def post_error_messages(self):
        """
        Post any error messages generated while using the api queries
        """
        await self.post_player_not_found()
        await self.post_no_match_history()
        await self.post_no_ranked_info()
        await self.post_no_ranked_clash()
        await self.post_no_clash_team()

    async def post_player_not_found(self):
        """
        Post if a given player was not found
        """
        failure_message = 'The given player(s) were not found:\n'
        for player_name in self.api_info.errors['player_not_found']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) were not found:\n':
            await self.message.channel.send(failure_message)

    async def post_no_ranked_info(self):
        """
        Post if a given player has no rank
        """
        failure_message = 'The given player(s) are not placed in any rank queue:\n'
        for player_name in self.api_info.errors['no_ranked_info']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) are not placed in any rank queue:\n':
            await self.message.channel.send(failure_message)

    async def post_no_ranked_clash(self):
        """
        Post if a given player has never played ranked or clash
        """
        failure_message = 'The given player(s) have never played ranked or clash:\n'
        for player_name in self.api_info.errors['no_ranked_clash']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) have never played ranked or clash:\n':
            await self.message.channel.send(failure_message)

    async def post_no_match_history(self):
        """
        Post if a given player was not found
        """
        failure_message = 'The given player(s) have no match history:\n'
        for player_name in self.api_info.errors['no_match_history']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) have no match history:\n':
            await self.message.channel.send(failure_message)

    async def post_no_clash_team(self):
        """
        Post if a given player was not in a clash team
        """
        failure_message = 'The given player(s) are not in a clash team:\n'
        for player_name in self.api_info.errors['no_clash_team']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) are not in a clash team:\n':
            await self.message.channel.send(failure_message)

    async def get_all_tables(self, display_positions: bool = False):
        """
        Get all of the different types of tables for each player given

        :param display_positions: Display the locked in positions table if using the clash API
        """
        if len(self.api_info.errors['no_clash_team']) == 0:
            await self.get_player_ranks_table()
            if display_positions:
                await self.get_player_locked_in_position()
            await self.get_role_rate_table()
            await self.get_mastery_shared_table()
            await self.get_recent_champion_table()
            await self.get_clash_ranked_table()
            if display_positions:
                await self.get_champions_for_locked_in_role()
                await self.get_ban_recommendation_table(know_position=True)
            else:
                await self.get_ban_recommendation_table()
        await self.post_error_messages()

    async def parse_discord_message(self):
        """
        Parse the discord message to grab each summoner name given
        """
        self.player_list = []
        # Get the first 5 player names given
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

    def get_api_information_for_each_player(self, clash_api: bool = False):
        """
        Run the API queries for each player

        :param clash_api: If using a single player to leverage the clash API
        """
        self.api_info = api_queries.APIQueries(self.player_list, clash_api)

    async def process_discord_message(self):
        """
        Process the given discord message and run the appropriate functions
        """
        await self.parse_discord_message()
        self.get_api_information_for_each_player()
        await self.get_all_tables()

    async def parse_discord_message_single_player(self):
        """
        Parse the discord message to extract the single player name given
        """
        self.player_list = [' '.join(self.message.content.strip().split()[1:])]
        await self.message.channel.send(f'Attempting to create tables for {self.player_list[0]}\'s clash team.')

    async def process_discord_message_single_player(self):
        """
        Process the given discord message for the single player given
        """
        await self.parse_discord_message_single_player()
        self.get_api_information_for_each_player(clash_api=True)
        await self.get_all_tables(display_positions=True)

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
            try:
                if message.content == '!clash help':
                    await message.channel.send('Clash Bot commands:\n'
                                               '```'
                                               '!clash\n'
                                               '-\tBasic command to pull all of the tables from the default list of:\n'
                                               '-\tDebonairesnake6, In Vänity, Wosko, Smol Squish, Ori Bot.\n\n'
                                               ''
                                               '!clash_team [player1]\n'
                                               '-\tInsert a single player name on the enemy team.\n'
                                               '-\tThis will grab all of the players on their clash team.\n'
                                               '-\tIt will also order the summoners by their role (Top --> Support).\n'
                                               '-\tIf players are locked in as fill it will attempt to display their '
                                               'correct position.\n\n'
                                               ''
                                               '!clash [player1], [player2], [player3], [player4], [player5]\n'
                                               '-\tInsert each summoner name separated by a comma.\n'
                                               '-\tThis will pull every table for all of the given summoners in NA.\n'
                                               '-\tYou can use up to 5 summoner names.\n\n'
                                               '```')
                elif message.content[:7] == '!clash ':
                    self.message = message
                    await self.process_discord_message()
                elif message.content[:11] == '!clash_team':
                    self.message = message
                    await self.process_discord_message_single_player()
                elif message.content[:6] == '!clash':
                    await message.channel.send('Unknown command. Use "!clash help" for the available options.')
            except Exception as exception:
                await message.channel.send(f'Failed with error: {exception}')

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')
            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='!clash help'))

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


def main():
    """
    Holds the high level logic of the program
    """

    # Start to read_chat messages on the server
    clash_bot = ClashBot()
    clash_bot.start_bot()


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # TODO:
            #   -   Possible counters
            #   -   Win rate of champions
            #   -   Add a !remove function to remove posts

            main()

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
