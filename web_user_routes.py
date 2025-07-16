# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from functools import wraps
from trytond.config import config
from trytond.transaction import Transaction
from trytond.res.user import PasswordError
from trytond.modules.web_user.exceptions import UserValidationError
#from trytond.protocols.wrappers import Response

AVATAR_TIMEOUT = config.getint(
    'web', 'avatar_timeout', default=7 * 24 * 60 * 60)


def login_required():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = args[0]
            request = args[1]
            pool = args[2]
            logger = args[3]
            UserSession = pool.get('web.user.session')

            try:
                auth = request.authorization
                session = None
                sessions = UserSession.search([('key', '=', auth.token)])
                if sessions:
                    session = sessions[0]
                if session is None:
                    return _response_exception(
                        response, 'Session not found.', 401, logger)

                if session.expired and not session.user.stay_logged_in:
                    return _response_exception(
                        response, 'Session expired.', 401, logger)

                nargs = args + (session.user,)

                return func(*nargs, **kwargs)

            except Exception as e:
                return _response_exception(
                        response, e, 500, logger)
        return wrapper
    return decorator


class WebUserRoutes:

    @staticmethod
    def web_user_register(response, request, pool, logger, auth_email=True):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')

        try:
            args = request.get_json(False)

            user = WebUser.search([('email', '=', args['username'])])
            if user:
                return _response_exception(
                    response,
                    'User with email {} already exists.'.format(args['username']),
                    403, logger)
            user = WebUser.create_web_user(pool, args)
            User.validate_password(args['password'], [user])
            user.save()
            User.generate_avatar([user])
            logger.info("AUTH_EMAIL: {}".format(auth_email))
            if auth_email:
                logger.info('Sending email verification to {}'.format(user.email))
                WebUserRoutes._check_email_config()
                WebUser.validate_email([user])
            logger.info(
                    '{} registered. Waiting for verification.'.format(user.email))

            return response(None, 204)

        except (PasswordError, UserValidationError) as e:
            return _response_exception(
                    response, e, 403, logger)
        except Exception as e:
            return _response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_token(response, request, pool, logger, auth_email=True):
        WebUser = pool.get('web.user')
        UserSession = pool.get('web.user.session')

        try:
            auth = request.authorization

            if request.method == 'DELETE':
                UserSession.remove(auth.token)
                return response(None, 204)

            if request.method == 'POST':
                user = WebUser.authenticate(auth['username'], auth['password'])
                if user is None:
                    return _response_exception(
                        response,
                        'User {} not found. Verify your email and password.'.format(
                            auth['username']),
                        401, logger)
                if auth_email:
                    if not user.email_valid:
                        return _response_exception(
                            response,
                            'Email {0} for User {1} has not been validated.'.format(
                                user.email,
                                user.party.name if user.party else 'Unkwnon'),
                            401, logger)

                key = user.new_session()
                return {'access_token': key}

            if request.method == 'PUT':
                sessions = UserSession.search([('key', '=', auth.token)])
                session = None
                if sessions:
                    session = sessions[0]
                if session is None:
                    return _response_exception(
                            response, 'Session not found.', 404, logger)
                key = session.key
                if session.expired:
                    if not user.stay_logged_in:
                        return _response_exception(
                                response,
                                'Session expired for {}'.format(user.email),
                                401, logger)
                    user = session.user
                    UserSession.remove(session.key)
                    key = user.new_session()
                return {'access_token': key}

            return _response_exception(
                response,
                'Invalid request method {}.'.format(request.method),
                405, logger)

        except Exception as e:
            return _response_exception(response, e, 500, logger)

    @staticmethod
    def web_user_me(response, request, pool, logger):
        WebUser = pool.get('web.user')

        try:
            auth = request.authorization
            user = WebUser.get_user(auth.token)
            if user is None:
                return _response_exception(
                    response, 'Invalid token.', 401, logger)
            return user.to_json()
        except Exception as e:
            return _response_exception(
                    response, e, 500, logger)

    @login_required()
    @staticmethod
    def web_user_password(response, request, pool, logger, user=None):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')

        try:
            args = request.get_json(False)

            old_user = WebUser.authenticate(
                    user.email, args['old_password'])
            if old_user is None:
                return _response_exception(
                        response, 'Invalid password.', 404, logger)

            User.validate_password(args['password'], [user])
            user.password = args['password']
            user.save()
            msg = "Password for {} changed successfully".format(
                user.party.name)
            logger.info(msg)
            return {'message': msg}

        except (PasswordError, UserValidationError) as e:
            return _response_exception(
                    response, e, 403, logger)
        except Exception as e:
            return _response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_password_reset(response, request, pool, logger, auth_email=True):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')
        try:
            args = request.get_json(False)

            if request.method == 'POST':
                users = WebUser.search([('email', '=', args['email'])])
                if not users:
                    return _response_exception(
                        response, 'Email not found.', 404, logger)
                user = users[0]
                if auth_email:
                    logger.info(
                            'Sending email verification to {}'.format(
                                user.email))
                    WebUserRoutes._check_email_config()
                    WebUser.reset_password([user])
                    return {
                        'message': "Email was sent to {} for reset password process.".format(
                            user.email)
                        }

                return _response_exception(
                    response, "Email system not working.", 500, logger)

            if request.method == 'PUT':
                users = WebUser.search([('email', '=', args['email'])])
                if not users:
                    return _response_exception(
                        response, 'User not found.', 404, logger)
                user = users[0]
                User.validate_password(args['password'], [user])
                res = WebUser.set_password_token(
                        user.email, args['token'], args['password'])
                if res:
                    return {'message': 'Password reset successfully.'}
                return _response_exception(
                        response, 'Inalid token.', 404, logger)

            return _response_exception(
                    response, 'Inalid request.', 500, logger)

        except (PasswordError, UserValidationError) as e:
            return _response_exception(
                    response, e, 403, logger)
        except Exception as e:
            return _response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_email_verify(response, request, pool, logger):
        WebUser = pool.get('web.user')

        try:
            args = request.get_json(False)
            logger.info('TOKEN: ' + args['token'])

            users = WebUser.validate_email_token([args['token']])
            if not users:
                return _response_exception(
                    response, 'Invalid email verification token',
                    500, logger)

            msg = "Email {} verified successfully".format(
                users[0].email)
            logger.info(msg)
            return {'message': msg}

        except Exception as e:
            return _response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_avatar(response, request, pool, logger, uuid):
        Avatar = pool.get('ir.avatar')

        try:
            avatars = Avatar.search([
                    ('uuid', '=', uuid),
                    ])
            if not avatars:
                return _response_exception(
                        response, 'Avatar not found', 404, logger)
            avatar = avatars[0]

            size = int(request.args.get('s', 32))

            response = response(avatar.get(size), mimetype='image/jpeg')
            response.headers['Cache-Control'] = (
                'max-age=%s, public' % AVATAR_TIMEOUT)
            response.add_etag()

            return response

        except Exception as e:
            return _response_exception(response, e, 500, logger)

    @staticmethod
    def _check_email_config():
        def get_config(section, key):
            val = config.get(section, key, default=None)
            if val is None:
                err = "{0}/{1} not configured.".format(section, key)
                raise ValueError(err)
        get_config('web', 'reset_password_url') 
        get_config('web', 'email_validation_url')
        get_config('email', 'uri')
        get_config('email', 'from')


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
