Data synchronization
####################

KubePortal synchronizes the current list of Kubernetes namespaces and service accounts with your Kubernetes API server instance.
It can create Kubernetes namespaces for new portal users, but will  **never** delete anything in your cluster, even if the linked portal user is deleted. 

You can trigger the sychronization manually on the backend landing page:

.. image:: static/kubeportal10.png

This is needed once after the installation, so that KubePortal gets the initial list of namespaces. It is also neccessary when
you create or modify namespaces directly in the cluster.
