#!/bin/sh
set -e

# URL for the primary database, in the format expected by sqlalchemy (required
# unless linked to a container called 'db')
: ${CKAN_SQLALCHEMY_URL:=}
# URL for solr (required unless linked to a container called 'solr')
: ${CKAN_SOLR_URL:=}
# URL for redis (required unless linked to a container called 'redis')
: ${CKAN_REDIS_URL:=}

CONFIG="${CKAN_CONFIG}/ckan.ini"

abort () {
  echo "$@" >&2
  exit 1
}

set_environment () {
  export CKAN_SQLALCHEMY_URL=${CKAN_SQLALCHEMY_URL}
  export CKAN_SOLR_URL=${CKAN_SOLR_URL}
  export CKAN_REDIS_URL=${CKAN_REDIS_URL}
  export CKAN_STORAGE_PATH=${CKAN_STORAGE_PATH}
  export CKAN_SITE_URL=${CKAN_SITE_URL}
}

write_config () {
  # Note that this only gets called if there is no config, see below!
  ckan-paster make-config --no-interactive ckan "$CONFIG"

  # The variables above will be used by CKAN, but
  # in case want to use the config from ckan.ini use this
  #ckan-paster --plugin=ckan config-tool "$CONFIG" -e \
  #    "sqlalchemy.url = ${CKAN_SQLALCHEMY_URL}" \
  #    "solr_url = ${CKAN_SOLR_URL}" \
  #    "ckan.redis.url = ${CKAN_REDIS_URL}" \
  #    "ckan.storage_path = ${CKAN_STORAGE_PATH}" \
  #    "ckan.site_url = ${CKAN_SITE_URL}"
}

link_postgres_url () {
  local user=$DB_ENV_POSTGRES_USER
  local pass=$DB_ENV_POSTGRES_PASSWORD
  local db=$DB_ENV_POSTGRES_DB
  local host=$DB_PORT_5432_TCP_ADDR
  local port=$DB_PORT_5432_TCP_PORT
  echo "postgresql://${user}:${pass}@${host}:${port}/${db}"
}

link_solr_url () {
  local host=$SOLR_PORT_8983_TCP_ADDR
  local port=$SOLR_PORT_8983_TCP_PORT
  echo "http://${host}:${port}/solr/ckan"
}

link_redis_url () {
  local host=$REDIS_PORT_6379_TCP_ADDR
  local port=$REDIS_PORT_6379_TCP_PORT
  echo "redis://${host}:${port}/1"
}

# If we don't already have a config file, bootstrap
if [ ! -e "$CONFIG" ]; then
  write_config
fi

# Set environment variables
if [ -z "$CKAN_SQLALCHEMY_URL" ]; then
  if ! CKAN_SQLALCHEMY_URL=$(link_postgres_url); then
    abort "ERROR: no CKAN_SQLALCHEMY_URL specified and linked container called 'db' was not found"
  else
    #If that worked, use the DB details to wait for the DB
    export PGHOST=${DB_PORT_5432_TCP_ADDR}
    export PGPORT=${DB_PORT_5432_TCP_PORT}
    export PGDATABASE=${DB_ENV_POSTGRES_DB}
    export PGUSER=${DB_ENV_POSTGRES_USER}
    export PGPASSWORD=${DB_ENV_POSTGRES_PASSWORD}

    # wait for postgres db to be available, immediately after creation
    # its entrypoint creates the cluster and dbs and this can take a moment
    for tries in $(seq 30); do
      psql -c 'SELECT 1;' 2> /dev/null && break
      sleep 0.3
    done
  fi
fi

if [ -z "$CKAN_SOLR_URL" ]; then
  if ! CKAN_SOLR_URL=$(link_solr_url); then
    abort "ERROR: no CKAN_SOLR_URL specified and linked container called 'solr' was not found"
  fi
fi

if [ -z "$CKAN_REDIS_URL" ]; then
  if ! CKAN_REDIS_URL=$(link_redis_url); then
    abort "ERROR: no CKAN_REDIS_URL specified and linked container called 'redis' was not found"
  fi
fi

set_environment

if [ ! -f "/usr/lib/ckan/default/src/ckanext-danepubliczne/config/template.ini" ]; then
    envsubst < /etc/ckan/ckan.ini.base > /etc/ckan/default/ckan.ini
    cd /usr/lib/ckan/default/src/ckanext-danepubliczne/config && \
    ckan-paster make-config ckan template.ini > /dev/null && \
    grep beaker.session.secret template.ini >> /etc/ckan/default/ckan.ini && \
    grep app_instance_uuid template.ini >> /etc/ckan/default/ckan.ini

fi

# Initializes the Database
##ckan-paster --plugin=ckan datastore set-permissions | psql --set ON_ERROR_STOP=1
ckan-paster --plugin=ckan db init -c /etc/ckan/default/ckan.ini
ckan-paster --plugin=ckanext-archiver archiver init -c /etc/ckan/default/ckan.ini
ckan-paster --plugin=ckanext-qa qa init -c /etc/ckan/default/ckan.ini
ckan-paster --plugin=ckanext-report report initdb -c /etc/ckan/default/ckan.ini

# Default user admin for development stage

if [ "${STAGE}" = "dev" ]; then

    ckan-paster --plugin=ckan user admin -c /etc/ckan/default/ckan.ini > /tmp/user 2>&1

    if cat /tmp/user | grep -q "apikey"
      then echo "Default user admin found"
      else
        echo "Adding user admin"
        ckan-paster --plugin=ckan user add admin email=admin@danepubliczne.gov.pl password=Password1 -c /etc/ckan/default/ckan.ini
        ckan-paster --plugin=ckan sysadmin add admin -c /etc/ckan/default/ckan.ini
    fi

fi



#cron -f &pu
service supervisor start &



#tail -f /var/log/dpkg.log


exec "$@"
