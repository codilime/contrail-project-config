#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import yaml
import lxml
import subprocess
from lxml import etree

zuul_var_path = sys.argv[1]
manifest_path = sys.argv[2]

def dump_xml(node):
    return etree.tostring(node, pretty_print=True).decode()

def del_node(node):
    node.getparent().remove(node)

def get_project(zuul_var, short_name):
    for project, data in zuul_var['_projects'].items():
        if data['short_name'] == short_name:
            return data

    msg = "Zuul does not know about project {}.\n".format(short_name)
    msg += "Make sure it is defined in ``required-projects'' for this job."
    raise RuntimeError(msg)

with open(zuul_var_path, 'r') as zuul_var_file:
  zuul_var = yaml.load(zuul_var_file)

with open(manifest_path, 'r') as manifest_file:
  manifest = etree.parse(manifest_file)

project = manifest.find('//project[@name="{}"]'.format('contrail-controller'))
project.attrib['remote'] = 'ddd'

for remote in manifest.xpath('//remote'):
    del_node(remote)

for default in manifest.xpath('//default'):
    del_node(default)

remotes = {}
for project in zuul_var['projects']:
    remotes[project['canonical_hostname']] = etree.Element('remote', name=project['canonical_hostname'], fetch='file://' + zuul_var['executor']['src_root'] + '/' + project['canonical_hostname'] + '/Juniper')
    remotes[project['canonical_hostname']].tail = '\n'

for remote in remotes.values():
    manifest.getroot().insert(0,remote)

for project in manifest.xpath('//project'):
    name = project.attrib['name']
    zuul_project = get_project(zuul_var, name)
    project.attrib['remote'] = zuul_project['canonical_hostname']
    head = subprocess.check_output(['git', 'symbolic-ref', 'HEAD'], cwd=zuul_var['executor']['work_root'] + '/' + zuul_project['src_dir'])
    project.attrib['revision'] = head[:-1]

# XXX(kklimonda): Remove after contrail-packaging has been added to contrail-vnc
for repo_name, repo_path in []:
    if not manifest.find('//project[@name="%s"]' % (repo_name,)):
        project = get_project(zuul_var, repo_name)
        repo_node = etree.Element("project", name=project['short_name'], remote=project['canonical_hostname'], path=repo_path)
        repo_node.tail = '\n'

        head = subprocess.check_output(['git', 'symbolic-ref', 'HEAD'], cwd=zuul_var['executor']['work_root'] + '/' + project['src_dir'])
        repo_node.attrib['revision'] = head[:-1]
        manifest.getroot().append(repo_node)

with open(manifest_path, 'w') as manifest_file:
    manifest_file.write(dump_xml(manifest))
