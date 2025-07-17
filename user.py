# This file is part of Web User Routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields

class User(metaclass=PoolMeta):
    __name__ = 'web.user'

    stay_logged_in = fields.Boolean('Stay logged in')

    def to_json(self, lang=None):
        headers = User._get_json_headers()
        data = User._get_json_data([self])[0]

        res = {}
        i = 0
        for dt in data:
            res[headers[i][0]] = dt
            i += 1

        return {'headers': headers, 'data': res}

    @classmethod
    def to_json_users(cls, users, lang=None):
        headers = cls._get_json_headers()
        data = cls._get_json_data(users)
        return {'headers': headers, 'data': data}

    @classmethod
    def _get_json_headers(cls):
        headers = [
            ['id', 'char', 'ro'],
            ['name'],
            ['email', 'email', 'ro'],
            ['avatar_uuid', 'bool']
            ]
        return headers

    @classmethod
    def _get_json_data(cls, users):
        data = []
        for user in users:
            if user.party:
                name = user.party.rec_name
            else:
                name = user.email

            data.append([
                user.id,
                name,
                user.email,
                user.avatars[0].uuid if user.avatars else -1
                ])
        return data

    @classmethod
    def create_web_user(cls, pool, args):
        Party = pool.get('party.party')
        user = cls(
            email = args['username'],
            password = args['password'],
            stay_logged_in = args['stay_logged_in'],
            party = Party(
                    name = args['name']
                )
            )
        return user
