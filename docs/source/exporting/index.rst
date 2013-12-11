Exporting Translation Information
*********************************

The metarelate API provides programmatic access to the information in the knowledge base.

This enables fine grained access to mappings, filtered by a variety of criteria allowing the information to be extracted and put into a form as required by a paritcular application.

The principle is to use the knowledge base and it's encoded contexts for mapping information to retrieve the required trnaslations and provide these in a form which allows them to be used by a software application.

This can be done by writing out static files for use by another code base.

For examples of this approach, see:

 * `Iris <https://www.scitools.org.uk/iris>`_ making use of the metarelate metOcean translation information, from the metOcean-mapping knowledge store, in the `iris-code-generators <https://github.com/SciTools/iris-code-generators>`_ project.

This can also be done by using the API as a live service and querying on demand for translations.  This approach has not been implemented yet, to my knowledge.
