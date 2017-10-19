=============
nodepool-base
=============

Tasks to deal with image metadata and other Nodepool cloud specific tweaks.

Environment variables:

`NODEPOOL_SCRIPTDIR` path to copy Nodepool scripts from. It is set
automatically by Nodepool.  For local hacking override it to where your scripts
are. Default:
`$TMP_MOUNT_PATH/opt/git/openstack-infra/project-config/nodepool/scripts`.

