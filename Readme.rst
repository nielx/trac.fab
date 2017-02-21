Automation for deployment of Trac on vmdev.haiku-os.org
=======================================================

This repository contains the management tools to install and maintain Haiku's
Trac installation.

The current scripts are written for the 1.0.x branch. They have been tested
with 1.0.1 and 1.0.13, and should theoretically work with versions in
between. But why would anybody want that?

Bootstrapping a new installation
--------------------------------

Bootstrapping is the creation of a new python environment in /srv/trac

To get from bootstrapping to running, use:
 * fab <staging/production> bootstrap_python

Bootstrapping is only ever required in case the python environment is deleted
(on purpose or when moving to a new server).

Backing up an existing installation
-----------------------------------

Updating an existing installation involves a few steps. First of all you might
want to do a backup:
 * fab <staging/production> backup

This creates a .tar.bz2 backup in the root directory

Hotcopying the production environment to a test environment
-----------------------------------------------------------

 * fab staging copy_production_to_environment

This will destroy the Postgresql database and the files for the staging
environment, and will copy the current site into the backup. This is a hotcopy
and minor inconsistencies between the database and the files might occur.

Upgrading trac
--------------

 * fab <staging/production> install_trac:<VERSION>
 * fab <staging/production> deploy

The `deploy` command will upgrade the database, the wiki pages and the static
resources. It will also reload apache so that the updated software is picked
up.

Enabling/disabling an environment
---------------------------------

 * fab <staging/production> enable_environment
 * fab <staging/production> disable_environment:<ALTERNATIVE HOST NAME>