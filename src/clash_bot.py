"""
This file handles all of the interactions with discord and controls creating each table to display
"""
import asyncio
import os
import urllib
import time
import sys

import discord
import discord.gateway

import api_queries
import json
import shelve
import datetime

from discord.ext import commands
from discord import ActivityType, Activity, Embed, app_commands, File
# from discord_slash import SlashCommand
# from discord_slash.utils.manage_commands import create_option
from calculate_recommendations import CalculateBanRecommendations
from mastery_shared import MasteryShared
from role_rate import RoleRate
from recent_champion import RecentChampion
from player_ranks import PlayerRanks
from player_locked_in_position import PlayerLockedInPosition
from champions_for_role import ChampionsForRole
from threading import Lock


class TableHandler:
    """
    Class to handle the creation and management of all of the tables
    """

    def __init__(self, discord_bot: object):
        """
        :param discord_bot: Discord bot to handle all of the interactions with discord
        """
        self.discord_bot = discord_bot
        self.severity = ['Red', 'Orange', 'Yellow', 'Blue', 'Green']
        self.roll_rate = None
        self.mastery_shared = None
        self.recent_champion = None
        self.clash_ranked = None
        self.player_ranks = None
        self.champions_for_role = None
        self.api_info = None
        self.player_list = []

        self.debug = False

    async def get_role_rate_table(self):
        """
        Parse the player list to generate the role rate table
        """
        fields = {
            self.severity[0]: '>50% play rate',
            self.severity[1]: '>25% play rate'
        }
        self.roll_rate = RoleRate(self.api_info, self.player_ranks.colour_columns[0])
        await self.discord_bot.post_to_discord(title='Lane Play Rate', filename='roll_rate.png', fields=fields)

    async def get_mastery_shared_table(self):
        """
        Parse the player list to generate the mastery shared table
        """
        fields = {
            self.severity[0]: 'High mastery points and shared champ',
            self.severity[1]: 'High mastery points',
            self.severity[2]: 'Shared champ'
        }
        self.mastery_shared = MasteryShared(self.api_info, self.player_ranks.colour_columns[0])
        await self.discord_bot.post_to_discord(title='Mastery/Shared Champions', filename='mastery_shared.png', fields=fields)

    async def get_recent_champion_table(self):
        """
        Parse the player list to generate the recent champion table
        """
        fields = {
            self.severity[0]: '+25 games and shared champ',
            self.severity[1]: '+25 games',
            self.severity[2]: '+10 games and shared champ',
            self.severity[3]: '+10 games',
            self.severity[4]: 'Shared champ',
            'NOTE': 'Does not include ARAM or Poro King games'
        }
        self.recent_champion = RecentChampion(self.api_info, 'all_match_history', self.player_ranks.colour_columns[0])
        await self.discord_bot.post_to_discord(title='Recently Played Champions', filename='all_match_history.png', fields=fields)

    async def get_clash_ranked_table(self):
        """
        Parse the player list to generate the clash ranked table
        """
        fields = {
            self.severity[0]: '+25 games and shared champ',
            self.severity[1]: '+25 games',
            self.severity[2]: '+10 games and shared champ',
            self.severity[3]: '+10 games',
            self.severity[4]: 'Shared champ'
        }
        self.clash_ranked = RecentChampion(self.api_info, 'ranked_match_history', self.player_ranks.colour_columns[0])
        await self.discord_bot.post_to_discord(title='Clash/Ranked Champions', filename='ranked_match_history.png', fields=fields)

    async def get_player_ranks_table(self):
        """
        Parse the player list to get the player ranks table
        """
        self.player_ranks = PlayerRanks(self.api_info)
        await self.discord_bot.post_to_discord(title='Player Ranks', filename='player_ranks.png', fields={})

    async def get_player_locked_in_position(self):
        """
        Parse the player list to get the lock in position table
        """
        PlayerLockedInPosition(self.api_info)
        await self.discord_bot.post_to_discord(title='Player Positions', filename='player_positions.png', fields={})

    async def get_champions_for_locked_in_role(self):
        """
        Get the table to display played champions in the locked in role
        """
        fields = {
            self.severity[0]: '+25% total games and shared champ',
            self.severity[1]: '+25% total games',
            self.severity[2]: '+16% total games and shared champ',
            self.severity[3]: '+16% total games',
            self.severity[4]: 'Shared champ',
        }
        self.champions_for_role = ChampionsForRole(self.api_info, self.player_ranks.colour_columns[0])
        await self.discord_bot.post_to_discord(title='Champions Per Role', filename='champions_for_role.png', fields=fields)

    async def get_ban_recommendation_table(self, know_position: bool = False):
        """
        Parse the player list to generate the ban recommendation table

        :param know_position: If the positions of the players are known use the champions_for_role table
        """
        fields = {
            self.severity[0]: '+9% of top 15 score',
            self.severity[1]: '+7% of top 15 score',
            self.severity[2]: '+5% of top 15 score'
        }
        combined_tables = [[self.mastery_shared.columns, self.mastery_shared.colour_columns],
                           [self.recent_champion.columns, self.recent_champion.colour_columns],
                           [self.clash_ranked.columns, self.clash_ranked.colour_columns]]
        if know_position:
            combined_tables.append([self.champions_for_role.columns, self.champions_for_role.colour_columns])
            CalculateBanRecommendations(combined_tables, locked_in_role=True)
        else:
            CalculateBanRecommendations(combined_tables, locked_in_role=False)
        await self.discord_bot.post_to_discord(title='Ban List', filename='ban_recommendations.png', fields=fields)

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
            self.discord_bot.message_list.append(await self.discord_bot.message.channel.send(failure_message))

    async def post_no_ranked_info(self):
        """
        Post if a given player has no rank
        """
        failure_message = 'The given player(s) are not placed in any rank queue:\n'
        for player_name in self.api_info.errors['no_ranked_info']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) are not placed in any rank queue:\n':
            self.discord_bot.message_list.append(await self.discord_bot.message.channel.send(failure_message))

    async def post_no_ranked_clash(self):
        """
        Post if a given player has never played ranked or clash
        """
        failure_message = 'The given player(s) have never played ranked or clash:\n'
        for player_name in self.api_info.errors['no_ranked_clash']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) have never played ranked or clash:\n':
            self.discord_bot.message_list.append(await self.discord_bot.message.channel.send(failure_message))

    async def post_no_match_history(self):
        """
        Post if a given player was not found
        """
        failure_message = 'The given player(s) have no match history:\n'
        for player_name in self.api_info.errors['no_match_history']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) have no match history:\n':
            self.discord_bot.message_list.append(await self.discord_bot.message.channel.send(failure_message))

    async def post_no_clash_team(self):
        """
        Post if a given player was not in a clash team
        """
        failure_message = 'The given player(s) are not in a clash team:\n'
        for player_name in self.api_info.errors['no_clash_team']:
            failure_message += f'\t-\t{player_name}\n'
        if failure_message != 'The given player(s) are not in a clash team:\n':
            self.discord_bot.message_list.append(await self.discord_bot.message.channel.send(failure_message))

    async def get_api_information_for_each_player(self, clash_api: bool = False):
        """
        Run the API queries for each player

        :param clash_api: If using a single player to leverage the clash API
        """
        if not self.debug:
            api_info = api_queries.APIQueries(self.player_list, clash_api)
            self.api_info = api_info
        else:
            try:
                with shelve.open('/home/ubuntu/ClashBot/extra_files/my_api') as shelf:
                    self.api_info = dict(shelf)['0']
            except Exception:
                import dbm
                print()

        # # Save the results to a local shelf in case they need to be used later
        # file_path = '../extra_files/save_number.txt'
        # shelf_path = '../extra_files/my_api'
        # if os.path.isfile(file_path):
        #     with open(file_path, 'r') as my_number:
        #         save_number = my_number.read().strip()
        # else:
        #     save_number = '0'
        #
        # with shelve.open(shelf_path) as shelf:
        #     shelf[save_number] = self.api_info

    async def get_names_from_discord_message(self):
        """
        Parse the discord message to grab each summoner name given
        """
        self.player_list = [param['value'] for param in self.discord_bot.message.data['options']]

        # Use the default list of players if none were given
        if self.player_list == ['test']:
            self.player_list = ['iKony',
                                'Eric1',
                                'Shorthop',
                                'spiderjo',
                                'Debonairesnake6']

        # Notify the user tables are being created
        player_message = '\n-\t'.join(self.player_list)
        self.discord_bot.message_list.append(
            await self.discord_bot.message.channel.send(f'Attempting to create tables for:\n\t-\t{player_message}'))

    async def parse_discord_message_single_player(self):
        """
        Parse the discord message to extract the single player name given
        """
        self.player_list = [self.discord_bot.message.data['options'][0]['value']]  # todo get the acutal clash team with the new api call
        self.discord_bot.message_list.append(
            await self.discord_bot.message.channel.send(f'Attempting to create tables for {self.player_list[0]}\'s clash team.'))


class DiscordBot:
    """
    Discord bot handler
    """
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents)
        self.bot.setup_hook = self.setup_hook
        self.bot.tree.clear_commands(guild=None)
        self.table_handler = TableHandler(self)
        self.message = None
        self.reaction_payload = None
        self.message_history = {}
        self.message_list = []
        self.embed = Embed()
        self.image_url = 'https://clashbotimages2025.s3.us-east-2.amazonaws.com/'
        self.lock = Lock()

    async def setup_hook(self) -> None:
        print("Syncing commands...")
        await self.bot.tree.sync()

    async def post_to_discord(self, title: str, filename: str, fields: dict):
        """
        Post the gathered information to discord

        :param title: The name of the table
        :param filename: Name of the file to upload
        :param fields: Each field to add to the embed for a description
        """
        with self.lock:
            timestamp = int(datetime.datetime.now().timestamp())
            self.embed.clear_fields()
            self.embed.set_image(url=f'{self.image_url}{filename}?{timestamp}')
            self.embed.title = title
            for key, value in fields.items():
                self.embed.add_field(name=key, value=value, inline=False)
            self.message_list.append(await self.message.channel.send(embed=self.embed))

    async def process_discord_message(self):
        """
        Process the given discord message and run the appropriate functions
        """
        self.message_list = []
        await self.table_handler.get_names_from_discord_message()
        await self.table_handler.get_api_information_for_each_player()
        await self.table_handler.get_all_tables()

    async def process_discord_message_single_player(self):
        """
        Process the given discord message for the single player given
        """
        self.message_list = []
        await self.table_handler.parse_discord_message_single_player()
        await self.table_handler.get_api_information_for_each_player(clash_api=True)
        await self.table_handler.get_all_tables(display_positions=True)

    async def process_reaction_event(self):
        """
        Delete the message to call the bot and all of the bot's response messages
        """
        if self.reaction_payload.emoji.name == '❌':
            if str(self.reaction_payload.message_id) in self.message_history:
                for message in self.message_history[str(self.reaction_payload.message_id)]:
                    channel = await self.bot.fetch_channel(message['channel_id'])
                    original_message = await channel.fetch_message(message['message_id'])
                    await original_message.delete()
                self.message_history.pop(str(self.reaction_payload.message_id))
        self.save_message_history()

    def save_message_history(self):
        """
        Save the message history
        """
        with open('../extra_files/message_history.json', 'w', encoding='utf-8') as message_history_file:
            json.dump(self.message_history, message_history_file, indent=4)

    def load_message_history(self):
        """
        Load the message history for the bot
        """

        # If the message_history.json file does not exist, create it
        if not os.path.isfile('../extra_files/message_history.json'):
            with open('../extra_files/message_history.json', 'w', encoding='utf-8') as message_history_file:
                message_history_file.write('{\n}')

        # If the file does exist, read it and save it's values
        else:
            try:
                with open('../extra_files/message_history.json', 'r', encoding='utf-8') as message_history_file:
                    self.message_history = json.load(message_history_file)

            # If the file is empty, create it an as empty dictionary
            except json.decoder.JSONDecodeError:
                with open('../extra_files/message_history.json', 'w', encoding='utf-8') as message_history_file:
                    message_history_file.write('{\n}')

    async def save_last_request(self):
        """
        Increase the save number to keep the last request so it may be used later for troubleshooting
        """
        file_path = '../extra_files/save_number.txt'
        if os.path.isfile(file_path):
            with open(file_path, 'r') as my_number:
                save_number = int(my_number.read().strip()) + 1

            with open(file_path, 'w') as my_number:
                my_number.write(str(save_number))
        else:
            save_number = '1'
            with open(file_path, 'w') as my_number:
                my_number.write(save_number)
        await self.message.channel.send(f'Saved last query as number: {save_number}')

    async def clear_saved_queries(self):
        """
        Clear the saved queries once the bugs have been fixed
        """
        file_path = '../extra_files/save_number.txt'
        if os.path.isfile(file_path):
            os.remove(file_path)
            await self.message.channel.send('Cleared all saved queries')

    def start_bot(self):
        """
        Start the bot
        """
        @self.bot.event
        async def on_message(message: object):
            """
            Receive and parse any message

            :param message: Context of the message
            """
            if not message.author.bot:
                try:
                    self.message = message
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
                        await self.process_discord_message()
                    elif message.content[:11] == '!clash_team':
                        await self.process_discord_message_single_player()
                    elif message.content[:11] == '!clash_save':
                        await self.save_last_request()
                    elif message.content[:12] == '!clash_clear':
                        await self.clear_saved_queries()
                    elif message.content[:6] == '!clash':
                        self.message_list.append(await message.channel.send('Unknown command. Use "!clash help" for the '
                                                                            'available options.'))

                    # Stop processing if not a clash command
                    else:
                        return

                except Exception as exception:
                    await message.channel.send(f'Failed with error: {exception}')

                # Add the messages to the message history dictionary
                else:
                    if len(self.message_list) > 0:
                        self.message_list.insert(0, message)
                        self.message_history[f'{self.message_list[-1].id}'] = [{'channel_id': message.channel.id,
                                                                                'message_id': message.id} for message
                                                                               in self.message_list]
                        await self.message_list[-1].add_reaction('❌')
                        self.save_message_history()

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')
            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='/clash'))
            self.load_message_history()

        @self.bot.event
        async def on_raw_reaction_add(reaction_payload: object):
            """
            Checks if a reaction is added to the message

            :param reaction_payload: Payload information about the reaction
            """
            if not reaction_payload.member.bot:
                self.reaction_payload = reaction_payload
                await self.process_reaction_event()

        @self.bot.tree.command(name='clash',
                           description='Gather information about a player\'s clash team',
                           guild=None)
        async def clash(message, player_name: str):
            await message.response.send_message(f"Starting to scout {player_name}'s team")
            self.message = message
            await self.process_discord_message_single_player()

        @self.bot.tree.command(name='scout',
                           description='Gather information about a player(s)',
                           guild=None)
        async def scout(message: discord.Interaction, player_name: str):
            await message.response.send_message(f"Starting to scout: {player_name}")
            self.message = message
            await self.process_discord_message()

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


def nop(*args, **kwargs):
    pass


def main():
    """
    Holds the high level logic of the program
    """

    # Start to read_chat messages on the server
    # discord.gateway._log.debug = nop
    discord.gateway._log.warning = nop
    clash_bot = DiscordBot()
    clash_bot.start_bot()


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # TODO:
            #   -   Change output to proper embeds
            #   -   Possible counters
            #   -   Win rate of champions
            #   -   Way to re-order players after knowing their roles

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
