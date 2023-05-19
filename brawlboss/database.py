#!/usr/bin/env python3
"""database.py
Description of database.py.
"""
import logging
import os
from datetime import datetime, timedelta
from pprint import pprint

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.server_api import ServerApi

import helper
from dotenv import load_dotenv

load_dotenv()


class BrawlBossDatabase:
    def __init__(self):
        self.client = None

        # Get server details
        host = os.getenv('MONGODB_HOST', '0.0.0.0')
        port = os.getenv('MONGODB_PORT', 27017)

        # Client
        database_name = 'brawlboss'
        uri = os.getenv('MONGODB_URI', f'mongodb://{host}:{port}/')
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]

    async def _upsert(self, collection: str, data: dict, _id=None, query=None):
        """
        Upserts a document into a MongoDB collection.

        Parameters:
            collection (str): The name of the collection to upsert the document into.
            data (dict): The data to upsert into the collection.
            _id (Optional[str]): The _id of the document.
            query (Optional[dict]): The query used to find the document.

        Returns:
            dict: The updated document from the collection.

        """
        # Get the collection object for the specified collection name.
        coll = self.db[collection]

        # If an _id is provided, add it to the data and create a query.
        if _id:
            data['_id'] = _id
            query = query or {'_id': data.get('_id')}

        # Use the update_one() method to upsert the data into the collection.
        is_new = False if await coll.find_one(query) else True
        result = await coll.update_one(query, {'$set': data}, upsert=True)
        # if result.modified_count >= 1:
        #     is_new = False

        # Find the document and return it.
        return await coll.find_one(query), is_new

    async def _delete_one(self, collection: str, query: dict):
        coll = self.db[collection]
        result = await coll.delete_one(query)

    async def test_connection(self):
        # Send a ping to confirm a successful connection
        try:
            await self.client.admin.command('ping')
            logging.info('Pinged your deployment. You successfully connected to MongoDB!')
        except Exception as e:
            logging.error(e)

    async def get_player_from_discord_name(self, discord_name):
        collection = self.db['discord']
        return collection.find_one({'discord': discord_name})

    async def upsert_player(self, data):
        """
        Upserts a Brawl Stars player into a MongoDB database.

        Parameters:
            data (dict): A dictionary containing the Brawl Stars player data.

        Returns:
            dict: The result of the upsert operation.
        """
        collection_name = 'player'
        return await self._upsert(collection_name, _id=data['tag'], data=data)

    async def upsert_battle(self, data):
        """
        Upserts a Brawl Stars battle into a MongoDB database.

        Parameters:
            data (dict): A dictionary containing the Brawl Stars battle data.

        Returns:
            dict: The result of the upsert operation.
        """
        battle_time = data['battleTime']
        timestamp = helper.battle_time_to_timestamp(battle_time)
        data['battleTime'] = helper.battle_time_to_datetime(battle_time)

        # Upsert
        collection_name = 'battle'
        return await self._upsert(collection_name, _id=timestamp, data=data)

    async def upsert_club(self, data):
        """
        Upserts a Brawl Stars club into a MongoDB database.

        Parameters:
            data (dict): A dictionary containing the Brawl Stars club data.

        Returns:
            dict: The result of the upsert operation.
        """
        collection_name = 'club'
        return await self._upsert(collection_name, _id=data['tag'], data=data)

    async def upsert_discord(self, data):
        """
        Upserts a discord member into a MongoDB database.

        Parameters:
            data (dict): A dictionary containing the discord member.

        Returns:
            dict: The result of the upsert operation.
        """
        return await self._upsert("discord", _id=data['_id'], data=data)

    async def player_from_discord_id(self, discord_id):
        player = None
        collection = self.db['discord']
        discord_doc = await collection.find_one({'_id': discord_id})
        if discord_doc:
            player = await self.db['player'].find_one({'_id': discord_doc['tag']})
        return player

    async def get_battles_since(self, tag, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        # Battles since a certain date
        collection = self.db.battle
        since_date = datetime.utcnow() - timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours,
                                                   weeks=weeks)
        query = {
            '$and': [
                {
                    'battle.teams': {
                        '$elemMatch': {
                            '$elemMatch': {
                                'tag': tag
                            }
                        }
                    }
                }, {
                    'battleTime':
                        {
                            '$gte': since_date
                        }
                }
            ]
        }
        battles = collection.find(query)
        return battles

    async def upsert_attribute_emoji(self, attribute, emoji):
        data = {'attribute': attribute,
                'emoji': emoji}
        self._upsert('emoji', data, query={'attribute': attribute})

    async def battle_count(self, tag, rank=2):
        """

        Args:
            tag:
            rank:

        Returns:
            tuple(victories, defeats, total)
        """
        # Get all victories of user
        collection = self.db.battle
        query = {
            '$and': [
                {
                    'battle.teams': {
                        '$elemMatch': {
                            '$elemMatch': {
                                'tag': tag
                            }
                        }
                    }
                }, {
                    '$or': [
                        {
                            'battle.result': 'victory'
                        }, {
                            'battle.rank': {'$lte': rank}
                        }
                    ]
                }
            ]
        }
        victory_count = await collection.count_documents(query)
        total_count = await collection.count_documents({
            'battle.teams': {
                '$elemMatch': {
                    '$elemMatch': {
                        'tag': tag
                    }
                }
            }
        })
        return victory_count, total_count - victory_count, total_count
