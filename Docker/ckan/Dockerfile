FROM ckan-base


RUN mkdir -p /home/ckan

# Update apt-get
RUN DEBIAN_FRONTEND=noninteractive apt-get update

# Install additional packages
RUN DEBIAN_FRONTEND=noninteractive apt-get install -q -y git wget curl libxml2-dev libxslt1-dev python-dev libffi-dev libjpeg-dev cron supervisor gettext-base \
      && rm -rf /var/lib/apt/lists/* \
      && apt-get clean -y

##############################
#Install ckan-dane-publiczne
##############################

ADD https://raw.githubusercontent.com/DanePubliczneGovPl/ckanext-danepubliczne/develop/requirements-danepublicznegovpl.txt /tmp/requirements-danepublicznegovpl.txt

# Comment out ckan  cause we use image
RUN sed -i '/release-v2.3.5/s/^/#/g' /tmp/requirements-danepublicznegovpl.txt

# Let's do some work

RUN ckan-pip install -r /tmp/requirements-danepublicznegovpl.txt && rm /tmp/requirements-danepublicznegovpl.txt

# Some backward compatibility
RUN ln -s /usr/lib/ckan/default/src /home/ckan/src \
    && ln -s /etc/ckan/default/ckan.ini /etc/ckan/prod.ini \
    && mkdir /var/log/ckan/

# Copy ini files
ADD conf/default.ini /etc/ckan/ckan.ini.base
RUN cat /home/ckan/src/ckanext-danepubliczne/config/who.ini > /etc/ckan/default/who.ini

# Enable cron

RUN ln -s /home/ckan/src/ckanext-danepubliczne/scripts/cron.d/ckan-tracking /etc/cron.d/ckan-tracking
RUN ln -s /home/ckan/src/ckanext-danepubliczne/scripts/cron.d/reports_qa /etc/cron.d/reports_qa
RUN chmod u+x /home/ckan/src/ckanext-danepubliczne/scripts/ckan-tracking.sh

# Install celery and cron


COPY conf/celery-supervisor.conf /etc/supervisor/conf.d/
COPY conf/cron-supervisor.conf /etc/supervisor/conf.d/

# SetUp EntryPoint
COPY ckan-entrypoint.sh /
RUN chmod +x /ckan-entrypoint.sh
ENTRYPOINT ["/ckan-entrypoint.sh"]

# Start ckan
CMD ["ckan-paster","serve","/etc/ckan/default/ckan.ini"]
