#!/bin/bash

remote_user=ckan-v5
backup_user=remote-ckan1
backup_server=<BACKUP_SERVER>

echo "Starting retrieving backup at $(date)"

apachectl stop
supervisorctl stop celery

sudo -u postgres dropdb ckan
# sudo -u postgres dropdb datastore
sudo -u postgres createdb -O ckan ckan -E utf-8
# sudo -u postgres createdb -O ckan datastore -E utf-8

echo "Retrieving latest backup.."

sudo -u ckan ssh $remote_user@$backup_server -C "cat /home/backup/last/$backup_user.timestamp"
sudo -u ckan ssh $remote_user@$backup_server -C "cat /home/backup/last/$backup_user-ckan.pgdump" | sudo -u postgres pg_restore -d ckan

apachectl start
supervisorctl start celery

echo "Rebuilding search index.."

su ckan
workon ckan
paster --plugin=ckan search-index rebuild

echo "Finished at $(date)"

# Be sure to have identical beaker.session.secret and app_instance_uuid configuration variables
# Be sure to have the same PIP packages installed (do freeze and req install)
