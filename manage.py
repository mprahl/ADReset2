#!flask/bin/python
"""
Author: StackFocus
File: app.py
Purpose: Manages the app
"""
import os
import fileinput
import flask_migrate
from re import sub
from flask_script import Manager
from adreset2 import app, db, models
from adreset2.utils import add_default_configuration_settings

app.config.from_object('config.BaseConfiguration')
migrate = flask_migrate.Migrate(app, db)
manager = Manager(app)
manager.add_command('db', flask_migrate.MigrateCommand)


@manager.command
def createdb():
    """Runs the db init, db migrate, db upgrade commands automatically,
    and adds the default configuration settings if they are missing"""
    if not os.path.isdir('db/migrations'):
        flask_migrate.init(directory='db/migrations')
    flask_migrate.migrate(directory='db/migrations')
    flask_migrate.upgrade(directory='db/migrations')
    add_default_configuration_settings()


@manager.shell
def make_shell_context():
    """Returns app, db, models to the shell"""
    return dict(app=app, db=db, models=models)


@manager.command
def clean():
    """Cleans the codebase, including database migration scripts"""
    if os.name == 'nt':
        commands = ["powershell.exe -Command \"@('*.pyc', '*.pyo', '*~', '__pycache__') |  Foreach-Object { Get-ChildItem -Filter $_ -Recurse | Remove-Item -Recurse -Force }\"",  # pylint: disable=anomalous-backslash-in-string, line-too-long
                    "powershell.exe -Command \"@('db') |  Foreach-Object { Get-ChildItem -Filter $_ | Remove-Item -Recurse -Force }\""]  # pylint: disable=anomalous-backslash-in-string, line-too-long
    else:
        commands = ["find . -name '*.pyc' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '*.pyo' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '*~' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '__pycache__' -exec rmdir {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "rm -rf db.db"]
    for command in commands:
        os.system(command)


@manager.command
def generatekey():
    """Replaces the SECRET_KEY in config.py with a new random one"""
    for line in fileinput.input('config.py', inplace=True):
        print(sub(r'(?<=SECRET_KEY = \')(.+)(?=\')', os.urandom(24).encode('hex'), line.rstrip()))


if __name__ == "__main__":
    manager.run()
