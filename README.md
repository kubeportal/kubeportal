# Kubeportal

Kubeportal is a web application to get a single sign-on Kubernetes experience. It operates as synchronizing entity between a portal user base and Kubernetes service accounts resp. namespaces.

After portal login, users can download their `kubectl` config file directly from the web site. Their service accounts and namespaces are configured by administrative users in the backend. 

Kubeportal acts as OAuth2 and WebHook authentication provider. This enables other web applications to use it as authorization service.
  

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
|       |                     | |  WebHook Provider       |            +---------------> | LDAP,    |
|       |                     | |                         |            |                 | ...      |
|       |                     | +-------------------------+            |                 |          |
|       |                     |           ^                            |                 +----------+
|       |                     |           |                            |
|       |                     +----------------------------------------+
|       |                                 |           
|       |                        +--------+------+    
|       +----------------------> | K8S Dashboard | ...  
|       | Web Login              +---------------+
|       | (name, password)
+-------+                                  

```

## Who needs that?

This project is intended to make the management of little clusters more comfortable.

Serious environments typically have an existing single sign-on frontend, and shouldn't need that. 

The Kubeportal functionality can also be achieved with a cascade of OAuth2 proxies, an LDAP server with schema extension, an LDAP UI and some stunts the get the service accounts being created.

## Are you re-inventing DEX?

Dex comes without a front-end for users and user management. It is mainly an authentication protocol converter.

