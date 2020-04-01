Changelog
#########




.. _v0.3.6:

v0.3.6 Release
===============

  * User groups and web applications were added as new concept, and replace the former direct OpenID connect handling. Check the documentation for details (:issue:`4`, :issue:`6`)
  * Backend permissions are now solely handled by group membership (:issue:`52`).
  * The Kubernetes namespace list in the backend now has some usage statistics, in order to find zombie namespaces  (:issue:`43`).
  * The Kubernetes namespace list in the backend now supports some bulk actions (:issue:`24`, :issue:`18`).
  * The welcome page is now mobile-friendly (:issue:`46`).
  * The test coverage was greatly extended (:issue:`34`).
  * Sub-authentication can now be separately enabled / disabled per web application. The overview pages were updated accordingly.
  * User names for active directory logins are now converted to lower case.

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


