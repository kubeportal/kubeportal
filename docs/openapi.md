# Kubportal Backend API
## Version: v1.4.0

### /cluster/{slug}/

#### GET
##### Summary:

Get information about the cluster.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| slug | path |  | Yes | string |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | A single information value as JSON dictionary with one entry. The key is the slug name. |
| 401 |  |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /webapps/{id}/

#### GET
##### Summary:

Get details about a web application.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | The ID of the web application. | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Attributes of the web application. |
| 401 |  |
| 403 | The user is not in a group assigned to this application, or the link is configured to not being shown. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /

#### GET
##### Summary:

Get bootstrap information for talking to the API.

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Information for talking to the API. |

### /groups/{id}/

#### GET
##### Summary:

Get details about a user group.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | The ID of the user group. | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Attributes of the user group. |
| 401 |  |
| 403 | The user is not in this group. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /users/{id}/webapps/

#### GET
##### Summary:

Get web apps of this user.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | ID of the user | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Ok |
| 401 |  |
| 403 | The current user is not allowed to get information for the requested user ID. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /users/{id}/groups/

#### GET
##### Summary:

Get groups of this user.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | ID of the user | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Ok |
| 401 |  |
| 403 | The current user is not allowed to get information for the requested user ID. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /users/{id}/

#### GET
##### Summary:

Get details for this user.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | ID of the user to get | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Ok. |
| 401 |  |
| 403 | The current user is not allowed to get information for the requested user ID. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

#### PATCH
##### Summary:

Modify details for this user.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| id | path | ID of the user to change | Yes | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 204 | Update successful. |
| 401 |  |
| 403 | The current user is not allowed to patch information for the requested user ID. |
| 404 |  |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### /login/

#### POST
##### Summary:

Authorize an user with name and password

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Ok. Authorized |

### /login_google/

#### POST
##### Summary:

Authorize a Google user with OAuth credentials

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | OK. Authorized |
| 400 | Invalid credentials, login denied. |

### /logout/

#### GET
##### Summary:

Invalidate API login session.

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | OK |

##### Security

| Security Schema | Scopes |
| --- | --- |
| JWT | |

### Models


#### StatisticType

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| StatisticType | string |  |  |

#### LoginSuccess

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| id | integer |  | No |
| firstname | string |  | No |
| access_token | string |  | No |

#### BootstrapSuccess

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| csrf_token | string |  | No |
| portal_version | string |  | No |
| default_api_version | string |  | No |

#### User

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| firstname | string |  | No |
| name | string |  | No |
| username | string |  | No |
| primary_email | string |  | No |
| all_emails | [ string ] |  | No |
| admin | boolean |  | No |
| k8s_serviceaccount | string |  | No |
| k8s_namespace | string |  | No |
| k8s_token | string |  | No |

#### WebApp

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| link_name | string |  | No |
| link_url | string |  | No |

#### Group

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| name | string |  | No |