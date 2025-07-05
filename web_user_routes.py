# This file is part of web user routes module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.transaction import Transaction
from trytond.res.user import PasswordError
from trytond.modules.web_user.exceptions import UserValidationError


class WebUserRoutes:
    def __init__(self, response_class, logger):
        self.response = response_class
        self.logger = logger

    def web_user_register(self, request, pool):
        User = pool.get('res.user')
        WebUser = pool.get('web.user')
        args = request.get_json(False)
        try:
            user = WebUser.search([('email', '=', args['username'])])
            if user:
                return self.response('User already exists.', 403)
            user = WebUser.create_web_user(pool, args)
            User.validate_password(args['password'], [user])
            user.save()
            User.generate_avatar([user])
            self.logger.info(
                    '{} registered. Waiting for verification.'.format(user.email))
            return self.response(None, 204)

           #TODO Send confirmation email

        except (PasswordError, UserValidationError) as e:
            return self._response_exception(e, 403)
        except Exception as e:
            return self._response_exception(e, 500)

    def web_user_token(self, request, pool):
        WebUser = pool.get('web.user')
        UserSession = pool.get('web.user.session')

        auth = request.authorization

        try:
            if request.method == 'DELETE':
                UserSession.remove(auth.token)
                return self.response(None, 204)

            if request.method == 'POST':
                user = WebUser.authenticate(auth['username'], auth['password'])
                if user is None:
                    return self._response_exception(
                        'User {} not found. Verify your email and password.'.format(
                            auth['username']), 401)
                #TODO if not user.email_verified()...
                key = user.new_session()
                return {'access_token': key}

            if request.method == 'PUT':
                sessions = UserSession.search([('key', '=', auth.token)])
                session = None
                if sessions:
                    session = sessions[0]
                if session is None:
                    return self._response_exception(
                            'Session not found.', 404)
                key = session.key
                if session.expired:
                    if not user.stay_logged_in:
                        return self._response_exception(
                                'Session expired for {}'.format(user.email), 401)
                    user = session.user
                    UserSession.remove(session.key)
                    key = user.new_session()
                return {'access_token': key}

            return self._response_exception(
                'Invalid request method {}.'.format(request.method), 405)

        except Exception as e:
            return self._response_exception(e, 500)

    def web_user_me(self, request, pool):
        WebUser = pool.get('web.user')

        auth = request.authorization

        try:
            user = WebUser.get_user(auth.token)
            if user is None:
                return self._response_exception('Invalid token.', 401)
            return user.to_json()
        except Exception as e:
            return self._response_exception(e, 500)

    def web_user_avatar(self, request, pool, uuid):
        self.logger.info('Getting avatar {}'.format(uuid))
        Avatar = pool.get('ir.avatar')

        try:
            avatars = Avatar.search([
                    ('uuid', '=', uuid),
                    ])
            if not avatars:
                return self._response_exception('Avatar not found', 404)
            avatar = avatars[0]

            size = int(request.args.get('s', 32))

            response = self.response(avatar.get(size), mimetype='image/jpeg')
            #TODO Cache avatar
            #response.headers['Cache-Control'] = (
            #    'max-age=%s, public' % AVATAR_TIMEOUT)
            response.add_etag()
            return response
        except Exception as e:
            self._response_exception(e, 500)

    def _response_exception(self, e, status):
        Transaction().rollback()
        if hasattr(e, 'message'):
            message = e.message
        else:
            message = str(e)

        if status >= 500:
            self.logger.error(message)
        else:
            self.logger.warning(message)

        return self.response(message, status)
