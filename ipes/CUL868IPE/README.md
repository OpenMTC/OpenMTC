# Prerequisite

## Hardware

* OpenMTC Gateway: Raspberry Pi 3 incl. SD with Raspbian (Jessi) and Power Plug 
* OpenMTC Backend: Raspberry Pi 3 incl. SD with Raspbian (Jessi) and Power Plug 
* USB-Stick: [Busware CUL v3](http://busware.de/tiki-index.php?page=CUL) 
* FS-20 sensor 
* FS-20 Actuator: Power Plug

## Software

Both Raspberry Pis need [Docker](https://www.docker.com/) to be installed.

```
curl -sSL https://get.docker.com | sh
```

```
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker <YOUR USERNAME>
```

After that reboot your Raspberry Pi and check the following command:

```
docker ps
```

If an emtpy table is returned the installion was succesfull.

After that check if the following tools are installed:

```
sudo apt install git jq
```

# Raspberry Pi 1: Setup the OpenMTC Backend

Clone the OpenMTC Repo to your Raspberry Pi and change to that directory.

```
git clone HIER MUSS DAS REPO STEHEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
cd REPO NAME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Create the Docker image for the OpenMTC backend:

```
./create-binary-docker -a arm backend
```

Start the Docker container:

```
docker run --name backend --rm -it -p 0.0.0.0:18000:18000 -e "ONEM2M_HTTP_TRANSPORT_PORT=18000" -e "ONEM2M_NOTIFICATION_DISABLED=false" openmtc/backend-arm -v
```

This should give you an output similiar to this:

```
INFO:HTTPTransportPlugin:Starting plugin HTTPTransportPlugin
INFO:GEventServerRack:WSGIServer started on ('::', 18000, 0, 0)
INFO:NotificationHandler:Starting plugin NotificationHandler
INFO:openmtc_gevent.main:OpenMTC is running
```

# Raspberry Pi 2: Setup the OpenMTC Gateway/IPE

Clone the OpenMTC Repo to your Raspberry Pi and change to that directory.

```sh
git clone HIER MUSS DAS REPO STEHEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
cd REPO NAME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Create the Docker image for the OpenMTC gateway and IPE:

```
./create-binary-docker -a arm gateway
./create-binary-docker -a arm cul868ipe 
```

Start the Docker  gateway container:

```
docker run --name gateway --rm -it -p 0.0.0.0:8000:8000\ 
  -e "ONEM2M_HTTP_TRANSPORT_PORT=8000"\ 
  -e "ONEM2M_NOTIFICATION_DISABLED=false"\
  -e "ONEM2M_REGISTRATION_DISABLED=false"\ 
  -e "ONEM2M_REMOTE_CSE_POA=http://<Backend_IP>:18000"\
  -e "EXTERNAL_IP=<Gateway_IP>"\
   openmtc/gateway-arm -v
```

This should give you an output similiar to this:

```
NFO:GEventServerRack:WSGIServer started on ('::', 8000, 0, 0)
INFO:NotificationHandler:Starting plugin NotificationHandler
INFO:RegistrationHandler:Starting plugin RegistrationHandler
INFO:RegistrationHandler:registering /mn-cse-1 at /in-cse-1
INFO:RemoteCSEController:Created resource of type 'remoteCSE' at onem2m/in-cse-1
INFO:openmtc_gevent.main:Gateway is running
```

On your Raspberry Pi running the backend you should se something like this:

```
INFO:RemoteCSEController:Created resource of type 'remoteCSE' at onem2m/mn-cse-1
::ffff:10.147.66.103 - - [2016-06-16 13:29:28] "POST /~/in-cse-1/onem2m HTTP/1.1" 201 431 0.036645
::ffff:10.147.66.103 - - [2016-06-16 13:29:28] "GET /~/in-cse-1/onem2m HTTP/1.1" 200 503 0.007546 
```

Now you should read this [site](http://busware.de/tiki-index.php?page=CUL) to
configure your RF USB-Stick: Busware CUL v3.

After that attach the stick to your Raspberry Pi. In order to get its device
name you should run:

```sh
dmesg | grep "tty"
```

This should give you an output like this:

```
[    1.810324] 3f201000.uart: ttyAMA0 at MMIO 0x3f201000 (irq = 87, base_baud = 0) is a PL011 rev2
[    5.931064] cdc_acm 1-1.4:1.0: ttyACM0: USB ACM device
```

In this example "ttyACM0" would be the device name.

``` sh
docker run --name cul868ipe --link gateway --rm -it \
  -e "EP=http://<Gateway_IP>:8000" \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  openmtc/culgip-arm -v
```

The output should show something similiar to:

```
Configuring M2M cul868gip...done
DEBUG:__main__:Trying config file location: /config.json
DEBUG:__main__:Trying config file location: /etc/openmtc/cul868gip/config.json
INFO:__main__:Reading configuration file /etc/openmtc/cul868gip/config.json.
INFO:CUL868Gip:Registering application as CUL868Gip.
INFO:CUL868Gip:Registration successful: onem2m/CUL868Gip.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/S300TH_1.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/S300TH_1/Temperature.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/S300TH_1/Humidity.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/S300TH_1/NGSI.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/FS20_ST3_16108_1.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/FS20_ST3_16108_1/Switch.
INFO:CUL868Gip:Container created: onem2m/CUL868Gip/FS20_ST3_16108_1/State.
```

The IWP (AE) is registering itself at the gateway. Output of gateway console:

```
INFO:AEController:Created resource of type 'AE' at onem2m/CUL868Gip
::ffff:172.17.0.3 - - [2016-06-16 13:55:57] "POST /onem2m HTTP/1.1" 201 447 0.011879
::ffff:172.17.0.3 - - [2016-06-16 13:55:57] "GET /onem2m/CUL868Gip HTTP/1.1" 200 442 0.003415
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868Gip/S300TH_1
::ffff:172.17.0.3 - - [2016-06-16 13:55:57] "POST /onem2m/CUL868Gip HTTP/1.1" 201 437 0.043352
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868Gip/S300TH_1/Temperature
::ffff:172.17.0.3 - - [2016-06-16 13:55:57] "POST /onem2m/CUL868Gip/S300TH_1 HTTP/1.1" 201 467 0.038131
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868Gip/S300TH_1/Humidity
::ffff:172.17.0.3 - - [2016-06-16 13:55:57] "POST /onem2m/CUL868Gip/S300TH_1 HTTP/1.1" 201 461 0.040906
...
```

# Retrieve Sensor Data

Example:

```
curl http://<GATEWAY_IP>:8000/onem2m/CUL868IPE/S300TH_1/Temperature/latest -s | jq -r '."m2m:cin".con' | base64 -d | jq -r . 
```

# Configure Actuator

Press and hold the button on the power plug until the light is flashing. Send the following command from the terminal session of the gateway to configure the power plug. Device code and house code is already preconfigured in the IPE. The power plug is adopting the config while receiving the command.

```sh
curl -H content-type:application/json -d '{"m2m:cin":{"con":"OFF", "cnf":"text/plain:0"}}' http://<GATEWAY_IP>:8000/onem2m/CUL868IPE/FS20_ST3_16108_1/Switch
```

The flashing light off the power plug should stop. Afterwards the power plug is
ready to use. Send commands to control the power plug:

**ON**
```sh
curl -H content-type:application/json -d '{"m2m:cin":{"con":"ON", "cnf":"text/plain:0"}}' http://<GATEWAY_IP>:8000/onem2m/CUL868IPE/FS20_ST3_16108_1/Switch
```

**OFF**
```sh
curl -H content-type:application/json -d '{"m2m:cin":{"con":"OFF", "cnf":"text/plain:0"}}' http://<GATEWAY_IP>:8000/onem2m/CUL868IPE/FS20_ST3_16108_1/Switch
```

**TOGGLE**
```sh
curl -H content-type:application/json -d '{"m2m:cin":{"con":"TOGGLE", "cnf":"text/plain:0"}}' http://<GATEWAY_IP>:8000/onem2m/CUL868IPE/FS20_ST3_16108_1/Switch
```

# Simulation mode

If you do not have any FS20 devices and ready but you want to check if the
OpenMTC Setup is working you are able to run the IPE docker container with a
simulation mode.

``` 
docker run --name cul868ipe --link gateway --rm -it \
  -e "EP=http://<Gateway_IP>:8000" \
  -e "SIM=true" \
  openmtc/culgip-arm -v
```

After that you should see something like this:

**IPE**
```
INFO:CUL868IPE:Registering application as CUL868IPE.
INFO:CUL868IPE:Registration successful: onem2m/CUL868IPE.
INFO:CUL868IPE:Container created: onem2m/CUL868IPE/FS20_ST3_16108_1.
INFO:CUL868IPE:Container created: onem2m/CUL868IPE/FS20_ST3_16108_1/Switch.
INFO:CUL868IPE:Container created: onem2m/CUL868IPE/FS20_sender_21111111-1321.
INFO:CUL868IPE:Container created:
onem2m/CUL868IPE/FS20_sender_21111111-1321/Command.
```

**Gateway**

```
NFO:AEController:Created resource of type 'AE' at onem2m/CUL868IPE
::ffff:172.17.0.4 - - [2017-09-13 15:32:05] "POST /onem2m HTTP/1.1" 201 524 0.011283
::ffff:172.17.0.4 - - [2017-09-13 15:32:05] "GET /onem2m/CUL868IPE HTTP/1.1" 200 519 0.004515
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_ST3_16108_1
::ffff:172.17.0.4 - - [2017-09-13 15:32:05] "POST /onem2m/CUL868IPE HTTP/1.1" 201 583 0.050967
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_ST3_16108_1/Switch
::ffff:172.17.0.4 - - [2017-09-13 15:32:05] "POST /onem2m/CUL868IPE/FS20_ST3_16108_1 HTTP/1.1" 201 553 0.052137
::ffff:172.17.0.4 - - [2017-09-13 15:32:06] "GET /onem2m/CUL868IPE/FS20_ST3_16108_1/Switch HTTP/1.1" 200 548 0.006070
INFO:SubscriptionController:Created resource of type 'subscription' at onem2m/CUL868IPE/FS20_ST3_16108_1/Switch/subscription-pFoSGnSNxZNXCWnW
::ffff:172.17.0.4 - - [2017-09-13 15:32:06] "POST /onem2m/CUL868IPE/FS20_ST3_16108_1/Switch HTTP/1.1" 201 509 0.055830
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_sender_21111111-1321
::ffff:172.17.0.4 - - [2017-09-13 15:32:06] "POST /onem2m/CUL868IPE HTTP/1.1" 201 577 0.053110
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_sender_21111111-1321/Command
::ffff:172.17.0.4 - - [2017-09-13 15:32:06] "POST /onem2m/CUL868IPE/FS20_sender_21111111-1321 HTTP/1.1" 201 551 0.052217
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_sender_21111111-1322
::ffff:172.17.0.4 - - [2017-09-13 15:33:46] "POST /onem2m/CUL868IPE HTTP/1.1" 201 577 0.062213
WARNING:ContainerController:expirationTime is too low. Adjusting
INFO:ContainerController:Created resource of type 'container' at onem2m/CUL868IPE/FS20_sender_21111111-1322/Command
::ffff:172.17.0.4 - - [2017-09-13 15:33:46] "POST /onem2m/CUL868IPE/FS20_sender_21111111-1322 HTTP/1.1" 201 551 0.062236
```

# Additional Informations

More information can be found on the [official webpage](http://www.openmtc.org/dev_center.html).
