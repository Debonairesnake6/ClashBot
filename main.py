import os
import json
import requests
import globals
import urllib
import time
import draw_tables
import sys

from discord import File
from discord.ext import commands
from role_rate import role_rate_table
from mastery_shared import mastery_shared_table
from recent_champion import recent_champion_table
from clash_ranked_table import clash_ranked_table
from calculate_recommendations import Calculate

base_url = globals.base_url
client_token = os.getenv('DISCORD_TOKEN')
players_not_found = globals.players_not_found


# Post a message
def post_message(message):

    # Headers for the POST request
    headers = {"Authorization": "Bot {}".format(client_token),
               "User-Agent": "myBotThing (http://some.url, v0.1)",
               "Content-Type": "application/json", }

    json_message = json.dumps({"content": message})

    requests.post(base_url, headers=headers, data=json_message)


# Send the table to discord
async def send_discord(ctx, legend, table=False, image=False):

    if image is False:
        # Create an image of the table
        # noinspection PyUnresolvedReferences
        draw_tables.DrawTable(table.get_string()).get_image().save('table.png')
    else:
        # Create and image of the ban table
        # noinspection PyUnresolvedReferences
        image.save('table.png')

    # Print the legend to console and discord
    if legend is not None:
        print(legend)
        await ctx.send(legend, file=File('table.png', filename='table.png'))


# Read messages from users
def read_messages(bot):
    @bot.command(name='clash', help='Type: ```!clash [player1], [player2], [player3], [player4], [player5]```',
                 pass_context=True)
    async def read(ctx):

        global players_not_found

        # Hold the severity levels
        severity = ['Red', 'Orange', 'Yellow', 'Blue', 'Green']

        # Hold the player_list
        player_list = []

        # Check if any player names were given
        if ctx.view.buffer != '!clash':

            # Get the desired player names
            for player_name_cnt, player_name in enumerate(ctx.view.buffer.split()[1:]):

                # Skip if it already names 5 players
                if player_name_cnt >= 5:
                    continue

                # Add the player to the player_list
                player_list.append(player_name.replace(',', '').strip())

        # Default list if blank
        if len(player_list) == 0:
            player_list = ['Debonairesnake6',
                           'In Vänity',
                           'Wosko',
                           'Smol Squish',
                           'Ori Bot']

        # Role rate Table ----------------------------------------------------------------------------------------------

        # Get the role rate table
        rr_table = role_rate_table(player_list)

        legend = f'--------------------------------------------------------------------\n' \
                 f'Lane Play Rate Legend:' \
                 f'\n\t- {severity[0]}:\t>60% play rate' \
                 f'\n\t- {severity[1]}:\t>30% play rate'

        # Post on discord
        await send_discord(ctx, legend, rr_table)

        # Mastery shared Table -----------------------------------------------------------------------------------------

        # Get the mastery shared table
        ms_table = mastery_shared_table(player_list)

        # Create a legend to read_chat the table
        legend = f'--------------------------------------------------------------------\n' \
                 f'Mastery/Shared Pool Legend:' \
                 f'\n\t- {severity[0]}:\tHigh mastery points and shared champ' \
                 f'\n\t- {severity[1]}:\tHigh mastery points' \
                 f'\n\t- {severity[2]}:\tShared champ' \
                 '\nNOTE: Champions not played with the past 30 days have their highlighting removed'

        # Post on discord
        await send_discord(ctx, legend, ms_table)

        # Recent champion Table ----------------------------------------------------------------------------------------

        # Get the recent champion table
        rc_table = recent_champion_table()

        # Create a legend to read_chat the table
        legend = f'--------------------------------------------------------------------\n' \
                 f'Recent Champion Legend:' \
                 f'\n\t- {severity[0]}:\t+25 games and shared champ' \
                 f'\n\t- {severity[1]}:\t+25 games' \
                 f'\n\t- {severity[2]}:\t+10 games and shared champ' \
                 f'\n\t- {severity[3]}:\t+10 games' \
                 f'\n\t- {severity[4]}:\tShared champ' \
                 f'\nNOTE: This list does not include ARAM or Poro King games'

        # Post to discord
        await send_discord(ctx, legend, rc_table)

        # Clash Ranked Table -------------------------------------------------------------------------------------------

        # Get the clash ranked table
        cr_table = clash_ranked_table(player_list)

        # Create a legend to the table
        legend = f'--------------------------------------------------------------------\n' \
                 f'Clash and Ranked Legend:' \
                 f'\n\t- {severity[0]}:\t+25 games and shared champ' \
                 f'\n\t- {severity[1]}:\t+25 games' \
                 f'\n\t- {severity[2]}:\t+10 games and shared champ' \
                 f'\n\t- {severity[3]}:\t+10 games' \
                 f'\n\t- {severity[4]}:\tShared champ'

        # Post to discord
        await send_discord(ctx, legend, cr_table)

        # Post which players were missing
        if players_not_found != '':
            await ctx.send(f'Could not find player(s): {players_not_found[:-3]}')

        # Ban table ----------------------------------------------------------------------------------------------------

        # Get the ban table
        ban_list = Calculate(ms_table.get_string()).get_ban_list()
        ban_list = Calculate(rc_table.get_string(), ban_list).get_ban_list()
        ban_list = Calculate(cr_table.get_string(), ban_list)
        ban_image = ban_list.create_table()

        # Create a legend for the table
        legend = f'--------------------------------------------------------------------\n' \
                 f'Ban List Legend:' \
                 f'\n\t- {severity[0]}:\t+11% of top 10 score' \
                 f'\n\t- {severity[1]}:\t+10% of top 10 score' \
                 f'\n\t- {severity[2]}:\t+9% of top 10 score' \

        # Post to discord
        await send_discord(ctx, legend, image=ban_image)

    # Start the bot
    bot.run(client_token)


def main():

    # Prefix to read_chat messages with
    bot = commands.Bot(command_prefix='!')

    # Start to read_chat messages on the server
    read_messages(bot)


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # TODO:
            #   -   Possible counters
            #   -   Account for player ranks
            #   -   Win rate of champions
            #   -   Add a !remove function to remove posts

            main()

            # player_list = ['Debonairesnake6',
            #                'In Vänity',
            #                'Wosko',
            #                'Smol Squish',
            #                'Ori Bot']

            # player_list = ['ßøé',
            #                'Tempos',
            #                'Gobleeto',
            #                'Anita',
            #                'GyrosSteelBall']

            player_list = ['Farcast']

            rr_table = role_rate_table(player_list)
            ms_table = mastery_shared_table(player_list)
            rc_table = recent_champion_table()
            cr_table = clash_ranked_table(player_list)
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
            post_message(error_msg)
            time.sleep(60)

        # Catch random OS error
        except OSError as e:
            print(e, file=sys.stderr)
            time.sleep(60)
