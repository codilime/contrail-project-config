# Copyright 2013 OpenContrail Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# We will need this to do pattern matching
import zuul.change_matcher
import logging
import re

def set_log_url(item, job, params):
    if hasattr(item.change, 'refspec'):
        path = "%s/%s/%s/%s" % (
            params['ZUUL_CHANGE'][-2:], params['ZUUL_CHANGE'],
            params['ZUUL_PATCHSET'], params['ZUUL_PIPELINE'])
    elif hasattr(item.change, 'ref'):
        path = "%s/%s/%s" % (
            params['ZUUL_NEWREV'][:2], params['ZUUL_NEWREV'],
            params['ZUUL_PIPELINE'])
    else:
        path = params['ZUUL_PIPELINE']
    params['BASE_LOG_PATH'] = path
    params['LOG_PATH'] = path + '/%s/%s' % (job.name,
                                            params['ZUUL_UUID'][:7])


def single_use_node(item, job, params):
    set_log_url(item, job, params)
    params['OFFLINE_NODE_WHEN_COMPLETE'] = '1'


def reusable_node(item, job, params):
    set_log_url(item, job, params)

def check_for_recheck_clean(item, job, params):
    '''Look for a 'recheck no bug clean' comment'''

    # Should never happen if we are called through oc_ci_pre_systest_check(), but be paranoid
    if not isinstance(item.change, zuul.model.Change): return

    log = logging.getLogger("gerrit.Gerrit") # Borrowing/using zuul's logger
    try:
        # Sanity check...
        if not item.change._data.has_key('comments'): return

        # The $?<clean> in re allows us to use group('clean') later
        recheck = re.compile('(?i)^Patch Set \d+:\s+recheck(( (?:bug|lp)[\s#:]*(\d+))|( no bug))(?P<clean>\s+clean)?\s*$')
        rvw_id = item.change.number

        log.info("Review #%s: Looking for 'recheck clean'" % rvw_id)

        fail = re.compile("^Patch Set %s:\s+Doesn't seem to work\s+Build failed" % item.change.patchset)
        comments = item.change._data.get('comments')

        # First we look for last 'build failed' message (searching backwards)
        for i in xrange(len(comments)-1, -1, -1):
            if fail.match(comments[i].get('message')): break

        # We got to comment 0 without matching, so no 'Build failed' msg
        if i == 0: return

        # Now let's find the 'recheck' comment
        for j in xrange(i+1, len(comments)):
            m = recheck.match(comments[j].get('message'))
            if m and m.group('clean'):
                log.info("Review #%s: Doing 'recheck clean' (without pre-built images)" % rvw_id)
                params['CI_OC_RECHECK_CLEAN'] = True
                return
    except:
        log.error("Caught an exception trying to analyze comments\n")

# For controller jobs, Check whether tempest tests should be run.
# The python function looks files in src/config/ or src/discovery
def check_for_tempest(item, job, params):
    '''Look at the files in the job and the change, set CI_OC_RUN_TEMPEST=1 as required'''

    # XXX 2016-05-31 tempest jobs are broken for ubuntu14-kilo. Until
    #                resolved, only consider tempest for ubuntu14-juno
    if not re.search('^ci-contrail-controller-systest-.*-juno$', job.name): return

    # Should never happen if we are called through oc_ci_pre_systest_check(), but be paranoid
    if not isinstance(item.change, zuul.model.Change): return

    # This is the pattern we want to match: anything in src/api-lib,
    # src/config, src/discovery, or src/schema
    fm = zuul.change_matcher.FileMatcher('src/(api-lib|config|discovery|schema)/')
    params['CI_OC_RUN_TEMPEST'] = fm.matches(item.change)

def oc_ci_pre_systest_checks(item, job, params):
    '''Invoke any/all job-specific parameter functions'''

    log = logging.getLogger("gerrit.Gerrit")
    if not isinstance(item.change, zuul.model.Change):
        log.debug("oc_ci_pre_systest_checks: not a Change, skipping pre-systest checks")
        return

    log.info("Looking at item.change == %s" % item.change)

    if re.search('^ci-.*-systest-.*$', job.name):
        check_for_recheck_clean(item, job, params)

    # XXX 2016-05-31 tempest jobs are broken for ubuntu14-kilo. Until
    #                resolved, only consider tempest for ubuntu14-juno
    if re.search('^ci-contrail-controller-systest-.*-juno$', job.name):
        check_for_tempest(item, job, params)
