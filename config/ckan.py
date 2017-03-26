import os

activate_this = os.path.join('/home/ckan/.virtualenvs/ckan/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from paste.deploy import loadapp

config_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prod.ini')
from paste.script.util.logging_config import fileConfig

fileConfig(config_filepath)

application = loadapp('config:%s' % config_filepath)                                                                  
