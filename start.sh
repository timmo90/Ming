rm -f *.pyc
sudo kill -9 `ps -aux | grep ming_uwsgi | awk '{ print $2 }'`
sudo ln -sf /var/www/ming/ming_uwsgi.conf /etc/nginx/conf.d/ming_uwsgi.conf
sudo mkdir -p /var/www/uwsgi-logs
sudo /etc/init.d/nginx restart
sudo chown mo:mo /var/www/ming
sudo uwsgi --py-autoreload 1 --ini /var/www/ming/ming_uwsgi.ini --daemonize /var/www/uwsgi-logs/ming_uwsgi.log
