# Kubeportal

Kubeportal is a web application to get a single sign-on Kubernetes experience for cluster users:

  * Kubeportal manages a user database for the cluster.
  * Administrative users get an admin web UI for adding / deleting cluster users.
  * Kubeportal makes sure that users have according namespaces and service accounts in Kubernetes, by talking to the API server whenever the administrative user changes something.
  * Non-administrative users get a web UI for downloading their `kubectl` config file.
  * Kubeportal acts as OAuth2 authentication provider. This enables applications with OAuth2 login support, such as Grafana, to use it as authentication frontend.
  * Kubeportal acts as reverse proxy that adds Bearer tokens to HTTP requests. This enables applications with JWT login support, such as Kubernetes dashboard, to use it as authentication frontend.
  * Kubeportal can delegate password checking to a backend entity, such as a LDAP server.
  
The intended design outcomes are:

  * Cluster web login always looks the same.
  * Independent user administration is possible.
  * User administration does not mean to deal with YML files.

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

## Who needs that?

This project is intended to make the management of our own little cluster more comfortable.

Serious environments already have their single sign-on frontends, and don't need that. 

The Kubeportal functionality can also be achieved with a cascade of OAuth2 proxies, an LDAP server + UI and some stunts the get the API server changes being done.

## Are you re-inventing DEX?

Dex comes without a front-end for users and user management. It is mainly an authentication protocol converter.

