# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging
from trytond.wsgi import app
from trytond.res.user import PasswordError
from trytond.modules.web_user.exceptions import UserValidationError
from trytond.protocols.wrappers import (allow_null_origin,
    Response, abort, with_pool, with_transaction)
from trytond.transaction import Transaction, without_check_access

logger = logging.getLogger(__name__)

@app.route('/<database_name>/web-user-register', methods=['POST'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_register(request, pool):
    User = pool.get('res.user')
    WebUser = pool.get('web.user')
    args = request.get_json(False)
    logger.info(str(args))
    try:
        user = WebUser.search([('email', '=', args['username'])])
        if user:
            return Response('User already exists.', 403)
        user = WebUser.create_web_user(pool, args)
        User.validate_password(args['password'], [user])
        user.save()
        return user.to_json()

        #TODO Send confirmation email

    except (PasswordError, UserValidationError) as e:
        return _response_exception(e, 403)
    except Exception as e:
        return _response_exception(e, 500)


@app.route('/<database_name>/web-user-tokens',
        methods=['POST', 'PUT', 'DELETE'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_token(request, pool):
    WebUser = pool.get('web.user')
    UserSession = pool.get('web.user.session')

    auth = request.authorization

    try:
        if request.method == 'DELETE':
            logger.info('DELETE %s', auth.token)
            UserSession.remove(auth.token)
            return Response(None, 204)

        if request.method == 'POST':
            user = WebUser.authenticate(auth['username'], auth['password'])
            if user is None:
                logger.info('POST not found %s', auth['username'])
                return _response_exception('Not found.', 401)
            logger.info("POST user found: %s", user.email)
            key = user.new_session()
            return {'access_token': key}

        if request.method == 'PUT':
            sessions = UserSession.search([('key', '=', auth.token)])
            session = None
            if sessions:
                session = sessions[0]
            if session is None:
                return _response_exception('Session not found.', 404)
            key = session.key
            if session.expired:
                logger.info('PUT session expired %s', key)
                if not user.stay_logged_in:
                    return _response_exception('Session expired.', 401)
                user = session.user
                UserSession.remove(session.key)
                key = user.new_session()
                logger.info('PUT renew session %s', key)
            return {'access_token': key}

        return _response_exception('Invalid request method.', 405)

    except Exception as e:
        return _response_exception(e, 500)


@app.route('/<database_name>/web-user-me', methods=['GET'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_me(request, pool):
    WebUser = pool.get('web.user')

    auth = request.authorization

    try:
        user = WebUser.get_user(auth.token)
        if user is None:
            return _response_exception('Invalid.', 401)
        return user.to_json()
    except Exception as e:
        return _response_exception(e, 500)


def _response_exception(e, status):
    Transaction().rollback()
    if hasattr(e, 'message'):
        message = e.message
    else:
        message = str(e)

    if status >= 500:
        logger.error(message)
    else:
        logger.warning(message)

    return Response(message, status)
