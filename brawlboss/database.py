#!/usr/bin/env python3
"""database.py
Description of database.py.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from pprint import pprint

from motor.motor_asyncio import AsyncIOMotorClient

import helper
from dotenv import load_dotenv

load_dotenv()


class MongoQueries:
    player_of_the_week = ['']
    club_rankings = []
    battle_type_ranked = {
        '$or': [
            {
                'battle.type': 'teamRanked'
            }, {
                'battle.type': 'soloRanked'
            }
        ]
    }

    @staticmethod
    def club_battles(member_tags: list):
        """Get all battles involving a club member

        Args:
            member_tags: list of club member tags

        Returns:
            dict: query
        """
        query = {
            "battle.teams": {
                "$elemMatch": {
                    "members.tag": {
                        "$in": member_tags
                    }
                }
            }
        }
        return query

    @staticmethod
    def tag_in_battle_teams_or_players(tag):
        query = {
            '$or': [
                {
                    'battle.teams': {
                        '$elemMatch': {
                            '$elemMatch': {
                                'tag': tag
                            }
                        }
                    }
                }, {
                    'battle.players': {
                        '$elemMatch': {
                            'tag': tag
                        }
                    }
                }
            ]
        }
        return query

    @classmethod
    def star_player_battles(cls, tag):
        query = {
            '$and': [
                cls.tag_in_battle_teams_or_players(tag), {
                    'battle.starPlayer.tag': tag
                }
            ]
        }
        return query

    @classmethod
    def battle_count(cls, tag, since_date: datetime = None):
        query = {'$and': [
            cls.tag_in_battle_teams_or_players(tag),
            {
                'battleTime':
                    {
                        '$gte': since_date
                    }
            }
        ]}
        return query

    @classmethod
    def battle_count_victories(cls, tag, rank=2, since_date: datetime = None):
        query = {'$and': [
            cls.tag_in_battle_teams_or_players(tag),
            cls.battle_victory(rank),
            {
                'battleTime':
                    {
                        '$gte': since_date
                    }
            }
        ]}
        return query

    @classmethod
    def battle_victory(cls, rank=2):
        return {
            '$or': [
                {
                    'battle.result': 'victory'
                }, {
                    'battle.rank': {'$lte': rank}
                }
            ]
        }

    @classmethod
    def battles_today(cls, tag):
        dt = datetime.utcnow()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return cls.battle_count(tag, since_date=dt)

    @classmethod
    def club_league_battles(cls, tag):
        query = {
            '$and': [
                cls.tag_in_battle_teams_or_players(tag),
                cls.battle_type_ranked,
                {
                    'battle.trophyChange':
                        {
                            '$in': [3, 5, 7, 9]
                        }
                }
            ]
        }
        return query

    @classmethod
    def battle_time(cls, since_date: datetime):
        query = {
            'battleTime': {
                '$gte': since_date
            }
        }
        return query

    @classmethod
    def battle_duration_pipeline(cls, tag, since_date: datetime = None):
        pipeline = [
            {
                '$match': {
                    '$and': [cls.tag_in_battle_teams_or_players(tag),
                             cls.battle_time(since_date)
                             ]
                }
            }, {
                '$group': {
                    '_id': tag,
                    'total_duration': {
                        '$sum': '$battle.duration'
                    }
                }
            }
        ]
        return pipeline

    @classmethod
    def all_battle_duration_pipeline(cls, since_date: datetime = None):
        pipeline = [
            {
                '$match': {
                    'battleTime': {
                        '$gte': datetime(2023, 9, 9, 0, 0, 0, tzinfo=timezone.utc)
                    }
                }
            }, {
                '$unwind': {
                    'path': '$battle.teams'
                }
            }, {
                '$unwind': {
                    'path': '$battle.teams'
                }
            }, {
                '$group': {
                    '_id': '$battle.teams.tag',
                    'name': {
                        '$first': '$battle.teams.name'
                    },
                    'total_duration': {
                        '$sum': '$battle.duration'
                    }
                }
            }, {
                '$sort': {
                    'total_duration': -1
                }
            }
        ]
        return pipeline

    @classmethod
    def club_members_battle_duration(cls, since_date: datetime = None):
        pipeline = [
            {
                '$unwind': {
                    'path': '$battle.teams'
                }
            }, {
                '$unwind': {
                    'path': '$battle.teams'
                }
            }, {
                '$lookup': {
                    'from': 'club',
                    'localField': 'battle.teams.tag',
                    'foreignField': 'members.tag',
                    'as': 'club_members'
                }
            }, {
                '$match': {
                    'club_members.0': {
                        '$exists': True
                    }
                }
            }, {
                '$group': {
                    '_id': '$battle.teams.tag',
                    'name': {
                        '$first': '$battle.teams.name'
                    },
                    'total_duration': {
                        '$sum': '$battle.duration'
                    }
                }
            }, {
                '$sort': {
                    'total_duration': -1
                }
            }
        ]

        return pipeline


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

    async def _aggregate(self, collection: str, pipeline: list):
        """Aggregate documents"""
        coll = self.db[collection]
        return await coll.aggregate(pipeline).to_list(length=None)

    async def _delete_one(self, collection: str, query: dict):
        coll = self.db[collection]
        result = await coll.delete_one(query)

    async def test_connection(self):
        # Send a ping to confirm a successful connection
        try:
            await self.client.admin.command('ping')
            logging.info('Pinged your deployment. You successfully connected to MongoDB!')
            return True
        except Exception as e:
            logging.error(e)
            return False

    async def first_battle(self, tag=None):
        """

        Returns:
            motor.motor_asyncio.AsyncIOMotorCursor:
        """
        collection = self.db['battle']
        query = {}
        if tag:
            query = MongoQueries.tag_in_battle_teams_or_players(tag)
        battle = collection.find(query).sort('battleTime', 1).limit(1)
        return battle

    async def last_battle(self, tag=None):
        """

        Returns:
            motor.motor_asyncio.AsyncIOMotorCursor:
        """
        collection = self.db['battle']
        query = {}
        if tag:
            query = MongoQueries.tag_in_battle_teams_or_players(tag)
        battle = collection.find(query).sort('battleTime', -1).limit(1)
        return battle

    async def last_club_league_battle(self, tag):
        """

        Returns:
            motor.motor_asyncio.AsyncIOMotorCursor:
        """
        collection = self.db['battle']
        query = {}
        query = MongoQueries.club_league_battles(tag)
        battle = collection.find(query).sort('battleTime', -1).limit(1)
        return battle

    async def first_battle_date(self):
        """Returns a datetime object with the time for the first battle in database

        Returns:
            datetime: First battle
        """
        cursor = await self.first_battle()
        battle_time = None
        for document in await cursor.to_list(length=1):
            # Try and get the datetime from document
            battle_time = document.get('battleTime')

            # Create from id since the id is a timestamp of the battle
            if not isinstance(battle_time, datetime):
                battle_time = datetime.fromtimestamp(document.get('_id'))

        return battle_time

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
                {'$or': [{'battle.teams': {
                    '$elemMatch': {
                        '$elemMatch': {
                            'tag': tag
                        }
                    }
                }}, {'battle.players': {
                    '$elemMatch': {
                        'tag': tag
                    }
                }}]

                }, {
                    'battleTime':
                        {
                            '$gte': since_date
                        }
                }
            ]
        }
        battles = collection.find(query)
        for b in battles:
            print(b)
        return battles

    async def wins_last_seven_days(self, tag, rank=2):
        # Battles since a certain date
        collection = self.db.battle
        since_date = datetime.utcnow() - timedelta(days=7)
        query = [{'$match': {
            '$and': [
                {'$or': [{'battle.teams': {
                    '$elemMatch': {
                        '$elemMatch': {
                            'tag': tag
                        }
                    }
                }}, {'battle.players': {
                    '$elemMatch': {
                        'tag': tag
                    }
                }}]

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
        }},
            {'$group': {'': ''}},
            {'$sort': {'': ''}}]

        battles = collection.find(query)
        return battles

    async def battle_duration(self, tag, since_date: datetime = None):
        pipeline = MongoQueries.battle_duration_pipeline(tag, since_date or await self.first_battle_date())
        durations = await self._aggregate('battle', pipeline)
        return durations[0]

    async def player_of_the_week(self, club_tag):
        # Battles since a certain date
        since_date = datetime.utcnow() - timedelta(days=7)

        club = await self.get_club(club_tag)
        members = club['members']
        # For each player in club
        # Get win rate
        # Get star player count
        # Add to list
        # Sort list by star player count*win rate
        # Return top player
        return players

    async def get_club(self, club_tag):
        """

        Args:
            club_tag:

        Returns:
            dict: club data
        """
        collection = self.db['club']
        club = await collection.find_one({'_id': club_tag})
        return club

    async def get_club_battles(self, club_tag):
        collection = self.db['battle']
        club = await self.get_club(club_tag)
        club_members_tags = [member['tag'] for member in club['members']]
        cursor = collection.find(MongoQueries.club_battles(club_members_tags))
        for document in await cursor.to_list(length=100):
            pprint(document)

    async def club_rankings(self, club_tag):
        scores = []
        rankings = {}

        # Get members
        club = await self.get_club(club_tag)
        if club:
            # Get club score for each member
            for member in club.get('members', []):
                tag = member['tag']
                score = await self.club_score(tag)
                member['score'] = score
                scores.append(member)
        rankings = sorted(scores, key=lambda x: x['score'], reverse=True)

        # Return dictionary with tag: club_score
        return rankings

    async def upsert_attribute_emoji(self, attribute, emoji):
        data = {'attribute': attribute,
                'emoji': emoji}
        await self._upsert('emoji', data, query={'attribute': attribute})

    async def battle_count(self, tag, rank=2, since_date: datetime = None):
        """

        Args:
            since_date:
            tag:
            rank:

        Returns:
            tuple(victories, defeats, total)
        """
        if not since_date:
            since_date = await self.first_battle_date()

        collection = self.db.battle

        # Get all victories of user
        query = MongoQueries.battle_count_victories(tag, rank, since_date)
        victory_count = await collection.count_documents(query)

        # Get all battles
        query = MongoQueries.battle_count(tag, since_date)
        total_count = await collection.count_documents(query)
        return victory_count, total_count - victory_count, total_count

    async def star_player_count(self, tag):
        collection = self.db.battle
        query = MongoQueries.star_player_battles(tag)
        star_player_battle_count = await collection.count_documents(query)
        return star_player_battle_count

    async def win_rate(self, tag, since_date: datetime = None):
        victories, defeats, total = await self.battle_count(tag, since_date=since_date)
        if victories:
            return victories / total
        return 0

    async def club_score(self, tag):
        """Club score for the last seven days

        Args:
            tag:

        Returns:

        """
        # Get win rate, 0-1
        since_date = helper.get_since_date(weeks=1)
        win_rate = await self.win_rate(tag, since_date)

        # Get star player count, but at least 1
        star_player_count = await self.star_player_count(tag)
        if star_player_count < 1:
            star_player_count = 1
        # Multiply win rate by star player count
        score = win_rate * star_player_count

        return score
