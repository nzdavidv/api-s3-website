systemctl enable mysql.service ;  systemctl start mysql.service
service cron start 
systemctl enable cron
chown www /var/www/html

mysql_secure_installation <<EOF

y
secret
secret
y
y
y
y
EOF