# ADR 0004: Traefik as the Ingress controller (not ingress-nginx)

- Status: accepted
- Date: 2026-10-12

## Context

The course material and the reference projects use ingress-nginx. Upstream
retired the Kubernetes ingress-nginx project in March 2026: the repository
is archived, and it gets no further releases or security fixes. Starting a
new platform on an unmaintained edge component would contradict the "Sec"
in DevSecOps.

The candidates were:

- **Traefik:** actively maintained, implements standard `networking.k8s.io/v1`
  Ingress, single binary, official Helm chart.
- **Gateway API implementations:** the long-term direction, but a larger
  change than the capstone needs.
- **Cloud load balancer controllers:** cloud-specific, so they don't help
  the local kind cluster.

## Decision

Use Traefik v3 (Helm chart `traefik/traefik` 41.7.1, app v3.7.14) as the
`traefik` IngressClass, with only the Kubernetes Ingress provider enabled.
The application chart uses plain `Ingress` objects, so swapping the
controller later is a values change, not a rewrite.

| Environment | Values file | Exposure |
|-------------|-------------|----------|
| kind | [`k8s/addons/traefik-kind-values.yaml`](../../k8s/addons/traefik-kind-values.yaml) | hostPorts 80/443 on the node, mapped to host ports **8088/8443** |
| EKS | [`k8s/addons/traefik-eks-values.yaml`](../../k8s/addons/traefik-eks-values.yaml) | Service of type `LoadBalancer` (NLB) |

On Windows, host ports 80/443 are held by Docker Desktop, which is why kind
uses 8088/8443.

## Consequences and lessons from running it

These came up while running Traefik on the kind cluster:

1. **Values schema.** Chart 41.x validates its values. Top-level
   `logs`/`metrics` keys failed CI run 38282550447 ("additional properties
   'logs' not allowed"), so they were removed.
2. **Ingress status.** With a ClusterIP Service, Traefik published no
   address, and Argo CD reported every Ingress as `Progressing`. The fix
   was `providers.kubernetesIngress.ingressEndpoint.ip: 127.0.0.1`.
3. **hostPort rollouts.** The default rolling update (`maxSurge: 1`) put the
   new pod in `Pending` ("didn't have free ports"), because only one pod per
   node can hold a hostPort. The fix was `maxSurge: 0` and
   `maxUnavailable: 1`. Transcript:
   [incident 2](../evidence/transcripts/incident-2-traefik-hostport.txt).
