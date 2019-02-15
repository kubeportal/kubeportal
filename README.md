# kubeportal

Kubeportal is a web application for getting a single sign-on Kubernetes experience for end users:

  * Kubeportal manages a user database for the cluster.
  * Administrative users get an admin web UI for adding / deleting cluster users.
  * Kubeportal makes sure that users have according namespaces and service accounts in Kubernetes, by talking to the API server whenever the administrative users changes something.
  * Non-administrative users get a web UI for downloading their `kubectl` config file.
  * Kubeportal acts as OAuth2 authentication provider. This enables applications with OAuth2 login support, such as Grafana, to use it as authentication frontend.
  * Kubeportal acts as reverse proxy that adds Bearer tokens to HTTP requests. This enables applications with JWT login support, such as Kubernetes dashboard, to use it as authentication frontend.
  * Kubeportal can delegate password checking to a backend entity, such as a LDAP server.
  
The intended outcome is that the cluster web login always looks the same, and that user administration no longer means to deal with YML files.  

```
+-------+
|       +-------------------------------------------------------------------------------------+
|       | kubectl (config file)                                                               |
|       |                                                                                     |
|       |                        +---------+                                                  |
|       |      +---------------> | Grafana | ...                                              |
|       |      |                 +---------+                                                  |
|       |      |                                                                              |
|       |      |              +--------------- KUBEPORTAL -------------+                      |
|       |      |              |                                        |                      |
|       |      |              | +-------------------------+            |                      |
|       |      |              | |                         |            |                      |
|       +------+-------->  +----+  OAuth2 Provider        |            |                      |
|       | Web Login           | |                         |            |                      |
|       | (name, password)    | +-------------------------+            |                      |
|       |                     | |                         |            |                 +----v-----+
| Human |                     | |  User Frontend          |            |     Sync        |          |
|       +--------------->  +----+  (config file download) | +--------+ +---------------> |  API     |
|       | Web Login           | |                         | |        | | (Namespaces,    |  Server  |
|       | (name, password)    | +-------------------------+ |User    | |  Svc Accounts,  |          |
|       |                     | |                         | |Database| |  Role Bindings) +----------+
|       +--------------->  +----+  Admin Backend          | |        | |
|       | Web Login           | |                         | +--------+ |
|       | (name, password)    | +-------------------------+            |                 +----------+
|       |                     | |                         |            |     AuthN       |          |
|       +--------------->  +----+  Auth Reverse Proxy     |            +---------------> | LDAP,    |
|       | Web Login           | |                         |            |                 | ...      |
|       | (name, password)    | +---------+----------+--+-+            |                 |          |
|       |                     |           |          |  |              |                 +----------+
|       |                     |           |          |  |              |
|       |                     +----------------------------------------+
|       |                          Bearer |          |  |
|       |                        +--------v------+   v  v
|       |                        | K8S Dashboard |   ...
+-------+                        +---------------+

```

