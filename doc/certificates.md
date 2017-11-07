# Certificate Issuance Guide

## How to create certificates?

TODO: some extra documentation when issuance is changed


### OpenSSL commands to create certificates

1. Create a Private Key

    ```shell
    $ openssl ecparam -genkey -name prime256v1 -out intermediate/private/server.key.pem
    ```

2. Create a Certificate Signing Request

    The private key is used to create a certificate signing request (CSR).

    ```shell
    $ openssl req -new -SHA256 -nodes -config intermediate/openssl_intermediate.cnf -key intermediate/private/server.key.pem -out intermediate/csr/server.csr.pem
    ```

3. Create a Certificate

    The Certificate Authority (CA) (in this case the intermediate CA) is used to sign the CSR and create a certificate.

    ```shell
    openssl ca -config intermediate/openssl_intermediate.cnf -extensions server_cert -days 365 -notext -md sha256 -in intermediate/csr/server.csr.pem -out intermediate/certs/server.cert.pem
    ```


## How to setup the certificates when using Docker?

TODO: NC
