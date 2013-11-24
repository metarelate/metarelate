Translation Use Case: Merge to Trunk
*************************************

Author: Mark Hedley

Owner: AVD Team

Version: 1

August 14, 2012

 * Primary actor: a admin
 * Goal: merged edits to the repository
 * Dependencies:

   * Edit Mappings

Main Success Scenario
=====================

To achieve the goal the actor will:

 #. Evaluate the pull request:

    * Check the validation rules pass;
    * Check changes have been agreed by all owners;
    * Check approvers have agreed all changes of state to approved;

 #. Branch their local repository
 #. merge changes from the pull request
 #. recheck validation rules
 #. push changes to the local master.
 #. push local master to the central repository.

