#!/usr/bin/python
#
# Copyright (c) 2017 Juniper Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

from ansible.module_utils.basic import AnsibleModule
from jinja2 import Template

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: docker_executure

short_description: Execute a command in a running docker container

description:
  - This module wraps ansible shell and command modules to simulate ansible
    command/shell modules (notably, outputting stderr/stdout as expected).

options:
  - name:
      description:
        - A name of a running container to execute commands in.
      required: true
  - shell:
      description:
        - An extended set of commands (shell script) to be executed in
          a container.
      required: false
  - executable:
      description:
        - When passed along with a ``shell'' option, a path to the executable
          to be used for running the script.
      default: /bin/sh -c '{{ shell }}'
'''

EXAMPLES = '''
- name: Execute a simple command in a docker container
  docker_execute:
    name: builder
    command: ls

- name: Execute an extended set of commands inside of a docker container
  docker_execute:
    name: builder
    shell: |
      apt-get update
      apt-get install vim
'''

def main():
    argument_spec = {
        'name': {'type': 'str', 'required': True },
        'shell': {'type': 'str', 'required': False},
        '_raw_params': {},
        'chdir': {'type': 'str', 'required': False, 'default': 'cd .'},
        'user': {'type': 'str', 'required': False},
        'executable': {'type': 'str', 'required': False, 'default': "/bin/sh -c '{{ chdir }} ; {{ shell }}'"},
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params['name']
    shell = module.params['shell']
    chdir = module.params['chdir']
    user = module.params['user']
    executable = module.params['executable']

    if user:
        user_arg = "--user %s" % (user,)
    else:
        user_arg = ""

    if shell:
        template = Template(executable)
        final_command = template.render(chdir=chdir, shell=shell)
    else:
        final_command = command

    docker_command = \
        'docker exec {user} {container} {final_command}'.format(
            user=user_arg, container=name, final_command=final_command)

    started = datetime.datetime.now()

    rc, out, err = module.run_command(args, executable='/bin/sh', use_unsafe_shell=True, encoding=None)

    finished = datetime.datetime.now()
    delta = finished - started

    if out is None:
        out = b''
    if err is None:
        err = b''

    result = dict(
        cmd=args,
        stdout=out.rstrip(b'\r\n'),
        stderr=err.rstrip(b'\r\n'),
        rc=rc,
        start=str(started),
        end=str(finished),
        delta=str(delta),
        changed=True
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)

