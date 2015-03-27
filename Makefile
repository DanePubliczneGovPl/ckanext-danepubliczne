## File downloaded from https://github.com/opendatatrentino/ckan-custom-translations/blob/master/Makefile

##============================================================
## This makefile does many tasks:
##
##   * Aggregate .pot files from different projects
##   * Aggreagate .po translations from different projects
##   * Creates translation files from .pot + .po
##   * Compiles .po -> .mo
##============================================================

## ---- % begin configuration % ----

## Note: you can override configuration variables
##       by passing them on the ``make`` command line:
##
##  make SOURCESDIR=/path/to/src PLUGINS="one two" LANGUAGES="en_GB it fr de"

## We expect to find ``ckan`` and ``ckanext-{plugin}``
## for each plugin in this directory.
SOURCESDIR := ..

## List of plugin names

PLUGINS := ckanext-danepubliczne

## Languages to consider for translations
LANGUAGES := pl en

## ---- % end configuration % ----


## Source .pot files for translations
SOURCE_POTS := i18n/custom.pot $(SOURCESDIR)/ckan/ckan/i18n/ckan.pot
SOURCE_POTS += $(foreach plugin,$(PLUGINS),$(SOURCESDIR)/ckanext-$(plugin)/ckanext/$(plugin)/i18n/ckanext-$(plugin).pot)
AGGREGATE_POT := i18n/all.pot

## Source .po files for translations

## WARNING! We cannot include i18n/%/LC_MESSAGES/ckan.po
##          here, as we would have a circular dependency!

SOURCE_POS := $(SOURCESDIR)/ckan/ckan/i18n/%/LC_MESSAGES/ckan.po
SOURCE_POS += $(foreach plugin,$(PLUGINS),$(SOURCESDIR)/ckanext-$(plugin)/ckanext/$(plugin)/i18n/%/LC_MESSAGES/ckanext-$(plugin).po)
AGGREGATE_PO := i18n/all_%.po
AGGREGATE_PO_TARGETS := $(foreach lang,$(LANGUAGES),aggregate_pos_$(lang))
AGGREGATE_PO_FILES := $(foreach lang,$(LANGUAGES),i18n/all_$(lang).po)

## Custom .po for a language
CUSTOM_PO := i18n/%/LC_MESSAGES/ckan.po
CUSTOM_PO_TARGETS := $(foreach lang,$(LANGUAGES),custom_po_$(lang))
CUSTOM_PO_FILES := $(foreach lang,$(LANGUAGES),i18n/$(lang)/LC_MESSAGES/ckan.po)

## Actual .po/.mo files to build
MO_TARGETS := $(patsubst %.po,%.mo,$(CUSTOM_PO_FILES))


all: $(MO_TARGETS)

##------------------------------------------------------------
## POT aggregation

aggregate_pots: $(AGGREGATE_POT)

## Merge .pot files by concatenating all the .pots
$(AGGREGATE_POT): $(SOURCE_POTS)
	@echo "--- Merging .pot files"
	msgcat --use-first $^ -o $@


##------------------------------------------------------------
## PO aggregation
## This is a bit tricky, as we need to aggregate
## A, B and C into A..

aggregate_pos_%: $(AGGREGATE_PO)

## Create an aggregate .po file by merging all the translations
$(AGGREGATE_PO): $(SOURCE_POS)
	@echo "--- Creating aggregate .po file"

	@# We need the name of the custom .po for this language
	@# but we need to do some trickery to get it..
	msgcat --use-first $(patsubst $(AGGREGATE_PO),$(CUSTOM_PO),$@) $^ -o $@


##------------------------------------------------------------
## Create new custom translation, filling the new .pot
## with aggregate .po, for this language

custom_po_%: $(CUSTOM_PO)

$(CUSTOM_PO): $(AGGREGATE_PO) $(AGGREGATE_POT)
	@echo "--- Merging translations in new .pot file"
	msgmerge $^ -o $@


##------------------------------------------------------------
## Compile .po files into .mo files

build_mo: $(MO_TARGETS)

$(MO_TARGETS): %.mo: %.po
	@echo "--- Building .po -> .mo files"
	msgfmt $< -o $@


##------------------------------------------------------------
## Clean up garbage

clean:
	rm -f $(MO_TARGETS)
	rm -f $(AGGREGATE_POT)
	rm -f $(AGGREGATE_PO_FILES)