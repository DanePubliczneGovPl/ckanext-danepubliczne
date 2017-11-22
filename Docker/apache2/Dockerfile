From ubuntu:16.04


RUN apt-get update && \
    apt-get install -y \
      apache2 \
      cron \
      language-pack-pl \
      language-pack-pl-base \
      unzip \
      gettext-base \
      git \
      php-gd php-apcu php-mysqli php-memcached php-memcache php-xml php-soap php-zip \
      php-cli php-common php-bcmath php-curl php-gd php-geoip \
      php-imagick  php-intl php-json php-msgpack php-mcrypt php-mysql \
      php-xml php-readline  php-tidy php-mbstring php-opcache \
      libapache2-mod-php \
      && rm -rf /var/lib/apt/lists/* \
      && apt-get clean -y


# Enable apache2 modules

RUN a2enmod ssl rewrite proxy proxy_http headers

# Certificates and apache2 configs

COPY certs/ /etc/ssl/certs/
COPY conf-enabled/ /etc/apache2/conf-enabled/
COPY apache2.conf /etc/apache2/apache2.conf
COPY sites-enabled/ckan.conf-stack /etc/apache2/sites-enabled/
COPY sites-enabled/piwik.conf-stack /etc/apache2/sites-enabled/
COPY .htpasswd /etc/apache2/

# Remove default config and disable other_vhost_access.log
RUN rm /etc/apache2/sites-enabled/000-default.conf && rm /etc/apache2/conf-enabled/other-vhosts-access-log.conf

# PHP.ini setup

COPY php.ini /etc/php/apache2/
COPY memcache.ini /etc/php//mods-available/memcache.ini

# Install piwik

ADD http://builds.piwik.org/piwik.zip /var/www/html/
RUN cd /var/www/html/ && unzip piwik.zip && \
    cd /var/www/html/ && rm piwik.zip && \
    chown -R www-data: /var/www/html/

ADD piwik-config.ini.php-stack /var/www/html/piwik/config/

# Add startup script

ADD run /usr/sbin/run
RUN chmod +x /usr/sbin/run

CMD ["/usr/sbin/run"]