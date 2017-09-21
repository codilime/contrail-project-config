export DIB_RELEASE=7.1.1503
export DIB_LOCAL_IMAGE=/home/cloud-user/CentOS-7-x86_64-GenericCloud-1503.qcow2
export DIB_DISTRIBUTION_MIRROR=http://vault.centos.org
export DISTRO=centos7
export ELEMENTS_PATH=elements/

source /opt/dib/bin/activate
bash -x build-image.sh
