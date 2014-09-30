Information Stored 
*******************

The MetaRelate project references an information repository, which must be structured to the specifications detailed here.

These repositories store semi-structured information as `RDF`_.

.. _RDF: http://www.w3.org/RDF/


The structure of the RDF enables queries to be run on the contained data, using `SPARQL1.1`_.

.. _SPARQL1.1: http://www.w3.org/TR/sparql11-query/


The information structure is extensible, the structure is not fixed, but this description represents a minimum set which is required for the current set of queries used in the mapping manager.

Editing is Adding
=================

All editing of the information in the repository is additive.  Any edits made in a branch which delete content will not be merged into the main repository. 


Information structure  
======================

A Mapping is a uniquely identified resource, consisting of a source and a target and optionally a set of valuemaps, plus a collection of context metadata statements.

The 'mr:source', 'mr:target' and the 'mr:valueMaps' provide all the functional information about the Mapping resource.

All other statements made by the Mapping resource are contextual, providing information on validity and enabling contacts to be made to manage change effectively.

.. graphviz:: records.dot



State
=====

A number of states and state changes are recognised for Mapping instances.  

When a mapping is created it is a draft mapping.  This may be updated by creating a new mapping which references the old Mapping resource using 'dc:replaces'.

A mapping may be provided with a rights statement and a collection of rightsHolder organisations.  The rights statement will be a metarelate statement regarding the quality of the information.  Such a resource is then functionally frozen; only updates to the Mapping metadata, adding new contributors and rightsHolders, will be allowed unless all rightsHolders agree on the change.

A mapping may be deprecated by a new mapping with no source or target, which replaces the deprecated mapping.


.. graphviz:: state.dot
