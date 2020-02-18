Changelog
#########

.. _v0.2.7:

v0.2.7 Release
===============

  * Fix broken auth providers
  * Allow override of auto-detected API server, because generated config file needs
    the world-visible IP address in production.

.. _v0.2.5:

v0.2.5 Release
===============

  * Fix backend admin optics, allow change of approving person (:issue:`23`)

.. _v0.2.4:

v0.2.4 Release
===============

  * Fixen broken dependencies

.. _v0.2.2:

v0.2.2 Release
===============

  * Database migrations squashed, outdated dependencies removed - attempt to fix :issue:`12`
  * Show approving person in backend overview list

.. _v0.2.1:

v0.2.1 Release
===============

  * API access for the portal user list (see :ref:`api`)
  * Support for storing comments about particular users in the backend (:issue:`20`)
  * Support for fine-grained log level configuration (:issue:`37`)
  * eMail address is shown in user backend (:issue:`21`)
  * Kubernetes API server is now automatically detected
  * Portal shows some generic statistics about the cluster
  * Generic support for OIDC login (thanks to :user:`cultcom`)


