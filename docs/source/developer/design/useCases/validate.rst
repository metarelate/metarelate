Translation Use Case: Validate
*******************************

Author: Mark Hedley

Owner: AVD Team

Version: 1

August 14, 2012

* Primary actor: an editor
* Goal: confirmation that the dataset is valid, according to the internal consistency rules

Main Success Scenario
======================

To achieve the goal the actor will:

1. Run the validation rules on the dataset
2. Obtain feedback on each validation failure:

   * listing shards are involved in the failure
   * for each shard, which validation rule they failed


Validation Rules
=================

Terms
-----

* Namespace: MO-UM:

  * MO-UM.STASH:

    * Met Office STASH Code

  * MO-UM.FC:

    * Met Office Field Code

* Namespace: CF

  * CF.SN:

    * CF standard name

  * CF.CU:

    * CF canonical unit

* Namespace: WMO-GRIB

  * WMO-GRIB.PC:

    * WMO-GRIB Parameter Code

* Namespace: MO-NI

  * MO-NI.PC:

    * Met Office NIMROD Parameter Code

Rules
------

#. No attribute may have a value of ‘’: an empty string
#. MO-UM.STASH to CF.SN:

   (a) one MO-UM.STASH shard to many CF.SN shards is banned

#. MO-UM.FC to CF.SN:

   (a) one MO-UM.FC shard to many CF.SN is banned
   (#) many MO-UM.FC shards to one CF.SN is banned

#. WMO-GRIB.PC to CF.SN:

   (a) one WMO-GRIB.PC shard to many CF.SN is banned

#. WMO-NI.PC to CF.SN:

   (a) one MO-NI.PC shard to many CF.SN shards is banned
   (#) many MO-NI.PC shard to one CF.SN shard is banned

#. No closed paths may exist between namespaces:

   (a) directed acyclic graphs only

#. All units of measure which link to CF shards must be able to be transformed to the relevant CF.CU
#. Preferred Routing:

   (a) Where validation rule 6 requires a deprecation change, the preferred path is through the CF namespace.

