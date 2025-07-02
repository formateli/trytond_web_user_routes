# This file is part of Tryton web user react project.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
