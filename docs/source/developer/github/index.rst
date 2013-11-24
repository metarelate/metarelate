Github Information Management
*****************************

The MetaRelate project uses Github to manage and maintain the translation information.

Translation information is stored as RDF turtle in ASCII files in a Github repository.   This can be retrieved and parsed for use in applications.

The RDF turtle in files is thus the primary source for the project.  A triple database is used to provide interactions with the data, on a contributors own machine, but this triple database does not persist as far as the project is concerned.  All persistent information is written out to ASCII files for storage in the repository.

Updating Translations
=====================

To provide updates, the information and the management application should be used together to make a set of additive changes to the RDF turtle.  This change can then be proposed, as a pull request, to the main Github repository.

A member of the metarelate management team will evaluate the pull request and work with the pull requester to merge the proposed changes into the repository.



Github 
==========

Managing Information Across a Distributed Group of Developers
--------------------------------------------------------------

The expectation for this project is that contributors will be working separately on subsets of the translation relationships.  These contributors should be able to work independently and trial their changes on different implementations.

Changes need to be managed to ensure that the information coherence is maintained; constraints are implemented as information validation rules.

A work flow, external to the translation repository, is being developed involving additions being put up for inclusion and evaluated before they are included.

Additions to the repository are likely to come in sets, representing cases such as coherent scope extensions and point fixes.

This thought process has lead the project to look at a distributed software development work flow to manage the information, treating the repository as a collection of source code.

Human in the Loop
-----------------

The nature of updates to the repository and the project work flow requires there to be a human in the loop, accepting updates or pushing them back to contributors for rework.

This particularly lends itself to a managed change involving a contributor and reviewer.

Expectation on Contributors
----------------------------

This approach puts a significant expectation on potential collaborators.  They must be prepared to:

* install software, including the metarelate software, on a local machine;
* work with the git version control system to:

 * branch
 * manage change
 * merge

* work with the Github work flow, forking and submitting pull requests;
* use the metarelate API to export information from a local triple store.

This is viewed as a significant barrier to adoption.



Alternative - A Centralised System
------------------------------------

A centralised system involving a live service which contributors log into is being considered, but it is currently deemed a reserve candidate.

There is a significant overhead in maintaining a live service which supports user editing, including authorisation and authentication, information security, service availability and management of change processes.

Race conditions on incompatible changes can be particularly challenging to manage.

The proposed oversight prior to acceptance of a change puts a timeliness implication on a live system which is more manageable with a staged change system, such as a repository. 

In particular the human in the loop is in a particularly challenging position if they are required to manage concurrent changes being made to the system in its live state.


Document Based Merging of Unordered Graphs
-------------------------------------------

Git has a powerful system for managing parallel changes and merging changes together.  It is designed to work on source code, inherently ordered information.  All changes are recorded by git, enabling parallel developments to be merged together.

Where a file has had the information reordered as part of an edit the git merging system may have significant challenges identifying information changes as opposed to reordering of collections.


Ordering Exported ASCII File Content
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It would be plausible for this project to introduce an ordering process at the point where data is written to file, but this process would be crucial to the successful management of the information, a significant risk.

RDF turtle has been chosen as the persistent format due to its inherent readability compared to other RDF forms, particularly for collections of triples sharing a subject (records).  This is viewed as the least suitable format for ordering with an algorithm.

Additive File Collections
^^^^^^^^^^^^^^^^^^^^^^^^^^

For the metarelate project, the nature of the information being persisted long term is that it is immutable.  All 'changes' involve the creation of new triples, some of which reference existing triples.  There is no part of the work flow which requires the alteration of an existent triple.

This lends itself to an approach where all additions to the persistent information, made during an edit session on a triple database, may be written out to a new file.  The files are collected into folders representing named graphs.  A hash of the file contents is used to uniquely identify the file.       

This removes the requirement for merging with Git, as all changes to the repository create new files.

An associated issue with this approach is that the possibility of duplicate triples is introduced in the persistent store.  Interestingly Jena appears to eliminate duplicate triples during load, which may be deemed to reduce the impact of this issue but does preclude the triple store from being used to evaluate additions for duplicate triples during a pull request.

Unordered Merging
^^^^^^^^^^^^^^^^^^

The output may be unordered but an enhanced merge process designed which is able to identify informational differences independent of order and merge appropriately.  This appears a very hard thing to pull off.

Appending to File
^^^^^^^^^^^^^^^^^^

If the constraint that triples are immutable is sound, then all additions may be appended to existent files.  

Each file may be its own named graph, for example.

This has the advantage that two independent developers may make somewhat overlapping but different sets of additions.  The first one to merge will add their new triples.  The second to merge will need to incorporate the changes from the first, which will be contained in a logical place in a file.  This fits reasonably with the git merge logic and is expected to deliver a manageable process.

As such this is the currently preferred solution.

