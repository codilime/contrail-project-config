import os

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

MASTER_RELEASE = '5.0'

class ReleaseType(object):
    CONTINUOUS_INTEGRATION = 'continuous-integration'
    NIGHTLY = 'nightly'

def main():
    module = AnsibleModule(
        argument_spec=dict(
            branch=dict(type='str', required=True),
        )
    )

    branch = module.params['branch']

    if branch == 'master':
        version = MASTER_RELEASE
    elif branch.startswith("R"):
        version = branch[1:]
    else:
        version = None

    contrail_version = {'contrail_version': version}

    module.exit_json(changed=True, ansible_facts=contrail_version)
