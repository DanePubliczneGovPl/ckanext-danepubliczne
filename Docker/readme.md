Dokument w trakce tworzenia.  Wersja 0.1 


# CKAN STACK  - dokumentacja 

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [CKAN STACK  - dokumentacja](#ckan-stack-dokumentacja)
	- [1. Opis obrazów](#1-opis-obrazów)
	- [2. Start stacka](#1-start-stacka)
		- [2.1 katalog i źródła](#11-katalog-i-źródła)
		- [2.2 Plik z konfiguracją](#12-plik-z-konfiguracją)
		- [2.3 Budowa obrazu](#13-budowa-obrazu)
		- [2.4 Uruchomienie stacka](#14-uruchomienie-stacka)
		- [2.5 Werfyikacja stanu kontenerów](#15-werfyikacja-stanu-kontenerów)

<!-- /TOC -->

### 1. Opis obrazów

Stacka składa się z następujących obrazów

- apache2 - obraz dla kontenera z serwerem apache, służy jako proxy dla usług w stacku
- ckan-base - bazowy obraz CKAN budowany z forka https://github.com/DanePubliczneGovPl/ckan.  Dla większej elastyczności zostało to oddzielone.  NIE definujemy tu żadnych konfiguracji specyficznych dla DanePubliczne. 
- ckan - obraz dla kontenera CKAN ze wszyskimi konfiguracjami DanePubliczne
- datapusher - datapusher
- datastore - obraz baza danych pgsql dla datastore
- pgsql - obraz baza danych pgsql dla ckan
- solr - obraz indeksera SOLR


### 2. Start stacka

Poniższy opis pokazuje pierwsze uruchomienie stacka. Zakładam, że masz dostęp do shela.

####  2.1 katalog i źródła

Zakładasz katalog i pobierasz źródła
```
mkdir /home/ckan
cd /home/ckan && git clone git@github.com:DanePubliczneGovPl/ckanext-danepubliczne.git ckan
```

####  2.2 Plik z konfiguracją

Tworzysz plik /home/ckan/ckan/Docker/.env z konfiguracją stacka

```

#### SETUP ####
###############

# STAGE
# Jesli jest stage dev to default admin user jest dodawany

STAGE=dev

# ip na którym będzie nasłuchiwać stack
PUBLIC_IP=192.168.50.22 

#### APACHE ####
################

# sciezki do certyfikatów

CERT_KEY=/etc/ssl/certs/mysitename.key
CERT_FILE=/etc/ssl/certs/mysitename.crt

# domena pod którą będzie działa strona

DOMAIN=stage.danepubliczne.gov.pl
CKAN_SITE_URL=https://${DOMAIN}

#### PIWIK ####
################

PIWIK_URL=https://stats.danepubliczne.gov.pl
PIWIK_HOST=mysql
PIWIK_USERNAME=piwik
PIWIK_PASS=******
PIWIK_DB=piwik
PIWIK_SALT=6a2a3c15512315463f4acdf5f91f2caf
PIWIK_TRUSTED_HOSTS=stats.dp.gov.pl

# certyfikaty dla domeny piwika

CERT_FILE_STATS=/etc/ssl/certs/mysitename.key
CERT_KEY_STATS=/etc/ssl/certs/mysitename.crt
```
#### 2.3 Budowa obrazu
```
cd /home/ckan/ckan/Docker && docker-compose build
```
#### 2.4 Uruchomienie stacka
```
cd /home/ckan/ckan/Docker && docker-compose up -d
```
#### 2.5 Werfyikacja stanu kontenerów
```
cd /home/ckan/ckan/Docker && docker-compose ps
```


### FAQ