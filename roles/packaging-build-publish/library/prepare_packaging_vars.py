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
  packaging_repo: Zuul dictionary with packaging project information.

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

    src_dir = params['packaging_repo']['src_dir']
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

        return {
            'name': package_name,
            'full_version': version,
            'version': {
                'epoch': epoch,
                'upstream': upstream,
                'distro': debian
            }
        }

    else:
        raise RuntimeError("Unsupported distribution: %s" % (distro,))


result = dict(
    changed=False,
    original_message='',
    message='',
)

def main(testing=False):
    module = AnsibleModule(
        argument_spec=dict(
            packaging_repo=dict(type='dict', required=True),
            source_repo=dict(type='dict', required=False, default=None),
            distribution=dict(type='str', required=True),
            release=dict(type='str', required=True),
        ),
    )

    try:
        result['package'] = get_package_name_versions(module)
    except RuntimeError as e:
        module.fail_json(msg=e.message, **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main(testing=True)