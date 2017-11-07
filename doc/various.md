# Appendix 

## Howto install Docker on Ubuntu 

[Docker](https://www.docker.com/) is a software container solution used
to provide operating-system-level virtualization.  It is possible for
all OpenMTC components to run within a Docker container.  To make
this possible, a script is provided to allow a user to build Docker
container images.

*Be aware that during the build process the build machine has to have
access to the Internet, since various Docker container image
dependencies are pulled.*

For a general introduction to Docker, see:
[Get Started with Docker](https://docs.docker.com/get-started/).
 
### Install and Prepare Docker

 For the build script to work, Docker needs to be installed.  There
 are two different approaches to installing Docker on your system.
 
   1. Use the OS package manager to install docker.io package
   2. Use installer from Docker.com to install freshest version of Docker
 
 Use the first method whenever your OS package manager provides a more
 recent of Docker.  If this not the case, *e.g. in Ubuntu 14.04*, use
 the second approach to install Docker.
 
#### Installing docker.io package in Ubuntu 16.04 or Debian testing via `apt`
 
 
```
# Install docker on Debian-like systems
sudo apt-get -y  install docker.io

# Prepare a user for non-root access to Docker

# If above installation did not create a 'docker' group, you may add
# it manually.  Afterwards, you need to restart Docker for that
sudo groupadd docker
sudo service docker restart

# Add a specific user to user group 'docker'
sudo usermod -aG docker USER_NAME

# Be sure to logoff and login that user, to make the group change to
# kick in

# Check if Docker runs properly, by using various docker commands, e.g.
docker images
docker ps

# Use the Docker build commands in the next section for further
# testing, if above commands were working properly.  If in the next
# section Docker does not work properly, see below description.

# If Docker does not work properly yet, try to restart it
sudo systemctl stop docker
sudo ip link set down docker0
sudo ip link set up docker0
sudo systemctl start docker

# Still, not?  Is routing configured correctly?  Maybe try:
sudo ip r add 172.17.0.0/16 dev docker0
```

#### Installing freshest Docker version via Docker.com installer

 *Use this particularly for Ubuntu 14.04.*
 
```
# Downloads an installation script and executes it
# Be aware that within the script `sudo` is called
curl -sSL https://get.docker.com | sh

# Prepare your user account to use docker command
#
# 1. Add the specified user to user group 'docker'
sudo usermod -aG docker USER_NAME

# 2. Logout and re-login to the system so that the user account changes
#    can "kick-in"
```
