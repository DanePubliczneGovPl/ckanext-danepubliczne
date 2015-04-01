#!/bin/bash

CURR_DIR=$(readlink -m $0/..)
SRC_DIR=$(readlink -m $0/../../../../..)
CURR_PLUGIN_DIRNAME=$(basename $(readlink -m $0/../../../..))
CURR_PLUGIN=${CURR_PLUGIN_DIRNAME:8}

LANGUAGES=en
PLUGINS=$CURR_PLUGIN
CKAN_I18N=$SRC_DIR/ckan/ckan/i18n/

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

  PO_FILES=""
  PO_FILES_VERBOSE=""

  # Find .po files. Filter existing files, warn about missing translations
  for plugin in $PLUGINS
  do
    plugin_po=$SRC_DIR/ckanext-$plugin/ckanext/$plugin/i18n/$LANGUAGE/LC_MESSAGES/ckanext-$plugin.po
    if [ -f $plugin_po ]; then
      PO_FILES="$PO_FILES $plugin_po"
      PO_FILES_VERBOSE="$PO_FILES_VERBOSE $plugin"
    else
      >&2 echo "  Translation $plugin[$LANGUAGE] doesn't exist. Missing $plugin_po"
    fi
  done

  OVERRIDEN_CKAN_PO="$CURR_DIR/$LANGUAGE/LC_MESSAGES/ckan_override.po"

  # Agreggate core CKAN and our .po files; our values override original ones (--use-first)
  # If we have file overriding all CKAN original translations use it (ckan_override.po)

  if [ -f $OVERRIDEN_CKAN_PO ]; then
    PO_FILES="$PO_FILES $OVERRIDEN_CKAN_PO"
    PO_FILES_VERBOSE="$PO_FILES_VERBOSE ckan[override]"
  fi

  if [ -f $CKAN_I18N/$LANGUAGE/LC_MESSAGES/ckan.po ]; then
    PO_FILES="$PO_FILES $CKAN_I18N/$LANGUAGE/LC_MESSAGES/ckan.po"
    PO_FILES_VERBOSE="$PO_FILES_VERBOSE ckan[org]"
  fi

  echo "  Aggregating translations for $LANGUAGE from files: $PO_FILES_VERBOSE. First defined translation takes precedence"
  MERGED=$CURR_DIR/$LANGUAGE/LC_MESSAGES/ckan
  echo "    msgcat --use-first $PO_FILES -o $MERGED.po"
  if ! msgcat --use-first $PO_FILES -o $MERGED.po; then exit 2; fi

  echo "  Compiling translations for $LANGUAGE"
  echo "    msgfmt $MERGED.po -o $MERGED.mo"
  if ! msgfmt $MERGED.po -o $MERGED.mo; then exit 3; fi
done