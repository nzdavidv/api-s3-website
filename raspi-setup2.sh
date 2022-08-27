systemctl enable mysql.service ;  systemctl start mysql.service
service cron start 
systemctl enable cron
chown www /var/www/html

echo "enter mysql root password"; read mpasswd
mysql_secure_installation <<EOF

y
${mpasswd}
${mpasswd}
y
y
y
y
EOF
