Information Stored 
*******************

The MetaRelate project references an information repository, which must be structured to the specifications detailed here.

These repositories store semi-structured information as `RDF`_.

.. _RDF: http://www.w3.org/RDF/


The structure of the RDF enables queries to be run on the contained data, using `SPARQL1.1`_.

.. _SPARQL1.1: http://www.w3.org/TR/sparql11-query/


The information structure is extensible, the structure is not fixed, but this description represents a minimum set which is required for the current set of queries used in the mapping manager.

Information structure  
======================

.. graphviz:: records.dot


Editing is Adding
=================

All editing of the information in the repository is additive.  Any edits made in a branch which delete content will not be merged into the main repository. 

State
=====

A number of States are allowed for Mapping record instances.  One of the allowable edit operations is to replace a mapping record with an up-versioned record with a different state; in fact the operation is additive, a new record is created which references the replaced record using a hasPrevious attribute.  

This operation is a record state transition operation.

.. graphviz:: state.dot
