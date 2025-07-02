# This file is part of Tryton web user react project.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import functools
from flask import request, Response
from app import tryton, wu
from app.main import bp


@bp.route('/<database_name>/web-user-register', methods=['OPTIONS', 'POST'])
@wu.route()
@tryton.transaction()
def web_user_register():
    User = tryton.pool.get('res.user')
    WebUser = tryton.pool.get('web.user')
    args = request.get_json(False)
    try:
        user = WebUser.search([('email', '=', args['username'])])
        if user:
            return wu.response_exception(
                    'User {} already exists.'.format(args['username']), 403)
        user = WebUser.create_web_user(tryton.pool, args)
        User.validate_password(args['password'], [user])
        user.save()
        return user.to_json()

        #TODO Send confirmation email

    except (wu.WuPasswordError, wu.WuUserValidationError) as e:
        return wu.response_exception(e, 403)
    except Exception as e:
        return wu.response_exception(e, 500)


@bp.route('/<database_name>/web-user-tokens',
        methods=['OPTIONS', 'POST', 'PUT', 'DELETE'])
@wu.route()
@tryton.transaction()
def web_user_token():
    WebUser = tryton.pool.get('web.user')
    UserSession = tryton.pool.get('web.user.session')

    auth = request.authorization

    try:
        if request.method == 'DELETE':
            UserSession.remove(auth.token)
            return Response(None, 204)

        if request.method == 'POST':
            user = WebUser.authenticate(auth['username'], auth['password'])
            if user is None:
                return wu.response_exception(
                        'Not found. {}.'.format(auth['username']), 401)
            key = user.new_session()
            return {'access_token': key}

        if request.method == 'PUT':
            sessions = UserSession.search([('key', '=', auth.token)])
            session = None
            if sessions:
                session = sessions[0]
            if session is None:
                return wu.response_exception('Session not found.', 404)
            key = session.key
            if session.expired:
                if not user.stay_logged_in:
                    return wu.response_exception(
                        'Session expired. {}.'.format(session.user.email), 401)
                user = session.user
                UserSession.remove(session.key)
                key = user.new_session()
            return {'access_token': key}

        return wu.response_exception(
                'Invalid request method. {}'.format(request.method), 405)

    except Exception as e:
        return wu.response_exception(e, 500)


@bp.route('/<database_name>/web-user-me', methods=['OPTIONS', 'GET'])
@wu.route()
@tryton.transaction()
def web_user_me():
    WebUser = tryton.pool.get('web.user')
    auth = request.authorization
    try:
        user = WebUser.get_user(auth.token)
        if user is None:
            return wu.response_exception('Invalid user token', 401)
        return user.to_json()
    except Exception as e:
        return wu.response_exception(e, 500)
