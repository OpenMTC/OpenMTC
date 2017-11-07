# Gateway and backend configuration

## global

```json
"global": {
    "additional_host_names": [],
    "default_content_type": "application/json",
    "default_lifetime": 3600,
    "disable_forwarding": false,
    "require_auth": false
}
```

| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| additional_host_names | Mandatory | List | [] | | A list of additional hostnames (or <hostname:port\> pairs) to consider as "local" to the system. Useful when dealing with NAT. | NOT USED in OOS |
| default_content_type | Mandatory | String | *application/json* | <ul><li> *application/json*</li><li> *application/vnd.onem2m-res+json*</li><li>*application/vnd.onem2m-ntfy+json*</li><li>*application/vnd.onem2m-attrs+json*</li><li>*text/plain*</li></ul> | The default content type of the response. | VALUE NOT CHECKED; NOT REALLY USED/Overwritten |
| default_lifetime | Optional | Number | 3600 | | The default lifetime for resources in seconds. |
| disable_forwarding | ? | ? | ? | ? | ? | NOT USED in OOS |
| require_auth | ? | Boolean | true | |Reject any request that is lacking authentication information. | NOT USED in OOS |

## database

```json
"database": {
    "driver": "openmtc_server.db.nodb2.NoDB2",
    "dropDB": true
}
```
| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| driver | Mandatory | String | openmtc_server.db.nodb2.NoDB2 | openmtc_server.db.nodb2.NoDB2 | The appropriate gevent db adapter to use. | |
| dropB | Optional | Boolean | true | true/false | Initially deletes the database. | NO EFFECT in OOS when only using NoDB2 data base adapter |

## logging

```json
"logging": {
    "file": "/var/log/openmtc/gateway.log",
    "level": "DEBUG"
}
```
| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| file | Optional | String | null | <ul><li>null</li><li>path to file</li></ul> | The path to a file in order to write logging also to this file. The parent directory path must already exist and be writeable. If not specified or set to *null* file logging is not used. | |
| level | Optional | String | WARN | <ul><li>ERROR</li><li>WARN</li><li>INFO</li><li>DEBUG</li></ul> | The level that is used for logging. If not specified, the default log level (WARN) is used. <br>Verbose logging can be enabled when executing the *run-gateway* or *run-backend* start scripts using the **-v** option. This option can be used multiple times to enable the following log level: <ul><li>-v : INFO</li><li>-vv : DEBUG</li></ul> |  |

## onem2m

```json
"onem2m": {
    "accept_insecure_certs": false,
    "cse_base": "onem2m",
    "cse_id": "mn-cse-1",
    "cse_type": "MN_CSE",
    "overwrite_originator": {
        "enabled": false,
        "originator": "/openmtc.org/mn-cse-1"
    },
    "sp_id": "openmtc.org",
    "ssl_certs": {
        "ca": "certs/ca-chain.cert.pem",
        "crt": "certs/mn-cse-1-client-server.cert.pem",
        "key": "certs/mn-cse-1-client-server.key.pem",
    }
}
```

| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| accept_insecure_certs | Optional | Boolean | not set (should be false) | true/false |  When set to *true* the HTTP client of the CSE will not verify if the hostname of a remote CSE/server matches any of the entries in the subjectAltName or commonName of the certificate. | TODO: DEFAULT VALUE; if missing in config => geventhttpclient connectionpool: "if not self.insecure (None)" will every time check if match of hostname and peercert info |
| cse_base | Optional | String | onem2m | | The name of the *\<CSEBase\>* resource. | |
| cse_id | Optional | String | mn-cse-1 | | The unique identifier of the CSE. | |
| cse_type | Optional | String | MN-CSE | <ul><li>IN_CSE</li><li>MN_CSE</li><li>AEN_CSE</li></ul>  | The type of the CSE. | |
| overwrite_originator | Optional | | | | Enables to overwrite the originator information of the CSE. Instead of using the *sp_id* and *cse_id* which is set in the *onem2m* section of the config, the originator specified by *overwrite_originator.originator* is used. May be applied, when using certificates to match the originator of the CSE and the originator included in the certificate using the subjectAltName. | |
| overwrite_originator.enabled | Optional | Boolean | false | true/false | Enables overwriting of the originator, if set to *true*. | |
| overwrite_originator.originator | Optional | String | "" (empty string) | | The originator which is used by the CSE when sending requests. | |
| sp_id | Optional | String | openmtc.org | | The unique identifier of the M2M Service Provider. | |
| ssl_certs | ? | | | |  When using SSL this section provides the private key, certificate and certificate chain. | |
| ssl_certs.ca | ? | String | | | The path of the certificate chain file. | TODO: fix when missing |
| ssl_certs.crt | ? | String | | | The path of the certificate file. | TODO: fix when missing |
| ssl_certs.key | ? | String | | | The path of the key file. | TODO: fix when missing |
| | | | | | | |


## plugins.openmtc_cse

Plugins are what enriches the core component of OpenMTC with functionality.
The ``plugins`` section of the configuration file consists of a list (``[...]``) of plugin entries.
Each plugin entry is a JSON Object (``{...}``) which consists of the following common parameters:

| Name | Mandatory/Optional | Type | Default | Description |
| :------- | :------------------------: | :----: | :-------- | :-------------- |
| name | Mandatory | String | | The name of the class  providing the plugin's functionality. |
| package | Mandatory | String | | The fully qualified name of the Python  where the plugin implementation resides. |
| disabled | Optional | Boolean | true | Set this to true to prevent a plugin from being loaded in the first place. Useful to disable a plugin without removing its configuration altogether. |
| config | Optional | Object | {} | The plugin specific configuration. Please see the documentation of individual plugins for details. |

### AnnouncementHandler

TODO: Description

```json
{
    "name": "AnnouncementHandler",
    "package": "openmtc_cse.plugins.announcement_handler",
    "disabled": true,
        "config": {
            "auto_announce": false
        }
}
```

| Name | Mandatory/Optional | Type | Default | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :------------- | :--------|
| config.auto_announce | Optional | Boolean | true | ? | NOT USED (part of commented-out code) |


### ExpirationTimeHandler

TODO: Description

```json
{
    "name": "ExpirationTimeHandler",
    "package": "openmtc_cse.plugins.expiration_time_handler",
    "disabled": true,
    "config": {
        "default_lifetime": 10000
    }
}
```

| Name | Mandatory/Optional | Type | Default  | Description |
| :------- | :------------------------: | :----: | :-------- | :-------------- |
| config.default_lifetime | Optional | Number | 86400 | The default lifetime of resources in seconds. |


### HistoricalData

TODO: Description

```json
{
    "name": "HistoricalData",
    "package": "openmtc_cse.plugins.historical_data_handler",
    "disabled": true
}
```


### HTTPTransportPlugin

The plugin enables HTTP/HTTPS connections of the CSE.

```json
{
    "name": "HTTPTransportPlugin",
    "package": "openmtc_cse.plugins.transport_gevent_http",
    "disabled": false,
    "config": {
        "enable_https": false,
        "interface": "::",
        "port": 8000,
        "require_cert": true
    }
}
```

| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| config.enable_https | Optional | Boolean | false | true/false | Enables secure HTTPS connections using the ssl certificate information provided in the *onem2m * section of the configuration file in the *ssl_certs* object. Only when *ca*, *crt* and *key* are given HTTPS is enabled.  | |
| config.interface | Optional | String | "" | | The HTTP/HTTPS server address. | |
| config.port | Optional | Number | 8000 | | The HTTP/HTTPS port. | |
| config.require_cert | | Boolean | true | true/false | If set to true, the client must provide a certificate. | |

### NotificationHandler

Entities of the onem2m system can subscribe to resources. The NotificationHandler plugin sends notifications to the notificationURI attribute of the subscription whenever the subscribed resource is changed (created, updated, deleted).

```json
{
    "name": "NotificationHandler",
    "package": "openmtc_cse.plugins.notification_handler",
    "disabled": false
}
```


### RegistrationHandler

The RegistrationHandler plugin registers a CSE with another CSEs.
Therefore, a remote CSE resource which contains information about the gateway CSE is created at the backend CSE.
Furthermore, a remote CSE resource which contains information about the backend CSE is created at gateway CSE.

```json
{
    "name": "RegistrationHandler",
    "package": "openmtc_cse.plugins.registration_handler",
    "disabled": false,
    "config": {
        "labels": [
            "openmtc"
        ],
        "remote_cses": [
            {
                "cse_base": "onem2m",
                "cse_id": "in-cse-1",
                "cse_type": "IN_CSE",
                "own_poa": [
                    "http://localhost:8000"
                ],
                "poa": [
                    "http://localhost:18000"
                ],
            }
        ],
        "interval": 3600,
        "offset": 3600
    }
}
```

| Name | Mandatory/Optional | Type | Default | Supported Values | Description | NOTE |
| :------- | :------------------------: | :----: | :-------- | :--------------------- | :------------- | :--------|
| config.labels | Optional | List | [] | | A list including the labels which are set in the remote CSE resource at the backend CSE. | |
| config.remote_cses.cse_base | Optional, see NOTE | String | onem2m | | The name of the *\<CSEBase\>* resource of the backend CSE. | When missing: WARNING:RegistrationHandler:Could not register: |
| config.remote_cses.cse_id | Mandatory | String | | | The CSE-ID of the backend CSE. | |
| config.remote_cses.cse_type | Mandatory | String |  | IN_CSE ??? | | |
| config.remote_cses.own_poa | Optional, see NOTE | List | | | A list including the points of access of the gateway CSE which is set in the remote CSE resource at the backend.  | When missing: WARNING:RegistrationHandler:Could not register: |
| config.remote_cses.poa | Optional, see NOTE | List | | | A list including the points of access of the backend CSE. | When missing: WARNING:RegistrationHandler:Could not register: |
| interval | Optional | Number | 3600 or 5 | | The expirationTime update interval. | DUPLICATED DEFAULT VALUES in Code |
| offset | Optional | Number | 3600 or 10 | | An offset added to the expirationTime to ensure it can be met early. | DUPLICATED DEFAULT VALUES in Code |
