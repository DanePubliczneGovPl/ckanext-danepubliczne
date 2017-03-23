#!/bin/bash

export CKAN_INI=/etc/ckan/prod.ini
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

workon ckan
paster --plugin=ckan tracking update
