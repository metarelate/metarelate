MetaRelate Predicates
*********************


MetaRelate Vocabulary
=====================

The MetaRelate vocabulary is used to define a mapping relationship between metadata collections.  It enables the assertion that one metadata collection is translationally equivalent to another metadata collection from a different scope.

Classes
=======

.. _`Component`:

Component
-----------

URI: http://www.metarelate.net/predicates/index.html#Component

URI: :ref:`Component`.

Definition: A collection of metadata statements within a defined type, as defined by the secondary rdf:type of the Component.

Label: Component


Mapping
-------

URI: http://www.metarelate.net/predicates/index.html#Mapping

Definition: An annotated assertion that one Component is translationally equivalent to one other Component.

Label: Mapping


ValueMap
--------

URI: http://www.metarelate.net/predicates/index.html#ValueMap

Definition: A value transfer between the source and target Components of the mapping.

Label: ValueMap



Properties
==========

invertible
-----------

URI:  http://www.metarelate.net/predicates/index.html#invertible

Definition: a "True"/"False" flag to indicate if the reciprocal relationship (target => source) is valid

Label:  invertible



source
--------

URI:  http://www.metarelate.net/predicates/index.html#source

Definition: a metarelate Component which this mapping translates from 

Label:  source


target
--------

URI:  http://www.metarelate.net/predicates/index.html#target

Definition: a metarelate Component which this mapping translates to

Label:  target


identifier
----------

URI:  http://www.metarelate.net/predicates/index.html#identifier

Definition: a predicate which is used to identify this resource

Label:  identifier


identifiedBy
------------

URI:  http://www.metarelate.net/predicates/index.html#identifiedBy

Definition: one of a collection of predicates used to identify the resource

Label:  identifiedBy


