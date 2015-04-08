#!/bin/bash

# When you copy templates from CKAN you end up with already translated translations in your pot file.
# This script filters them out.

CURR_DIR=$(readlink -m $0/..)
SRC_DIR=$(readlink -m $0/../../../../..)

# TODO traverse also other plugins

# Find strings that we have reused from core CKAN
msgcat --use-first --more-than=1 $SRC_DIR/ckan/ckan/i18n/ckan.pot $CURR_DIR/ckanext-danepubliczne.pot -o $CURR_DIR/ckanext-danepubliczne-reused.pot

# Leave only unique strings in our pot
msgcat --unique $CURR_DIR/ckanext-danepubliczne.pot $CURR_DIR/ckanext-danepubliczne-reused.pot -o $CURR_DIR/ckanext-danepubliczne.pot

rm $CURR_DIR/ckanext-danepubliczne-reused.pot