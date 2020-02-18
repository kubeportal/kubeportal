.. _api:

API
###

KubePortal provides an API for fetching information stored in the portal database.

The access token is printed in the Docker logs on startup. For clients to authenticate, the token key should be included in the Authorization HTTP header. The key should be prefixed by the string literal "Token", with whitespace separating the two strings. For example:

  ``Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b``

The API allows you to fetch the following information:

  * List of approved cluster users: `https://<your installation>/api/users/` (GET)

