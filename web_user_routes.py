# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.config import config
from trytond.transaction import Transaction
from trytond.res.user import PasswordError
from trytond.modules.web_user.exceptions import UserValidationError
#from trytond.protocols.wrappers import Response

AVATAR_TIMEOUT = config.getint(
    'web', 'avatar_timeout', default=7 * 24 * 60 * 60)


class WebUserRoutes:

    @staticmethod
    def web_user_register(response, request, pool, logger):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')
        args = request.get_json(False)
        try:
            user = WebUser.search([('email', '=', args['username'])])
            if user:
                return response('User already exists.', 403)
            user = WebUser.create_web_user(pool, args)
            User.validate_password(args['password'], [user])
            user.save()
            User.generate_avatar([user])
            logger.info(
                    '{} registered. Waiting for verification.'.format(user.email))
            return response(None, 204)

           #TODO Send confirmation email

        except (PasswordError, UserValidationError) as e:
            return WebUserRoutes._response_exception(
                    response, e, 403, logger)
        except Exception as e:
            return WebUserRoutes._response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_token(response, request, pool, logger):
        WebUser = pool.get('web.user')
        UserSession = pool.get('web.user.session')

        auth = request.authorization

        try:
            if request.method == 'DELETE':
                UserSession.remove(auth.token)
                return response(None, 204)

            if request.method == 'POST':
                user = WebUser.authenticate(auth['username'], auth['password'])
                if user is None:
                    return WebUserRoutes._response_exception(
                        response,
                        'User {} not found. Verify your email and password.'.format(
                            auth['username']),
                        401, logger)
                #TODO if not user.email_verified()...
                key = user.new_session()
                return {'access_token': key}

            if request.method == 'PUT':
                sessions = UserSession.search([('key', '=', auth.token)])
                session = None
                if sessions:
                    session = sessions[0]
                if session is None:
                    return WebUserRoutes._response_exception(
                            response, 'Session not found.', 404, logger)
                key = session.key
                if session.expired:
                    if not user.stay_logged_in:
                        return WebUserRoutes._response_exception(
                                response,
                                'Session expired for {}'.format(user.email),
                                401, logger)
                    user = session.user
                    UserSession.remove(session.key)
                    key = user.new_session()
                return {'access_token': key}

            return WebUserRoutes._response_exception(
                response,
                'Invalid request method {}.'.format(request.method),
                405, logger)

        except Exception as e:
            return WebUserRoutes._response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_me(response, request, pool, logger):
        WebUser = pool.get('web.user')

        auth = request.authorization

        try:
            user = WebUser.get_user(auth.token)
            if user is None:
                return WebUserRoutes._response_exception(
                    response, 'Invalid token.', 401, logger)
            return user.to_json()
        except Exception as e:
            return WebUserRoutes._response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_avatar(response, request, pool, logger, uuid):
        logger.info('Getting avatar {}'.format(uuid))
        Avatar = pool.get('ir.avatar')

        try:
            avatars = Avatar.search([
                    ('uuid', '=', uuid),
                    ])
            if not avatars:
                return WebUserRoutes._response_exception(
                        response, 'Avatar not found', 404, logger)
            avatar = avatars[0]

            size = int(request.args.get('s', 32))

            response = response(avatar.get(size), mimetype='image/jpeg')
            response.headers['Cache-Control'] = (
                'max-age=%s, public' % AVATAR_TIMEOUT)
            response.add_etag()
            return response
        except Exception as e:
            WebUserRoutes._response_exception(response, e, 500, logger)

    @staticmethod
    def _response_exception(response, e, status, logger):
        Transaction().rollback()
        if hasattr(e, 'message'):
            message = e.message
        else:
            message = str(e)

        if status >= 500:
            logger.error(message)
        else:
            logger.warning(message)

        return response(message, status)
