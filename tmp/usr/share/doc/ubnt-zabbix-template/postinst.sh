#! /bin/bash
#

logfile="/var/log/ubnt-zabbix-template.log"
api_url="http://127.0.0.1/api_jsonrpc.php"
zbx_imp="python3 /usr/share/doc/ubnt-zabbix-template/import.py"
zbx_act="python3 /usr/share/doc/ubnt-zabbix-template/action.py"
api_cfg_import="$zbx_imp --url $api_url --user visor --password ping /usr/share/doc/ubnt-zabbix-template/"
api_act_import="$zbx_act --url $api_url --user visor --password ping"

echo "">$logfile

test=`ps ax | grep -F $0 | grep -v "grep -F $0" | wc -l`

if [ "$test" -gt "3" ]; then
    echo "we're already running" >>$logfile
    exit 0
fi

test=`ps ax | grep postgres | grep -v 'grep postgres'`

if [ -z "$test" ]; then
    echo "postgres is not running" >>$logfile
    exit 0
fi

test=`ps ax | grep nginx | grep -v 'grep nginx'`

if [ -z "$test" ]; then
    echo "nginx is not running" >>$logfile
    exit 0
fi

test=`ps ax | grep php-fpm | grep -v 'grep php-fpm'`

if [ -z "$test" ]; then
    echo "php-fpm is not running" >>$logfile
    exit 0
fi

echo "Stopping Zabbix..." >>$logfile

/etc/init.d/zabbix-server stop
/etc/init.d/zabbix-agent stop

echo "Stopped." >>$logfile

sudo -u postgres dropdb zabbix >>$logfile 2>&1
sudo -u postgres dropuser zabbix >>$logfile 2>&1
sudo -u postgres createuser -w zabbix >>$logfile 2>&1
sudo -u postgres createdb -O zabbix zabbix >>$logfile 2>&1

echo "ALTER USER zabbix WITH PASSWORD 'netping';" | sudo -u postgres psql zabbix >>$logfile 2>&1
cat /usr/share/doc/ubnt-zabbix-template/dump.sql.gz | gzip -dc | sudo -u postgres psql -d zabbix >>$logfile 2>&1

echo "Starting Zabbix..." >>$logfile

/etc/init.d/zabbix-agent start
/etc/init.d/zabbix-server start

echo "Started." >>$logfile

sensors-detect --auto >>$logfile 2>&1

${api_cfg_import}Zabbix_6.0-6.4.xml >>$logfile 2>&1
${api_cfg_import}export_zabbix_server.xml >>$logfile 2>&1
${api_cfg_import}zbx_export_internal_netping.xml >>$logfile 2>&1
cp /usr/share/doc/ubnt-zabbix-template/sendsms2.sh /usr/lib/zabbix/alertscripts/
cp /usr/share/doc/ubnt-zabbix-template/zabbix_agentd.conf /etc/zabbix/
${api_cfg_import}mediatype_sms_via_np.xml >>$logfile 2>&1
${api_act_import} >>$logfile 2>&1

sed -i '/\*\/2 \* \* \* \* \/usr\/share\/doc\/ubnt-zabbix-template\/postinst.sh/d' /var/spool/cron/crontabs/root >>$logfile 2>&1


exit 0
