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
    def web_user_register(response, request, pool, logger, auth_email=True):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')

        try:
            args = request.get_json(False)

            user = WebUser.search([('email', '=', args['username'])])
            if user:
                return WebUserRoutes._response_exception(
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
            return WebUserRoutes._response_exception(
                    response, e, 403, logger)
        except Exception as e:
            return WebUserRoutes._response_exception(
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
                    return WebUserRoutes._response_exception(
                        response,
                        'User {} not found. Verify your email and password.'.format(
                            auth['username']),
                        401, logger)
                if auth_email:
                    if not user.email_valid:
                        return WebUserRoutes._response_exception(
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

        try:
            auth = request.authorization
            user = WebUser.get_user(auth.token)
            if user is None:
                return WebUserRoutes._response_exception(
                    response, 'Invalid token.', 401, logger)
            return user.to_json()
        except Exception as e:
            return WebUserRoutes._response_exception(
                    response, e, 500, logger)

    @staticmethod
    def web_user_email_verify(response, request, pool, logger):
        WebUser = pool.get('web.user')

        try:
            args = request.get_json(False)
            logger.info('TOKEN: ' + args['token'])

            fr = WebUser.search([('email', '=', 'formateli@gmail.com')])[0]
            logger.info("FR TOKEN: {}".format(fr.email_token))

            users = WebUser.validate_email_token([args['token']])
            if not users:
                return WebUserRoutes._response_exception(
                    response, 'Invalid email verification token',
                    500, logger)

            msg = "Email {} verified successfully".format(
                users[0].email)
            logger.info(msg)
            return {'message': msg}

        except Exception as e:
            raise Exception(e) from e
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
