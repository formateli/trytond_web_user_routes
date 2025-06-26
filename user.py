# This file is part of Web User Routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta


class User(metaclass=PoolMeta):
    __name__ = 'web.user'

    def to_json(self):
        if self.party:
            name = self.party.rec_name
        else:
            name = self.email

        res = {
            'id': self.id,
            'name': name,
            'email': self.email,
        }
        return res

    @classmethod
    def create_web_user(cls, pool, args):
        Party = pool.get('party.party')
        user = cls(
            email = args['username'],
            password = args['password'],
            party = Party(
                    name = args['name']
                )
            )
        return user
