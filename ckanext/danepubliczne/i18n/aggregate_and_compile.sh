#!/bin/bash

SRC_DIR=$(basename $(readlink -m ../../../..))
CURR_PLUGIN_DIRNAME=$(basename $(readlink -m ../../..))
CURR_PLUGIN=${CURR_PLUGIN_DIRNAME:8}

LANGUAGES=en
PLUGINS=$CURR_PLUGIN
CKAN_I18N=$(readlink -e ../../../../ckan/ckan/i18n/)

while getopts ":l:p:" opt; do
  case $opt in
    l) LANGUAGES="$OPTARG"
    ;;
    p) PLUGINS="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done


for LANGUAGE in $LANGUAGES
do
  echo "Processing lang $LANGUAGE"

  PLUGINS_POS=""
  PO_FILES_VERBOSE=""

  # Find .po files. Filter existing files, warn about missing translations
  for plugin in $PLUGINS
  do
    plugin_po=$SRC_DIR/ckanext-$plugin/ckanext/$plugin/i18n/$LANGUAGE/LC_MESSAGES/ckanext-$plugin.po
    if [ -f $plugin_po ]; then
      PLUGINS_POS="$PLUGINS_POS $plugin_po"
      PO_FILES_VERBOSE="$PO_FILES_VERBOSE $plugin"
    else
      >&2 echo "Translation $plugin[$LANGUAGE] doesn't exist. Missing $plugin_po
    fi
  done

  OVERRIDEN_CKAN_PO=$LANGUAGE/LC_MESSAGES/ckan.po

  # Agreggate core CKAN and our .po files; our values override original ones (--use-first)
  # If we have file overriding all CKAN original translations use it (ckan.po)

  if [ ! -f $OVERRIDEN_CKAN_PO ]; then
    PO_FILES = $PLUGINS_PO $OVERRIDEN_CKAN_PO $CKAN_I18N/$LANGUAGE/LC_MESSAGES/ckan.po
    PO_FILES_VERBOSE="$PO_FILES_VERBOSE ckan[override] ckan[org]"
  else
    PO_FILES = $PLUGINS_PO $CKAN_I18N/$LANGUAGE/LC_MESSAGES/ckan.po
    PO_FILES_VERBOSE="$PO_FILES_VERBOSE ckan[org]"
  fi

  echo "Aggregating translations for $LANGUAGE from files: $PO_FILES_VERBOSE. First defined translation takes precedence"
  MERGED=$LANGUAGE/LC_MESSAGES/merged
  msgcat --use-first $PO_FILES -o $MERGED.po

  echo "Compiling translations for $LANGUAGE"
  msgfmt $MERGED.po -o $MERGED.pot
done