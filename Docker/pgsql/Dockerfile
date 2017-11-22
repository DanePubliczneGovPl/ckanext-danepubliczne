FROM ckan/postgresql


#SET LOCALE TO UTF8

RUN localedef -i pl_PL -c -f UTF-8 -A /usr/share/locale/locale.alias pl_PL.UTF-8
ENV LANG pl_PL.utf8

#MOVE IT LATER TO .ENV

ENV POSTGRES_USER ckan
ENV POSTGRES_PASSWORD ckan
ENV POSTGRES_DB ckan


# INIT SCRIPT FOR DB CREATION ETC
# COPY init.sh /docker-entrypoint-initdb.d/
# RUN chmod +x /docker-entrypoint-initdb.d/init.sh

