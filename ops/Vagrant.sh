#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

echo 'Updating the aptitude repository...'
apt-get -y update > /dev/null

packages=('python' 'python-pip' 'python-dev' 'libffi-dev' 'apache2' 'libapache2-mod-wsgi')

for package in "${packages[@]}"
do
    if dpkg --get-selections | grep -q "^$package[[:space:]]*install$" >/dev/null
    then
        echo "Skipping the installation of $package"
    else
        echo "Installing $package..."
        apt-get install -y $package > /dev/null
    fi
done

echo 'Checking the python version...'
if [ $(python -V 2>&1 | grep -c "2.7") -eq 0 ]
then
    >&2 echo 'Please ensure that python 2.7 is installed and is the default python version'
    exit 1
fi

echo 'Creating the /opt/adreset2/logs directory'
mkdir /opt/adreset2/logs
chown www-data:www-data /opt/adreset2/logs

if ! [ -d '/opt/adreset2/env' ]
then
    echo 'Installing the virtual environment...'
    pip install virtualenv > /dev/null
    virtualenv /opt/adreset2/env > /dev/null
    source /opt/adreset2/env/bin/activate
else
    >&2 echo '/opt/adreset2/env already exists. Please make sure it is removed before rerunning the script'
    exit 1
fi

cd /opt/adreset2/git
echo 'Installing the Python packages required in the virtualenv...'
pip install -r requirements.txt > /dev/null

echo 'Creating the database...'
python manage.py clean
python manage.py createdb
python manage.py generatekey

deactivate

if [ $(apachectl -M | grep -c 'wsgi_module') == 0 ]
then
    echo 'Enabling the wsgi module for Apache...'
    a2enmod -q wsgi > /dev/null
fi

if [ $(apachectl -S | grep -c "000-default.conf") != 0 ]
then
    echo 'Disabling 000-default.conf...'
    a2dissite 000-default.conf > /dev/null
fi

echo 'Copying and enabling the standard PostMaster Apache configuration...'
cp -f /opt/adreset2/git/ops/apache.conf /etc/apache2/sites-available/adreset2.conf
chmod 644 /etc/apache2/sites-available/adreset2.conf
a2ensite -q adreset2.conf > /dev/null

echo 'Restarting Apache...'
service apache2 restart > /dev/null

unset DEBIAN_FRONTEND

echo 'The installation has completed!'
