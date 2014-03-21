Getting Started with MetaRelate
********************************

MetaRelate is a project to relate definitions within metadata schemes: it provides guidance on how to interpret a metadata definition from one scheme within another.

Getting started using the information requires the installation of some software, the project does not yet have a live web interface to the relationships.

The project is hosted on `Github, at MetaRelate <https://github.com/metarelate>`_

The primary tool is the Metarelate API, a programmatic interface to the knowledge management software.  The project also provides an editing interface, which can be used locally for managing information.

The API and editor is a Github repository, `MetaRelate <https://github.com/metarelate/metarelate>`_. 

Translation knowledge is held in separate projects.  

The Meteorology and Oceanography translation knowledge base is maintained at `metOcean <https://github.com/metarelate/metocean>`_.

The metarelate projects use Python, Django, Jena and Fuseki to provide the capabilities to manage a repository of translation information, an application programming interface and a user interface.

Software
=========

Metarelate is a knowledge base support system, providing information management for metadata translations.

This project provides software to manage the knowledge base and the knowledge base content. The knowledge is stored as RDF Turtle datasets in data repository, referred to as StaticData.

To contribute to the project, the required static data should be used to populate a local triple store which the management software may access. 

See the README.md for installation instructions.

The software can be run from the source, or installed, whichever is preferred.  There are run-time paths which must be managed by each session, this are controlled with user-defined environment variables.

Use
===

The metarelate API provides programmatic access to the data in the local triple store.  This API enables valid and relevant information to be retrieved and converted to a form which can be used by other applications.

Editor
------

* To run the editor application:
    1. ./run_mr_editor.py

Translation Retrieval
---------------------

The metarelate :class:`metarelate.fuseki.FusekiServer` provides programmatic access to a running server process accessing the local data set.

:class:`metarelate.fuseki.FusekiServer` is a context manager, which handles the underlying Jena processes; it is always better to call this as a context manager, to enable this process handling to work effectively; so:

.. code-block:: python

    with metarelate.fuseki.FusekiServer() as fu_p:
        ## do something useful with fu_p
	## once this indented block is exited the process will exit cleanly

To retrieve a set of ordered translations, for example from a data set with formats 'um' and 'cf' defined, :meth:`metarelate.fuseki.FusekiServer.retrieve_mapping` can be used.

.. code-block:: python

    import metarelate.fuseki
    with metarelate.fuseki.FusekiServer() as fu_p:
        mappings = fu_p.retrieve_mappings('um', 'cf')


Application Programming Interface
----------------------------------

The API provides a Python interface to the knowledge base.  

To use the API, create an instance of the metarelate.fuseki.FusekiServer class, as detailed in the API documentation.

Examples
--------

There is more information in the `exporting translations <../exporting/index.html>`_ pages.

For examples of this approach, see how Iris makes use of metarelate and the metOcean-mapping translation information in `iris-code-generators <https://github.com/SciTools/iris-code-generators>`_




Contribution
============

The project aims to collate and manage translation information from many sources.  Contributions to the knowledge base are crucial.

To contribute:

  * Create a branch in your git repository, linked to the main data project your are interested in, and check it out.
  * Load the static data into your local triple store.
  * Use the editor application to add information to the knowledge base.
  * Validate your changes against the information rules in the application.
  * Persist your changes to your local static data store.
  * Propose these changes to the relevant Metarelate github data project as a Pull Request.
