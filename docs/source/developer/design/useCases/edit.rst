Translation Use Case: Edit
***************************

Author: Mark Hedley

Owner: AVD Team

Version: 1

August 14, 2012


 * Primary actor: an editor
 * Goal: a set of edits to the repository


Main Success Scenario
======================

To achieve the goal the actor will:

 #. Obtain a referenced copy of the translation information; this involves:

    • forking the centrally managed repository;
    • downloading the forked repository to a local workspace;
    • branching the local repository;

 #. Obtain an editing tool for working with the source:

    • the project will supply an editing tool;
    • batch import of information will be supported;
    • single shard edits via forms will be supported;

 #. Obtain a query tool for working with the source

    • the project will supply a query tool;

 #. make edits to the source on the local branch;
 #. ‘Validate’ these edits:

    • validation will often highlight further edits which may be needed.;

 #. push the branch containing the completed edits to the editor owned public fork;
