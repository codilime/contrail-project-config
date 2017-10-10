#!/usr/bin/python

import os
import re

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: prepare_packaging_vars

short_description: Prepare variables describing package being built.

description:
  - "This module prepares a number of variables that describe package that is being built,
for example upstream version, package version, source location, and workspace layout."

options:
  zuul_project: Zuul dictionary with packaging project information.

  zuul_project_is_packaging: Whether the main zuul project is packaging repo, or code repo.

  source_repo: An optional Zuul object for upstream source project. If not given, module will try to locate it based on the packaging repo.

author:
  - OpenContrail Developers <dev@lists.opencontrail.org>
'''


def _debian_get_name_versions(changelog_path):
    '''Returns tuple (package_name (epoch, upstream_version, debian_version)) based on changelog'''
    if not os.path.exists(changelog_path):
        raise RuntimeError("changelog is missing at %s" % (changelog_path,))
    with open(changelog_path, "r") as fh:
        manifest = fh.readline()

    matcher = "^(?P<name>[\w-]+)\ \((?P<version>.*)\).*$"
    groups = re.match(matcher, manifest)
    if not groups:
        raise RuntimeError("Could not parse debian/changelog")
    return groups.group(1), groups.group(2)



def get_package_name_versions(module):
    """Returns a dictionary with package information."""
    params = module.params

    src_dir = params['zuul_project']['src_dir']
    if not os.path.exists(src_dir):
        raise RuntimeError("Could not find packaging repository under %s" % (src_dir,))

    distro = params['distribution']
    release = params['release']
    if distro == "ubuntu":
        debian_path = os.path.join(src_dir, distro, release, "debian/")
        changelog_path = os.path.join(debian_path, "changelog")

        package_name, version = _debian_get_name_versions(changelog_path)

        try:
            (epoch, rest) = version.split(":")
        except ValueError:
            epoch, rest = None, version

        upstream, debian = rest.split('-')
        target_dir = "%s-%s" % (package['name'], package['version']['upstream'])

        return {
            'name': package_name,
            'debian_dir': debian_path,
            'full_version': version,
            'version': {
                'epoch': epoch,
                'upstream': upstream,
                'distro': debian
            },
            'target_dir': target_dir,
        }

    else:
        raise RuntimeError("Unsupported distribution: %s" % (distro,))


def get_upstream_path(module):
    zuul_project, upstream_repo = module.params['zuul_project'], module.params['source_repo']
    package = get_package_name_versions(module)

    if upstream_repo:
        local_path = upstream_repo['src_dir']
    else:
        # deduce local_path based on zuul_project
        # XXX: This assumes that both packaging repository and upstream source are pulled from
        #      the same zuul connection.
        packaging_path = zuul_project['src_dir']
        packaging_short_name = zuul_project['short_name']

        upstream_repo_name = re.sub("^packaging-", "", packaging_short_name)
        packaging_org_dir = "/".join(packaging_path.split("/")[:-1])

        local_path = os.path.join(packaging_org_dir, upstream_repo_name)
        if not os.path.exists(local_path):
            local_path = None

    if local_path is None:
        return None

    return {"source_dir": local_path }


result = dict(
    changed=False,
    original_message='',
    message='',
)

def main(testing=False):
    module = AnsibleModule(
        argument_spec=dict(
            zuul_project=dict(type='dict', required=True),
            zuul_project_is_packaging=dict(type='bool', required=False, default=True),
            source_repo=dict(type='dict', required=False, default=None),
            distribution=dict(type='str', required=True),
            release=dict(type='str', required=True),
        ),
    )

    try:
        result['package'] = get_package_name_versions(module)
        upstream_source = get_upstream_path(module)
        if upstream_source:
            result['upstream'] = upstream_source
    except RuntimeError as e:
        module.fail_json(msg=e.message, **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main(testing=True)
