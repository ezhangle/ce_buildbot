#!/usr/bin/env python
import os
import sys
import json
import requests


def main(argv):
    # Argument order is defined by git, we cannot use '--name' parameters.
    branch = argv[1]
    oldref = argv[2]    # Unused, but here for clarity.
    newref = argv[3]

    available_heads = os.listdir(os.path.join('refs', 'heads'))
    if branch not in available_heads:
        print('It is only possible to push to the following heads: {}.'.format(','.join(available_heads)))
        return 1

    builds = get_relevant_builds(branch, newref)

    return count_failed_builds(builds)


def count_failed_builds(builds):
    """
    Find the number of builds that have failed.
    :param builds: Builds thyrough which to search.
    :return: Number of failed builds in the list.
    """
    failed_builds = []
    with open('buildbot_config.json') as fd:
        cfg = json.load(fd)

    for target in cfg['targets']:
        for config in cfg[target]:
            all_builds = get_targeted_builds(builds, target, config)
            newest = get_newest_build(all_builds)

            if newest['results'] != 0:
                failed_builds.append('{} / {}'.format(target, config))

    if failed_builds:
        print('The following targets/configs failed:\n{}'.format('\n'.join(failed_builds)))
    else:
        print('All builds succeeded.')

    return len(failed_builds)


def get_targeted_builds(buildlist, target, config):
    """
    Search a list of builds for those with the specified target and config.
    :param buildlist: List of builds for the ref we are checking.
    :param target: Compilation target.
    :param config: Compilation configuration (debug/profile/release).
    :return: List of builds for the specified target and config.
    """
    selected = []
    for b in buildlist:
        if b['properties']['target'] != target:
            continue
        if b['properties']['config'] != config:
            continue
        selected.append(b)
    return selected


def get_newest_build(buildlist):
    """
    Find the latest build in the provided list.
    :param buildlist: List of builds to check.
    :return: Build with the highest buildnumber property.
    """
    newest = buildlist[0]
    for b in buildlist:
        if b['properties']['buildnumber'] > newest['properties']['buildnumber']:
            newest = b
    return newest


def get_relevant_builds(branch, ref):
    """
    Get a list of builds that were performed with the provided ref.
    :param branch: Branch to which we are pushing.
    :param ref: Reference by which to filter the list.
    :return: List of builds for the provided reference.
    """
    parameters = []
    parameters.extend(['field={}'.format(f)
                       for f in ['buildid', 'complete', 'state_string', 'properties', 'results']])
    parameters.extend(['property={}'.format(p)
                       for p in ['branch', 'buildername', 'buildnumber', 'config', 'head_ref', 'target']])
    requesturl = 'http://localhost:8010/api/v2/builds?{}'.format('&'.join(parameters))

    response = requests.get(requesturl).json()
    builds = response['builds']
    relevant_builds = []

    # Strip out builds that don't have the head_ref that we're trying to push.
    for b in builds:
        if 'head_ref' not in b['properties']:
            continue
        if b['properties']['branch'][0] != branch:
            continue
        if b['properties']['head_ref'][0] == ref:
            relevant_builds.append(b)

    # Buildbot stores properties as a list, with the second entry being the source of the property.
    for b in relevant_builds:
        b['properties'] = {p: b['properties'][p][0] for p in b['properties']}

    return relevant_builds


if __name__ == '__main__':
    sys.exit(main(sys.argv))
