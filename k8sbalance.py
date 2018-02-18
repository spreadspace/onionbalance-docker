#!/usr/bin/env python3

SERVICE_LABEL='spreadspace.org/onion-service'
INSTANCE_ANNOT='spreadspace.org/onion-instance'
REFRESH_INTERVAL=120
SECRETS_PATH='/var/run/secrets/spreadspace.org/onionbalance'
ONIONBALANCE_CONFIG='/tmp/onionbalance.yml'

def get_onion_mapping(client, NAMESPACE):
    l = client.list_namespaced_pod(NAMESPACE, label_selector=SERVICE_LABEL)
    m = {}

    for pod in l:
        service = pod.metadata.labels[SERVICE_LABEL]
        instance = pod.metadata.annotations[INSTANCE_ANNOT]

        if service not in m:
            m[service] = []

        m[service].append(instance)

    return m


def onionbalance_config(mapping):
    import json, os.path
    return json.dumps({
        'REFRESH_INTERVAL': REFRESH_INTERVAL,
        'services': [
            { 'key': os.path.join(SECRETS_PATH, address),
              'instances': map(lambda s: {'address': s}, instances) }
            for address, instances in mapping.items()
        ]
    })


def start_onionbalance(mapping):
    from subprocess import Popen, PIPE

    with open(ONIONBALANCE_CONFIG, 'w') as fd:
        fd.write(onionbalance_config(mapping))
    return Popen(['onionbalance', '-c', ONIONBALANCE_CONFIG],
                 stdout=PIPE, stderr=PIPE
    )


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
    import os
    from kubernetes import client, config, watch
    NAMESPACE = os.environ['POD_NAMESPACE']

    config.incluster_config.load_incluster_config()
    v1 = client.CoreV1Api()

    ob = start_onionbalance(get_onion_mapping(v1, NAMESPACE))

    stream = watch.Watch().stream(v1.list_namespaced_pod,
                                  NAMESPACE,
                                  label_selector=SERVICE_LABEL
    )

    for event in stream:
        kill(ob)
        ob = start_onionbalance(get_onion_mapping(v1, NAMESPACE))
