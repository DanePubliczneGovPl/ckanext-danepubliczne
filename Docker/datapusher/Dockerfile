FROM python:2-slim


ENV DATAPUSHER_HOME /usr/lib/ckan/


#Install the required packages
RUN apt-get -qq update
RUN apt-get -qq install -y git
RUN apt-get clean && rm -fr /tmp/* /var/tmp/* && rm -rf /var/lib/apt/lists/*

#Switch to source directory
WORKDIR $DATAPUSHER_HOME

RUN pip install -e git+https://github.com/DanePubliczneGovPl/datapusher@develop#egg=datapusher
RUN pip install -r src/datapusher/requirements.txt


EXPOSE 8800

#Run the DataPusher
CMD [ "python", "src/datapusher/datapusher/main.py", "src/datapusher/deployment/datapusher_settings.py"]