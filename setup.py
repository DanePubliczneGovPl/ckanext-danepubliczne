from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='''ckanext-danepubliczne''',

    # Versions should comply with     .  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='1.0.0.dev0',

    description='''Extension handling DanePubliczne.gov.pl (PublicData.gov.pl) site''',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/DanePubliczneGovPl/ckanext-danepubliczne',

    # Author details
    author='''Fundacja ePanstwo / ePF Foundation''',
    author_email='''webmaster@epf.org.pl''',

    # Choose your license
    license='AGPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='''CKAN ckanext dane publiczne government pl''',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=[
        'biryani >=0.10.4, <0.11',
    ],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    include_package_data=True,
    package_data={
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points='''
[ckan.plugins]
dane_publiczne=ckanext.danepubliczne.plugin:DanePubliczne
dane_publiczne_organization=ckanext.danepubliczne.schema.organization:OrganizationForm
dane_publiczne_dataset=ckanext.danepubliczne.schema.dataset:DatasetForm
dane_publiczne_categories=ckanext.danepubliczne.schema.category:Category
dane_publiczne_articles=ckanext.danepubliczne.schema.article:Article
piwik=ckanext.danepubliczne.piwik:PiwikPlugin

[babel.extractors]
ckan=ckan.lib.extract:extract_ckan

[paste.paster_command]
init = ckanext.danepubliczne.lib.cli:Init
    ''',
)
