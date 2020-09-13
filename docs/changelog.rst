Changelog
#########

.. _v0.3.13:

v0.3.13 Release
===============

  * Fix sync with pre-existing namespaces of the same name in K8S
  * Fix sync with illegal namespace names after approval


.. _v0.3.12:

v0.3.12 Release
===============

  * Allow reverse member management in backend at different places (:issue:`61`)(:issue:`62`)
  * Fix bug with duplicate web apps being shown
  * "All users" and "Kubernetes users" are not automatically created and managed groups


.. _v0.3.8:

v0.3.8 Release
===============

  * Fix a problem with 'next=' parameter forwarding on OIDC login from web applications.
  * Fix some small glitches in the user administration backend.
  * The documentation now reflects the latest features (web apps, user groups, installation methods).


.. _v0.3.7:

v0.3.7 Release
===============

  * Fix a problem with existing users not seing the new portal group and web app admin pages.

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


