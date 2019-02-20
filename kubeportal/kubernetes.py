from kubernetes import client, config

from kubeportal.models import KubernetesNamespace


class StupidLogger:
    logs = []

    def info(self, msg):
        self.logs.append(msg)

    def error(self, msg):
        self.logs.append(msg)


logger = StupidLogger()


def sync_namespaces(v1):
    k8s_ns_list = v1.list_namespace()
    for k8s_ns in k8s_ns_list.items:
        k8s_name = k8s_ns.metadata.name
        k8s_uid = k8s_ns.metadata.uid
        portal_ns, created = KubernetesNamespace.objects.get_or_create(name=k8s_name, uid=k8s_uid)
        if created:
            logger.info("Created portal record for namespace '{0}'".format(k8s_name))
            portal_ns.save()
        else:
            logger.info("Found existing portal record for namespace '{0}'".format(k8s_name))


def sync():
    logger.info("Starting synchronization ...")
    logger.info("Loading Kubernetes client configuration ...")
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        sync_namespaces(v1)
    except Exception as e:
        logger.error("Exception: {0}".format(e))
    return logger.logs
