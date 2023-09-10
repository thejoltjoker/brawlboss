import json
import logging
import os
import urllib.parse
from pprint import pprint
import aiohttp
import requests
import aiohttp
import asyncio
from dotenv import load_dotenv
from requests import HTTPError

load_dotenv()


class BrawlApiEndpoint:
    base_url = 'https://api.brawlapi.com/v1'
    brawlers = f'{base_url}/brawlers'

    events = f'{base_url}/events'
    definitions = f'{base_url}/#/definitions'

    def brawler(self, brawler_id):
        brawler = f'{self.base_url}/brawlers/{brawler_id}'


class BrawlStarsEndpoint:
    base_url = 'https://api.brawlstars.com/v1'
    brawlers = f'{base_url}/brawlers'
    events = f'{base_url}/events/rotation'
    definitions = f'{base_url}/#/definitions'

    def players(self, tag):
        return f'{self.base_url}/players/{urllib.parse.quote_plus(tag)}'

    def players_battle_log(self, tag):
        return f'{self.base_url}/players/{urllib.parse.quote_plus(tag)}/battlelog'

    def clubs(self, tag):
        return f'{self.base_url}/clubs/{urllib.parse.quote_plus(tag)}'

    def clubs_members(self, tag):
        return f'{self.base_url}/clubs/{urllib.parse.quote_plus(tag)}/members'


class BrawlStarsApiAsync:
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {os.getenv("BRAWLSTARS_API_TOKEN")}'
        }

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *err):
        await self._session.close()
        self._session = None

    async def _get(self, url, *args, **kwargs):
        async with self._session.get(url, headers=self.headers, *args, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.warning(f'{response.status}: {response.reason}')
                return {}

    async def get_events(self):
        endpoint = BrawlStarsEndpoint.events
        return await self._get(endpoint)

    async def get_players(self, tag):
        endpoint = BrawlStarsEndpoint().players(tag)
        return await self._get(endpoint)

    async def get_players_battle_log(self, tag):
        endpoint = BrawlStarsEndpoint().players_battle_log(tag)
        return await self._get(endpoint)

    async def get_club(self, tag):
        endpoint = BrawlStarsEndpoint().clubs(tag)
        return await self._get(endpoint)


async def main():
    club_tag = os.getenv('BRAWLSTARS_CLUB_TAG')
    async with BrawlStarsApiAsync() as api:
        print(await api.get_club(club_tag))
        print(await api.get_events())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
