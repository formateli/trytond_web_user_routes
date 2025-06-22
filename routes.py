# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.wsgi import app
from trytond.res.user import PasswordError
from trytond.modules.web_user.exceptions import UserValidationError
from trytond.protocols.wrappers import (allow_null_origin,
    Response, abort, with_pool, with_transaction)
from trytond.transaction import Transaction, without_check_access
import logging

logger = logging.getLogger(__name__)

@app.route('/<database_name>/web-user-register', methods=['POST'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_register(request, pool):
    Party = pool.get('party.party')
    User = pool.get('res.user')
    WebUser = pool.get('web.user')
    args = request.get_json(False)
    try:
        user = WebUser.search([('email', '=', args['username'])])
        if user:
            return Response('User already exists.', 403)
        user = WebUser(
                email = args['username'],
                password = args['password'],
                party = Party(
                    name = args['name']
                    )
                )
        User.validate_password(args['password'], [user])
        user.save()

        #TODO Send confirmation email

    except (PasswordError, UserValidationError) as e:
        return response_exception(e, 403)
    except Exception as e:
        return response_exception(e, 500)

    return {'id': user.id}


@app.route('/<database_name>/web-user-tokens', 
        methods=['POST', 'PUT', 'DELETE'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_token(request, pool):
    WebUser = pool.get('web.user')
    UserSession = pool.get('web.user.session')

    auth = request.authorization

    #logger.info(str(auth))
    #logger.info(str(auth.type))
    #logger.info(str(auth.parameters))

    try:
        if request.method == 'POST':
            user = WebUser.authenticate(auth['username'], auth['password'])
            if user is None:
                return response_exception('Not found.', 401)
            logger.info('user: ' + str(user))
            key = user.new_session()
            return {'access_token': key}
        elif request.method == 'PUT':
            sessions = UserSession.search([('key', '=', auth.token)])
            session = None
            if sessions:
                session = sessions[0]
            if session is None:
                return response_exception('Session not found.', 404)
            if sesion.expired:
                user = sesion.user
                UserSession.remove(session.key)
                key = user.new_session()
                return {'access_token': key}
            return {'access_token': session.key}
        elif request.method == 'DELETE':
            UserSession.remove(auth.token)
        else:
            return response_exception('Invalid request method.', 500)

    except Exception as e:
        return response_exception(e, 500)


@app.route('/<database_name>/web-user-me', methods=['GET'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_me(request, pool):
    WebUser = pool.get('web.user')

    auth = request.authorization

    #logger.info(str(auth))
    #logger.info(str(auth.type))
    #logger.i<nfo(str(auth.parameters))
    #logger.info(str(auth.token))

    try:
        user = WebUser.get_user(auth.token)
        if user is None:
            return response_exception('Invalid.', 401)
        return user.to_json()
    except Exception as e:
        return response_exception(e, 500)


def response_exception(e, status):
    Transaction().rollback()
    if hasattr(e, 'message'):
        message = e.message
    else:
        message = str(e)

    if status >= 500:
        logger.error(message)
    else:
        logger.warn(message)

    return Response(message, status)
