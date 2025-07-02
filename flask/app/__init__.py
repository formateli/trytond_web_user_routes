# This file is part of Tryton web user react project.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config
from flask import Flask
from flask_tryton import Tryton
from app.web_user import WebUser


tryton = Tryton()
wu = WebUser()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    tryton.init_app(app)
    wu.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if app.config['LOG_TO_STDOUT']:
        _create_logger_handler(app, logging.StreamHandler, logging.INFO)
    else:
        if not os.path.exists(app.config['LOG_PATH']):
            os.mkdir(app.config['LOG_PATH'])
        _create_logger_handler(app, RotatingFileHandler, logging.INFO,
                               app.config['LOG_PATH'] + '/web-user.log')

    app.logger.setLevel(logging.INFO)
    app.logger.info('Web User startup')

    return app


def _create_logger_handler(app, handler_class, log_level,
                       path=None, max_bytes=10240, backup_count=10):
    if path is not None:
        handler = handler_class(path, maxBytes=max_bytes, backupCount=backup_count)
    else:
        handler = handler_class()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'))
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
