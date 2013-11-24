Translation Use Case: Release
******************************

Author: Mark Hedley

Owner: AVD Team

Version: 1

August 14, 2012

* Primary actor: an Admin
* Goal: a release of the translation mappings

Main Success Scenario
=====================

To achieve the goal the actor will:

#. Set the release standard; a release may be:

   * approved only
   * draft, proposed and approved

#. initiate a new ‘Edit’

   * no mapping shards may be edited for a release edit;

#. create a release shard, with:

   * a valid and unique release number;
   * a release standard;

#. run a query to return all the mappings which will be included in the release:
#. link all of the results to the release shard
#. initiate a ‘Pull Request’.
