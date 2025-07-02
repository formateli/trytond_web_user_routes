# This file is part of Tryton web user react project.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes
