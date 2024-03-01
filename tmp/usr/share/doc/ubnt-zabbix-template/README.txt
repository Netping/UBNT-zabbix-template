1. Шаблоны:

Импортировать Zabbix_5.0-5.2.xml 
API Импорт (применимо и далее): https://www.zabbix.com/documentation/current/ru/manual/api/reference/configuration/import

2. Мониторинг самого сервера + температура + внутренний нетпинг

2.1 
Установить пакеты:
jq
lm-sensors

2.2 
запустить sensors-detect для обнаружения датчиков на мат. плате. на все вопросы отвечаем yes

2.3
В файле /etc/zabbix/zabbix_agentd.conf
Редактируем: UnsafeUserParameters=1
Добавляем новое:
UserParameter=dkst90.mbTemperature,sensors -j | jq .\"it8786-isa-0a40\".\"temp1\".\"temp1_input\"
UserParameter=dkst90.cpuTemperature,sensors -j | jq .\"coretemp-isa-0000\".\"Core\ 0\".\"temp2_input\"

2.4
импортируем с заменой export_zabbix_server.xml
импортируем с заменой zbx_export_internal_netping.xml

2.5
После рестарта заббикса в разделе CPU будут итемы с температурой цпу и мат.платы

3. СМС уведомления:

3.1
копируем sendsms2.sh в /usr/lib/zabbix/alertscripts/

3.2
импортируем (MediaType) mediatype_sms_via_np.xml

3.3
Через API создаем (Configurtaion -> Actions, https://www.zabbix.com/documentation/current/ru/manual/api/reference/action/create)
Name: Report By SMS
Condition: 	Host equals Internal_NetPing
Enabled: True
Operations: Send message to user groups: Zabbix administrators via Send SMS (via Internal NetPing)	Immediately	Default

3.4
Через API редактируем пользователя Zabbix: (Administration -> Users, https://www.zabbix.com/documentation/current/ru/manual/api/reference/user/update)
Добавляем Media:
Type: Send SMS (via Internal NetPing)
Send To: +70000000000 (клиент отредактирует на свой)
When Active: 1-7,00:00-24:00 (default)
Use if severity: all checkboxes
Enabled: True



