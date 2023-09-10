#!/usr/bin/env python3
"""helper.py
Description of helper.py.
"""
import hashlib
import logging
import random
import re
import string
from datetime import datetime, timedelta
from pprint import pprint

import requests


def proton_sweden_ips():
    ips = []
    with requests.get('https://api.protonmail.ch/vpn/logicals') as response:
        json_data = response.json()
        for server in json_data['LogicalServers']:
            if server['ExitCountry'] == 'SE':
                for s in server['Servers']:
                    ip = s['ExitIP']
                    print(f'Adding server {server["Name"]} ({ip}) to list')
                    ips.append(ip)
    return ips


def public_ip():
    ip = None
    response = requests.get('https://checkip.amazonaws.com')
    if response:
        ip = response.text.strip()

    return ip


def format_seconds(seconds):
    # Calculate hours, minutes, and remaining seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Create a formatted string
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time


def get_since_date(weeks=0, days=0, hours=0, minutes=0, seconds=0):
    since_date = datetime.utcnow() - timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours,
                                               weeks=weeks)
    return since_date


def battle_log_id(battle_log):
    to_hash = f'{battle_log["battleTime"]}'
    for team in battle_log['battle']['teams']:
        for p in team:
            to_hash = f'{to_hash}{p["tag"]}'

    return hashlib.md5(to_hash.encode('utf-8')).hexdigest()


def camel_case_to_snake_case(input_string):
    output_string = re.sub(r'(?<!^)(?=[A-Z])', '_', input_string).lower()
    return output_string


def camel_case_to_title_case(input_string):
    output_string = re.sub(r'(?<!^)(?=[A-Z])', ' ', input_string).title()
    return output_string


def player_to_profile_message(player, **kwargs):
    message = f"**{player.get('name')}** ({player.get('tag')})"

    # Add trophies
    trophies = player.get('trophies')
    highest_trophies = player.get('highestTrophies')
    if trophies == highest_trophies:
        message = f"{message}\n" \
                  f"🏆 **Trophies:** {trophies}\n"
    else:
        message = f"{message}\n" \
                  f"🏆 **Trophies:** {trophies} ({highest_trophies})\n"
    # Experience
    message = f"{message}\n" \
              f"⬆️ **Exp Level:** {player.get('expLevel')} ({player.get('expPoints')} points)\n"

    # Club
    club = player.get('club')
    if club:
        club_name = club.get('name')
        club_tag = club.get('tag')

        message = f"{message}\n" \
                  f"⚔️ **Club:** {club_name} ({club_tag})\n"

        rank_msg = '🌺 **Club rank:** #12'

    # Challenges
    # message = f"{message}\n" \
    # f"**Challenges**\n" \
    # f"🤖 **Best Robo Rumble Time:** {player.get('bestRoboRumbleTime')}\n" \
    # f"🐘 **Best Time As Big Brawler:** {player.get('bestTimeAsBigBrawler')}\n"

    # Stats
    message = f"{message}\n" \
              f"**Stats**\n" \
              f"*All time*\n" \
              f"🤺 **Solo Victories:** {player.get('soloVictories')}\n" \
              f"👯 **Duo Victories:** {player.get('duoVictories')}\n" \
              f"👪 **3Vs3 Victories:** {player.get('3vs3Victories')}\n"

    # Win rate
    victories = kwargs.get('victories')
    defeats = kwargs.get('defeats')
    if victories and defeats:
        total = victories + defeats
        message = f"{message}\n" \
                  f"🏁 **Win rate:** {round((victories / total) * 100)}%\n"

        # Win rate
        star_player = kwargs.get('starPlayer')
        if star_player:
            message = f"{message}" \
                      f"⭐ **Star player rate:** {round((star_player / total) * 100)}%\n"

    extra = f"*Last 7 days / last 30 days*" \
            f"🏅 **Victories:** 15 / 52" \
            f"💩 **Defeats:** 32 / 42"
    return message


def rankings_message(rankings):
    """Return a formatted list of club rankings"""
    message = 'Club rankings for the past seven days:'
    for i, player in enumerate(rankings, 1):
        if i == 1:
            i = '🥇'
        elif i == 2:
            i = '🥈'
        elif i == 3:
            i = '🥉'
        elif i == 4:
            i = f'\n{i}.'
        else:
            i = f'{i}.'

        name_part = f'{i} **{player["name"]}** `{player["tag"]}`'
        score_part = f'Score: **{round(player["score"], 2)}**'
        message = f'{message}\n' \
                  f'{name_part} | {score_part}'
    return message


def random_slap(sender, receiver):
    responses = ["{sender} slaps {receiver} with a large trout", "{sender} slaps {receiver} with a wet noodle",
                 "{sender} slaps {receiver} with a rotten tomato", "{sender} slaps {receiver} with a rubber chicken",
                 "{sender} slaps {receiver} with a brick", "{sender} slaps {receiver} with a baseball bat",
                 "{sender} slaps {receiver} with a frying pan", "{sender} slaps {receiver} with a foam finger",
                 "{sender} slaps {receiver} with a pillow", "{sender} slaps {receiver} with a slice of pizza",
                 "{sender} slaps {receiver} with a keyboard", "{sender} slaps {receiver} with a bouquet of flowers",
                 "{sender} slaps {receiver} with a cream pie", "{sender} slaps {receiver} with a bag of popcorn",
                 "{sender} slaps {receiver} with a fish", "{sender} slaps {receiver} with a snowball",
                 "{sender} slaps {receiver} with a hockey stick", "{sender} slaps {receiver} with a banana",
                 "{sender} slaps {receiver} with a bucket of water", "{sender} slaps {receiver} with a book",
                 "{sender} slaps {receiver} with a feather duster", "{sender} slaps {receiver} with a paper airplane",
                 "{sender} slaps {receiver} with a rubber duck", "{sender} slaps {receiver} with a can of soda",
                 "{sender} slaps {receiver} with a cactus", "{sender} slaps {receiver} with a rolled-up newspaper",
                 "{sender} slaps {receiver} with a bunch of grapes", "{sender} slaps {receiver} with a giant lollipop",
                 "{sender} slaps {receiver} with a toy lightsaber", "{sender} slaps {receiver} with a baguette",
                 "{sender} slaps {receiver} with a toy hammer", "{sender} slaps {receiver} with a giant gummy worm",
                 "{sender} slaps {receiver} with a toy snake", "{sender} slaps {receiver} with a giant marshmallow",
                 "{sender} slaps {receiver} with a rolled-up yoga mat", "{sender} slaps {receiver} with a foam dart",
                 "{sender} slaps {receiver} with a rubber chicken", "{sender} slaps {receiver} with a brick",
                 "{sender} slaps {receiver} with a bag of flour", "{sender} slaps {receiver} with a bucket of ice",
                 "{sender} slaps {receiver} with a baseball bat", "{sender} slaps {receiver} with a rotten apple",
                 "{sender} slaps {receiver} with a wet sponge", "{sender} slaps {receiver} with a bag of marbles",
                 "{sender} slaps {receiver} with a balloon filled with water",
                 "{sender} slaps {receiver} with a frying pan", "{sender} slaps {receiver} with a giant teddy bear",
                 "{sender} slaps {receiver} with a whipped cream can",
                 "{sender} slaps {receiver} with a bag of feathers",
                 "{sender} slaps {receiver} with a rolled-up poster", "{sender} slaps {receiver} with a bookshelf",
                 "{sender} slaps {receiver} with a bucket of confetti",
                 "{sender} slaps {receiver} with a bunch of roses", "{sender} slaps {receiver} with a giant candy cane",
                 "{sender} slaps {receiver} with a bucket of slime",
                 "{sender} slaps {receiver} with a pillow filled with rocks",
                 "{sender} slaps {receiver} with a foam finger", "{sender} slaps {receiver} with a bag of chips",
                 "{sender} slaps {receiver} with a giant inflatable hammer",
                 "{sender} slaps {receiver} with a snowball", "{sender} slaps {receiver} with a toy sword"]

    message = random.choice(responses)
    message = message.format(sender=sender, receiver=receiver)
    return message


def random_engage(sender, receiver):
    responses = ["{sender} tickles {receiver} with a live octopus tentacle",
                 "{sender} kisses {receiver} on the nose with a rubber chicken",
                 "{sender} feeds {receiver} a slice of pizza through a megaphone",
                 "{sender} serenades {receiver} with a kazoo solo",
                 "{sender} paints {receiver}'s face with rainbow-colored mustard",
                 "{sender} hypnotizes {receiver} with a toy yo-yo",
                 "{sender} juggles {receiver}'s shoes while reciting the alphabet backwards",
                 "{sender} tickles {receiver}'s ears with a feather duster",
                 "{sender} balances a cupcake on {receiver}'s nose with chopsticks",
                 "{sender} rides {receiver} like a horse while singing a lullaby",
                 "{sender} dances the tango with {receiver} using a broomstick",
                 "{sender} casts a spell on {receiver} with a glitter-filled wand",
                 "{sender} plays the harmonica while {receiver} belly dances",
                 "{sender} whispers secrets to {receiver} in gibberish",
                 "{sender} gives {receiver} a piggyback ride while wearing a tutu",
                 "{sender} recites Shakespeare while {receiver} juggles eggs",
                 "{sender} performs a magic trick that turns {receiver} into a balloon animal",
                 "{sender} makes {receiver} wear a lobster hat and sing karaoke",
                 "{sender} plays hopscotch with {receiver} on a pile of bubble wrap",
                 "{sender} makes {receiver} wear a chicken suit and cluck like a hen",
                 "{sender} gives {receiver} a bubble bath with green Jell-O",
                 "{sender} blindfolds {receiver} and feeds them pickles while reciting nursery rhymes",
                 "{sender} jumps out of a cake and surprises {receiver} with a ukulele",
                 "{sender} reads {receiver} a bedtime story in a Donald Duck voice",
                 "{sender} makes {receiver} wear a Viking helmet and do the Macarena",
                 "{sender} tickles {receiver} with a giant feather",
                 "{sender} gives {receiver} a bear hug while wearing a Pikachu costume",
                 "{sender} tickles {receiver} with a rubber chicken",
                 "{sender} feeds {receiver} spaghetti with their toes",
                 "{sender} serenades {receiver} with a kazoo solo",
                 "{sender} paints {receiver}'s face with rainbow-colored mustard",
                 "{sender} hypnotizes {receiver} with a toy yo-yo",
                 "{sender} juggles {receiver}'s shoes while reciting the alphabet backwards",
                 "{sender} tickles {receiver}'s ears with a feather duster",
                 "{sender} balances a cupcake on {receiver}'s nose with chopsticks",
                 "{sender} rides {receiver} like a horse while singing a lullaby",
                 "{sender} plays a game of tag with {receiver} using a water gun",
                 "{sender} teaches {receiver} how to hula hoop",
                 "{sender} juggles fruit with {receiver} while reciting tongue twisters",
                 "{sender} wears a silly hat and dances the cha-cha with {receiver}",
                 "{sender} gives {receiver} a balloon animal tutorial",
                 "{sender} puts on a puppet show for {receiver}",
                 "{sender} draws caricatures of {receiver} and their friends",
                 "{sender} teaches {receiver} how to make origami animals",
                 "{sender} has a staring contest with {receiver} while balancing an apple on their head",
                 "{sender} gives {receiver} a guided tour of a haunted house",
                 "{sender} sings a song in a made-up language with {receiver} as backup singer",
                 "{sender} has a picnic with {receiver} and feeds them grapes with chopsticks",
                 "{sender} performs a comedy skit with {receiver} as the straight man",
                 "{sender} gives {receiver} a piggyback ride while reciting a tongue twister",
                 "{sender} teaches {receiver} how to juggle with fruit",
                 "{sender} has a drawing competition with {receiver} using their non-dominant hand",
                 "{sender} gives {receiver} a foot massage with a rubber chicken",
                 "{sender} puts on a magic show for {receiver}",
                 "{sender} teaches {receiver} how to solve a Rubik's cube",
                 "{sender} performs a dance routine with {receiver} using a broom as a prop",
                 "{sender} has a water balloon fight with {receiver} while wearing swim goggles",
                 "{sender} has a staring contest with {receiver} while balancing a book on their head",
                 "{sender} gives {receiver} a guided tour of a zoo and makes animal noises",
                 "{sender} puts on a fashion show with {receiver} using clothes made of recycled materials",
                 "{sender} teaches {receiver} how to play a song on a kazoo",
                 "{sender} performs a skit where {receiver} is the superhero and {sender} is the villain",
                 "{sender} has a tickle fight with {receiver} using a feather duster",
                 "{sender} gives {receiver} a tour of a museum and acts out the exhibits",
                 "{sender} puts on a puppet show for {receiver} using socks as puppets",
                 "{sender} teaches {receiver} how to make a balloon animal",
                 "{sender} performs a stand-up comedy routine with {receiver} as the audience",
                 "{sender} has a thumb wrestling competition with {receiver}",
                 "{sender} gives {receiver} a guided tour of a candy factory",
                 "{sender} teaches {receiver} how to make homemade ice cream",
                 "{sender} performs a rap with {receiver} as the DJ",
                 "{sender} has a staring contest with {receiver} while balancing a spoon on their nose",
                 "{sender} gives {receiver} a guided tour of a science museum and performs science experiments",
                 "{sender} puts on a play with {receiver} using puppets made of fruit",
                 "{sender} teaches {receiver} how to solve a crossword puzzle",
                 "{sender} performs a skit where {receiver} is a famous actor/actress and {sender} is their assistant",
                 "{sender} has a thumb war competition with {receiver} using chopsticks"]

    message = random.choice(responses)
    message = message.format(sender=sender, receiver=receiver)
    return message


def translate_player_keys(player_dict):
    """Convert player json keys to ones that match the Player object

    Args:
        player_dict:

    Returns:

    """
    data = {}
    for k, v in player_dict.items():
        if k == '3vs3Victories':
            k = 'three_vs_three_victories'
        data[camel_case_to_snake_case(k)] = v
    return data


def camel_case_dict_to_snake_case(data, change_builtins=False):
    """Converts a dictionary with camel case keys to snake case keys and returns the modified dictionary.

    Args:
        change_builtins: Add underscore to conflicting names
        data (dict): A dictionary with camel case keys.

    Returns:
        dict: A dictionary with snake case keys.

    """
    output = {}
    for key, value in data.items():
        if change_builtins:
            if key in [x for x in __builtins__]:
                key = f'{key}_'
        snake_key = camel_case_to_snake_case(key)
        if isinstance(value, dict):
            output[snake_key] = camel_case_dict_to_snake_case(value, change_builtins)
        elif isinstance(value, list):
            output[snake_key] = camel_case_list_to_snake_case(value)
        else:
            output[snake_key] = value
    return output


def battle_time_to_timestamp(battle_time: str) -> float:
    """
    Convert a battle time string in the format 'YYYYMMDDTHHMMSS.ffffffZ' to a Unix timestamp.

    Parameters:
        battle_time (str): A string representing the time of a battle in the format 'YYYYMMDDTHHMMSS.ffffffZ'.

    Returns:
        float: The Unix timestamp corresponding to the given battle time.

    """
    date_format = '%Y%m%dT%H%M%S.%fZ'
    datetime_object = datetime.strptime(battle_time, date_format)
    timestamp = datetime_object.timestamp()

    return timestamp


def battle_time_to_datetime(battle_time: str) -> datetime:
    """
    Convert a battle time string in the format 'YYYYMMDDTHHMMSS.ffffffZ' to a datetime object.

    Parameters:
        battle_time (str): A string representing the time of a battle in the format 'YYYYMMDDTHHMMSS.ffffffZ'.

    Returns:
        datetime: The datetime object corresponding to the given battle time.

    """
    date_format = '%Y%m%dT%H%M%S.%fZ'
    datetime_object = datetime.strptime(battle_time, date_format)

    return datetime_object


def prepare_api_model(data):
    """Convert keys to snake case and change keys to not collide with builtins"""
    if data.get('3vs3Victories'):
        data['three_vs_three_victories'] = data['3vs3Victories']
        data.pop('3vs3Victories')

    icon = data.get('icon')
    if icon:
        if isinstance(icon, dict):
            data['icon'] = icon.get('id')

    return camel_case_dict_to_snake_case(data, change_builtins=True)


def camel_case_list_to_snake_case(data):
    """Converts a list with camel case keys to snake case keys and returns the modified list.

    Args:
        data (list): A list with camel case keys.

    Returns:
        list: A list with snake case keys.

    """
    output = []
    for value in data:
        if isinstance(value, dict):
            output.append(camel_case_dict_to_snake_case(value))
        else:
            output.append(value)
    return output


def strip_tag(tag):
    tag = tag.strip('#')
    tag = tag.strip('%23')
    return tag.strip()


def main():
    """docstring for main"""
    for ip in proton_sweden_ips():
        print(ip)
    # print(battle_time_to_datetime('20230506T093717.000Z') < datetime.now())
    # print(camel_case_to_snake_case('isQualifiedFromChampionshipChallenge'))


if __name__ == '__main__':
    main()
