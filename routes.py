# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging
from trytond.wsgi import app
from trytond.protocols.wrappers import Response, with_pool, with_transaction
from .web_user_routes import WebUserRoutes

logger = logging.getLogger(__name__)
AUTH = False

@app.route('/<database_name>/web-user-register', methods=['POST'])
@with_pool
@with_transaction()
def web_user_register(request, pool):
    return WebUserRoutes.web_user_register(
            Response, request, pool, logger, AUTH)


@app.route('/<database_name>/web-user-tokens',
        methods=['POST', 'PUT', 'DELETE'])
@with_pool
@with_transaction()
def web_user_token(request, pool):
    return WebUserRoutes.web_user_token(
            Response, request, pool, logger, AUTH)


@app.route('/<database_name>/web-user-me', methods=['GET'])
@with_pool
@with_transaction()
def web_user_me(request, pool):
    return WebUserRoutes.web_user_me(
            Response, request, pool, logger)


@app.route('/<database_name>/web-user-password', methods=['PUT'])
@with_pool
@with_transaction()
def web_user_password(request, pool):
    return WebUserRoutes.web_user_password(
            Response, request, pool, logger)


@app.route('/<database_name>/web-user-password-reset', methods={'POST', 'PUT'})
@with_pool
@with_transaction()
def web_user_password_reset(request, pool):
    return WebUserRoutes.web_user_password_reset(
            Response, request, pool, logger)


@app.route('/<database_name>/web-user-avatar/<uuid>', methods={'GET'})
@with_pool
@with_transaction()
def web_user_avatar(request, pool, uuid):
    return WebUserRoutes.web_user_avatar(
            Response, request, pool, logger, uuid)


@app.route('/<database_name>/web-user-email-verify', methods={'PUT'})
@with_pool
@with_transaction()
def web_user_email_verify(request, pool):
    return WebUserRoutes.web_user_email_verify(
            Response, request, pool, logger)
