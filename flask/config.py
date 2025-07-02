# This file is part of Tryton web user react project.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    TRYTON_DATABASE = os.environ.get('TRYTON_DATABASE', None)
    TRYTON_CONFIG = os.environ.get(
            'TRYTON_CONFIG',
            os.environ.get('TRYTOND_CONFIG', None)
            )
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') is not None
    LOG_PATH = os.environ.get('LOG_PATH', 'log')
    TESTING = False
