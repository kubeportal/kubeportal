# kubeportal

Kubeportal is a web application enabling a single-sign experience for Kubernetes clusters:

  * Admin can manage Kubernetes users in a nice web UI.
  * The neccessary namespaces, service accounts and role bindings in Kubernetes are accordingly managed.
  * Users can download their kubectl config file in a nice web UI.
  * User passwords are checked against an authentication backend, such as LDAP.
  * OAuth web applications can use it as authentication provider.
  * Bearer auth web application can use it as reverse proxy.

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
|       +------+-------->  +----+  OAuth Provider         |            |                      |
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
|       |                     | |                         |            |     LDAP        |          |
|       +--------------->  +----+  Auth Reverse Proxy     |            +---------------> | AuthN    |
|       | Web Login           | |                         |            |                 | Provider |
|       | (name, password)    | +---------+----------+--+-+            |                 |          |
|       |                     |           |          |  |              |                 +----------+
|       |                     |           |          |  |              |
|       |                     +----------------------------------------+
|       |                          Bearer |          |  |
|       |                        +--------v------+   v  v
|       |                        | K8S Dashboard |   ...
+-------+                        +---------------+

```

