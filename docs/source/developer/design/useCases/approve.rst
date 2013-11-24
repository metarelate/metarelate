Translation Use Case: Approve
******************************

Author: Mark Hedley

Owner: AVD Team

Version: 1

August 14, 2012



 * Primary actor: an approver
 * Goal: an approved set of state changes
 * Dependencies:

   * propose for approval


Main Success Scenario
======================

To achieve the goal the actor will:

 #. Be assigned a ticket for a set of changes of state:

    * the change set will include a number of ‘proposed’ mappings.

 #. The approver will analyse the mappings and their change of state.
 #. The approver will initiate an ‘Edit’ process:

    * all mappings which the approver agrees with will change state to ‘approved’;
    * all mappings which the approver does not agree with will change state to ‘draft’;
    * no mappings may remain as ‘proposed’;
    * no other edits may take place within this branch.

 #. The ticket is updated by the approver with the reasoning behind these state edits.
 #. The approver will initiate a ‘Pull Request’ to update the repository with the state changes.

