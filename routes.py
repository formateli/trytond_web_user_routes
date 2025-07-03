# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging
from trytond.wsgi import app
from trytond.protocols.wrappers import Response, with_pool, with_transaction
from .web_user_routes import WebUserRoutes

logger = logging.getLogger(__name__)

@app.route('/<database_name>/web-user-register', methods=['POST'])
@with_pool
@with_transaction()
def web_user_register(request, pool):
    wur = WebUserRoutes(Response, logger)
    return wur.web_user_register(request, pool)


@app.route('/<database_name>/web-user-tokens',
        methods=['POST', 'PUT', 'DELETE'])
@with_pool
@with_transaction()
def web_user_token(request, pool):
    wur = WebUserRoutes(Response, logger)
    return wur.web_user_token(request, pool)


@app.route('/<database_name>/web-user-me', methods=['GET'])
@with_pool
@with_transaction()
def web_user_me(request, pool):
    wur = WebUserRoutes(Response, logger)
    return wur.web_user_me(request, pool)
