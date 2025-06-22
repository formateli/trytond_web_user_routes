# This file is part of Web User Routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta


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
