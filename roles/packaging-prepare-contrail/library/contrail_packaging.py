import os

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

result = dict(
    changed=False,
    original_message='',
    message='',
)

MASTER_RELEASE = '5.0'

class ReleaseType(object):
    CONTINUOUS_INTEGRATION = 'continuous-integration'
    NIGHTLY = 'nightly'

def main():
    module = AnsibleModule(
        argument_spec=dict(
            zuul=dict(type='dict', required=True),
            release_type=dict(type='str', required=False, default=ReleaseType.CONTINUOUS_INTEGRATION)
        )
    )

    zuul = module.params['zuul']
    release_type = module.params['release_type']

    branch = zuul['branch']
    change = zuul['change']
    patchset = zuul['patchset']
    date = datetime.now().strftime("%Y%m%d%H%M%S")

    version = {'epoch': None}
    if branch == 'master':
        version['upstream'] = MASTER_RELEASE
    else:
        version['upstream'] = branch[1:]

    if release_type == 'continous-integration':
        # Versioning in CI consists of change id, pachset and date
        version['debian'] = "~{changeset}.{patchset}~{date}".format(
            changetset=changeset, patchset=patchset, date=date
        )
    elif release_type == 'nightly':
        version['debian'] = "~{date}".format(date=date)
    else:
        module.fail_json(
            msg="Unknown release_type: %s" % (release_type,), **result
        )

    debian_dir = None
    for project in zuul['projects']:
        if project['short_name'] == 'contrail-packages':
            debian_dir = project['src_dir']

    if not debian_dir:
        module.fail_json(
            msg="Could not find contrail-packages repository" % (release_type,), **result
        )

    debian_dir = os.path.join(debian_dir, "debian/contrail/debian")
    target_dir = "contrail-%s" % (version['upstream'],)

    result['packaging'] = {
        'name': 'contrail',
        'debian_dir': debian_dir,
        'full_version': full_version,
        'version': version,
        'target_dir': target_dir,
    }

    module.exit_json(**result)
