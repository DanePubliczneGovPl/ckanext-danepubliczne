#!/bin/bash

# When you copy templates from CKAN you end up with already translated translations in your pot file.
# This script filters them out.


# Find strings that we have reused from core CKAN
msgcat --use-first --more-than=1 ../../../../ckan/ckan/i18n/ckan.pot ckanext-danepubliczne.pot -o ckanext-danepubliczne-reused.pot

# Leave only unique strings in our pot
msgcat --unique ckanext-danepubliczne.pot ckanext-danepubliczne-reused.pot -o ckanext-danepubliczne.pot

rm ckanext-danepubliczne-reused.pot