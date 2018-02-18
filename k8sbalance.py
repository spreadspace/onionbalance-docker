#!/usr/bin/env python3

SERVICE_LABEL='spreadspace.org/onion-service'
INSTANCE_ANNOT='spreadspace.org/onion-instance'
REFRESH_INTERVAL=120
SECRETS_PATH='/var/run/secrets/spreadspace.org/onionbalance'
ONIONBALANCE_CONFIG='/tmp/onionbalance.yml'
ONIONBALANCE_CONTROL='/tmp/onionbalance.control'

def get_onion_mapping(client, NAMESPACE):
    l = client.list_namespaced_pod(NAMESPACE, label_selector=SERVICE_LABEL)
    m = {}

    for pod in l.items:
        if not pod.metadata.annotations:
            continue

        if INSTANCE_ANNOT not in pod.metadata.annotations:
            continue

        service = pod.metadata.labels[SERVICE_LABEL]
        instance = pod.metadata.annotations[INSTANCE_ANNOT]

        if service not in m:
            m[service] = set()

        m[service].add(instance)

    return m


def onionbalance_config(mapping):
    import json, os.path
    return json.dumps({
        'STATUS_SOCKET_LOCATION': ONIONBALANCE_CONTROL,
        'REFRESH_INTERVAL': REFRESH_INTERVAL,
        'services': [
            { 'key': os.path.join(SECRETS_PATH, address),
              'instances': list(map(lambda s: {'address': s}, instances))
            }
            for address, instances in mapping.items()
        ]
    })


def start_onionbalance(mapping):
    from subprocess import Popen

    with open(ONIONBALANCE_CONFIG, 'w') as fd:
        fd.write(onionbalance_config(mapping))
    return Popen(['onionbalance', '-c', ONIONBALANCE_CONFIG])


def kill(process):
    from subprocess import TimeoutExpired
    print('Sending SIGTERM to onionbalance')
    process.terminate()

    try:
        process.wait(timeout=5)
    except TimeoutExpired:
        print('Onionbalance failed to terminate within 5s')
        process.kill()
        process.wait(timeout=60)


if __name__ == '__main__':
    import itertools, os, sys
    from kubernetes import client, config, watch
    NAMESPACE = os.environ['POD_NAMESPACE']

    config.incluster_config.load_incluster_config()
    v1 = client.CoreV1Api()

    onionmap     = get_onion_mapping(v1, NAMESPACE)
    onionbalance = start_onionbalance(onionmap)

    stream = watch.Watch().stream(v1.list_namespaced_pod,
                                  NAMESPACE,
                                  label_selector=SERVICE_LABEL
    )

    for event in stream:
        newmap = get_onion_mapping(v1, NAMESPACE)
        if newmap == onionmap:
            continue

        sys.stderr.write('Updating onionbalance config:')
        for host in set(itertools.chain(newmap.keys(), onionmap.keys())):
            if host in newmap and host in onionmap and newmap[host] == onionmap[host]:
                continue

            sys.stderr.write('  %s\n' % host)

            sys.stderr.write('    Adding: %s\n' % (newmap[host] - onionmap[host]))
            sys.stderr.write('    Removing: %s\n' % (onionmap[host] - newmap[host]))
            sys.stderr.write('    Keeping: %s\n' % (onionmap[host] & newmap[host]))
            sys.stderr.flush()

        onionmap = newmap
        kill(onionbalance)
        onionbalance = start_onionbalance(onionmap)
