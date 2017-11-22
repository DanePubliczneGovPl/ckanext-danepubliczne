FROM ckan/postgresql


#SET LOCALE TO UTF8

RUN localedef -i pl_PL -c -f UTF-8 -A /usr/share/locale/locale.alias pl_PL.UTF-8
ENV LANG pl_PL.utf8

#MOVE IT LATER TO .ENV



ENV DATASTORE_USER_READ dataread
ENV DATASTORE_USER_READ_PASSWORD dataread

ENV POSTGRES_USER datastore
ENV POSTGRES_PASSWORD datastore
ENV POSTGRES_DB datastore

# INIT SCRIPT FOR DB CREATION ETC
COPY init.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init.sh
