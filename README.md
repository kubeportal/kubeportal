# kubespider

Kubespider is a web application enabling a single-sign experience for Kubernetes clusters:

  * Admin can manage Kubernetes users in a nice web UI.
  * Users can download their kubectl config file in a nice web UI.
  * User passwords are checked against an authentication backend, such as LDAP.
  * The API server uses it as authentication provider.
  * OAuth web applications can also use it as authentication provider.

```
                                                     KUBESPIDER

                                        +---------------------------------+
                                        |                                 |
                                        +-----------------------+         |
                                        |                       |         |  authn
    +--> kubectl +----> API Server +--> | OICD AUTH PROVIDER    |         +--------->  LDAP
    |                                   |                       |         |
    +                                   +-----------------------+         |
                                        |                       |         |
  User +----------------> Web App +---> | OAUTH2 AUTH PROVIDER  |         +--------->  ...
                                        |                       |         |
    +                                   +-----------------------+         |
    |                                   |                       |         |
    +---------------------------------> | SELF SERVICE UI       |         |
                                        | (kubectl config file) |         |
                                        +-----------------------+         |
                                        |                       |         |
Admin +-------------------------------> | USER MANAGEMENT UI    |         |
                                        |                       |         |
                                        +-----------------------+         |
                                        |                                 |
                                        +---------------------------------+

```

