from marto_python.fabfile_django import *
from fabric.api import *


prod()  # only one possible host


# ############### INITIAL DB ################

# @task
# def initial_dump_local():
#     """
#     Dump initial data from local, adding accounts
#     """
#     require('hosts')
#     require('venv_app')
#     local(f'./manage.py dumpdata {fab_settings["DUMP_INITIAL_LOCAL"]} --indent=2 > data/initial_local.json')


# ############### DEPLOY MULTILANGUAGE ################


@task
def ucdm():
    require('hosts')
    require('venv_app')
    push()
    restart()
