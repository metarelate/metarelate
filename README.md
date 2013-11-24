metarelate
===========

metarelate is a knowledge base system for managing metadata translations.

To contribute to a translation project, the static data from that project should be used to populate a local triple store which the management software may access. 

Dependencies
------------
* Apache Jena - http://jena.apache.org/
* Fuseki - http://jena.apache.org/documentation/serving_data/
* Python - http://python.org/
* Django - https://www.djangoproject.com/

Installation
------------

* Apache Jena - http://jena.apache.org/
    1. Download the 'apache-jena' release from http://www.apache.org/dist/jena/binaries/
    2. Unpack the archive
* Fuseki - http://jena.apache.org/documentation/serving_data/
    1. Download the 'jena-fuseki' release from http://www.apache.org/dist/jena/binaries/
    2. Unpack the archive
* Python - http://python.org/
    1. install Python = 2.7
* Django - https://www.djangoproject.com/
    1. install Django >= 1.3
* pydot - https://code.google.com/p/pydot/
    1. install pydot >= 1.0
* Configure the metarelate metarelate software
    1. lib/metarelate/etc/site.config provides paths to libraries and static data
    2. see lib/metarelate/etc/README.md

Configuration
-------------

Local configuration files are required to set up a metarelate environment:

* ./lib/metarelate/etc/site.cfg
 * see ./lib/metarelate/etc/sample.site.cfg
* ./lib/editor/settings_local.py
 * see ./lib/editor/sample_settings_local.py

Run
---

* Run the application:
    1. ./lib/editor/run.sh


