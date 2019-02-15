# kubeportal

Kubeportal is a web application enabling a single-sign experience for Kubernetes clusters:

  * Admin can manage Kubernetes users and their namespaces / services accounts / role bindings in a nice web UI.
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
|       | Name / PW           | |                         |            |                      |
|       |                     | +-------------------------+            |                      |
|       |                     | |                         |            |                 +----v-----+
| Human |                     | |  User Frontend          |            |     Sync        |          |
|       +--------------->  +----+  (config file download) | +--------+ +---------------> |  API     |
|       | Name / PW           | |                         | |        | | (Namespaces,    |  Server  |
|       |                     | +-------------------------+ |User    | |  Svc Accounts,  |          |
|       |                     | |                         | |Database| |  Role Bindings) +----------+
|       +--------------->  +----+  Admin Backend          | |        | |
|       | Name / PW           | |                         | +--------+ |
|       |                     | +-------------------------+            |                 +----------+
|       |                     | |                         |            |     LDAP        |          |
|       +--------------->  +----+  Auth Reverse Proxy     |            +---------------> | AuthN    |
|       | Name / PW           | |                         |            |                 | Provider |
|       |                     | +---------+----------+--+-+            |                 |          |
|       |                     |           |          |  |              |                 +----------+
|       |                     |           |          |  |              |
|       |                     +----------------------------------------+
|       |                          Bearer |          |  |
|       |                        +--------v------+   v  v
|       |                        | K8S Dashboard |   ...
+-------+                        +---------------+

```

