# onionbalance-docker

This is a containerized wrapper around `onionbalance` that automatically
(re)configure it based on the state of the Kubernetes cluster it runs in.


## Usage

This can support any number of onion services, and any number of instances
supporting each service (within [`onionbalance`'s limits]). Instances' onion
addresses are detected based on the `spreadspace.org/onion-instance` annotation,
and are matched to the onion service address found in the
`spreadspace.org/onion-service` label.

The onion services' private keys are expected to be found in the
`spreadspace.org/onionbalance` Kubernetes secret.

I recommend using my [`onion-service-docker`] container to implement onion
instances; it makes **single-hop** onion services, automatically generates a
fresh instance key, and self-annotates.


[`onionbalance`'s limits]: https://onionbalance.readthedocs.io/en/latest/design.html#choice-of-introduction-points
[`onion-service-docker`]: https://github.com/spreadspace/onion-service-docker
