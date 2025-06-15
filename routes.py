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
    User = pool.get('res.user')
    WebUser = pool.get('web.user')
    args = request.get_json(False)
    try:
        #with without_check_access():
        user = WebUser.search([('email', '=', args['username'])])
        if user:
            return Response('User already exists.', 403)
        user = WebUser(
                email = args['username'],
                password = args['password']
                )
        #User.check_valid_email([user])
        User.validate_password(args['password'], [user])
        user.save()

        #TODO Send confirmation email

    except (PasswordError, UserValidationError) as e:
        return response_exception(e, 403)
    except Exception as e:
        return response_exception(e, 500)

    return {'id': user.id}


@app.route('/<database_name>/web-user-tokens', methods=['POST'])
@allow_null_origin
@with_pool
@with_transaction()
def web_user_token(request, pool, user):
    WebUser = pool.get('web.user')
    args = request.get_json(False)


def response_exception(e, status):
    Transaction().rollback()
    if hasattr(e, 'message'):
        return Response(e.message, status)
    else:
        return Response(str(e), status)
