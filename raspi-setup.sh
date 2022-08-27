echo "setup timezone"
dpkg-reconfigure tzdata

echo "setup packages"
apt update
apt upgrade
apt install apache2 php mysql-server php-mysql tcptraceroute bc expect dos2unix telnet php-cli libapache2-mod-php postfix mailutils gh

echo "setup www user"
useradd -m -d  /home/www -s /bin/bash www
mkdir ~www/bin
chown www:www ~www/bin
echo umask 022 >> ~www/.profile
