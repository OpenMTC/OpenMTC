# Authentication Guide

## Enable Authentication using HTTPS at the backend CSE and gateway CSE

To enable authentication the following parameters need to be changed in the configuration files of the backend CSE and gateway CSE named `config-backend.json` and `config-gateway.json`.
The configuration files are located in the `openmtc-open-source/openmtc-gevent` directory.

In the `plugins` section of each configuration file the HTTPTransportPlugin needs to be enabled.
Therefore, make sure the `disabled` option of the plugin is set to **false**.
Set the option `enable_https` to **true** in the config of the HTTPTransportPlugin to enable HTTPS.
If the option `require_cert` is set to **true**, the client that requests the gateway must provide a certificate.


### Example of the gateway CSE configuration:
```json
"plugins": {
        "openmtc_cse": [
            {
                "name": "HTTPTransportPlugin",
                "package": "openmtc_cse.plugins.transport_gevent_http",
                "disabled": false,
                "config": {
                    "enable_https": true,
                    "interface": "::",
                    "port": 8000,
                    "require_cert": true
                }
            },
```

The necessary SSL parameters used for the HTTPS/SSL connection must be specified in the `ssl_certs` option in the `onem2m` section of the corresponding configuration file.
This option includes the private key (`key`), the certificate (`crt`) and the certificate chain (`ca`).
Pre-shipped keys, certificates and a chain file which can be used at the gateway CSE and the backend CSE are located in the `openmtc-open-source/openmtc-gevent/certs` directory.


### Example of the SSL parameters configured at the gateway CSE:
```json
"onem2m": {
        "accept_insecure_certs": false,
        "cse_base": "onem2m",
        "cse_id": "mn-cse-1",
        "cse_type": "MN-CSE",
        "overwrite_originator": {
            "enabled": false,
            "originator": "/openmtc.org/mn-cse-1"
        },
        "sp_id": "openmtc.org",
        "ssl_certs": {
            "ca": "certs/ca-chain.cert.pem",
            "crt": "certs/mn-cse-1-client-server.cert.pem",
            "key": "certs/mn-cse-1-client-server.key.pem"
        }
    },
```

## Registering the gateway CSE to the backend CSE using HTTPS

The RegistrationHandler plugin is responsible to register the gateway CSE to the backend CSE.
Therefore, the plugin needs to be enabled by setting the `disabled` option to **false**.
Furthermore, when HTTPS is enabled at both CSEs the options `poa` and `own_poa` needs to be changed to **https://...**  in the `config` section of the RegistrationHandler plugin.

```json
{
                "name": "RegistrationHandler",
                "package": "openmtc_cse.plugins.registration_handler",
                "disabled": false,
                "config": {
                    "interval": 3600,
                    "labels": [
                        "openmtc"
                    ],
                    "offset": 3600,
                    "remote_cses": [
                        {
                            "cse_base": "onem2m",
                            "cse_id": "in-cse-1",
                            "cse_type": "IN_CSE",
                            ,
                            "own_poa": [
                                "https://localhost:8000"
                            ],
                            "poa": [
                                "https://localhost:18000"
                            ]
                        }
                    ]
                }
            },
```

## Authentication of AEs/IPEs

When HTTPS is enabled in the configuration of the CSEs the AEs/IPEs must provide SSL information as well to perform requests to the CSEs.

Using the [OpenMTC application framework](./sdk-framework.md)
AEs and IPEs derive from the provided base class `openmtc_app.onem2m.XAE`.

When creating an instance of the AE/IPE the following additional SSL parameter can be specified:
* `ca_certs`: the certificate chain file
* `cert_file`: the certificate file
* `key_file`: the private key file
* `originator_pre`: the originator which needs to match the subjectAltName value in the certificate

If all SSL parameters are specified, the AE/IPE is started by the application framework using an HTTPS client.

### Example from the [onem2m-gui-sensors-actuators-final.py](/doc/training/apps/onem2m/ipe/sensors-actuators/onem2m-ipe-sensors-actuators-final.py) training IPE:

```python
host = 'https://localhost:8000'
    app = TestIPE(
        poas=['https://localhost:21346'],          # adds poas in order to receive notifications
        # SSL options
        originator_pre='//openmtc.org/mn-cse-1',  # originator_pre, needs to match value in cert
        ca_certs='../../openmtc-gevent/certs/ca-chain.cert.pem',
        cert_file='certs/test-ipe.cert.pem',      # cert file, pre-shipped and should match name
        key_file='certs/test-ipe.key.pem'
    )
```


## Request information using curl when HTTPS is enabled

In general requests are performed just the same as presented in the [REST API Guide](./overview-rest-api.md).
But, when HTTPS is enabled additional SSL options need to be provided by the client to the CSE.

When using curl as client add the following options:
* **--cert**: the client certificate
* **--key**: the private client key
* **--cacert**: the certificate chain
* **-H**: set Header Fields, used to set the *X-M2M-Origin* header mapped as `the originator`

### Example curl request

```shell
curl https://localhost:8000/onem2m -v --cert test-ae.cert.pem --key test-ae.key.pem --cacert ca-chain.cert.pem -H "X-M2M-Origin: //openmtc.org/mn-cse-1/CTest-AE"
```
### Notes

If the option `require_cert` in the HTTPTransportPlugin config is set to **false**, the client does not need to present a certificate.
Therefore, the curl option **--cert** and **--key** are not needed when sending a request to the CSE.


**Example:**

```shell
curl https://localhost:8000/onem2m -v --cacert ca-chain.cert.pem -H "X-M2M-Origin: //openmtc.org/mn-cse-1/CTest-AE"
```

curl performs SSL certificate verification by default, using a "bundle" of Certificate Authority (CA) public keys (CA certs).
Using the **--cacert** option the "bundle" file which is used for verification can by specified.
In the above example this option is used and the certificate presented by the server to the curl client is verified.
Nevertheless, curl's verification of the server certificate can be turned off, using the **-k (or --insecure)** option.


**Example:**

```shell
curl https://localhost:8000/onem2m -v -H "X-M2M-Origin: //openmtc.org/mn-cse-1/CTest-AE" --insecure
```
