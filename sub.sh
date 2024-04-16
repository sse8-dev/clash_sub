#!/bin/bash

wget -T 10 -O /run/geolite.mmdb https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb
exit_status=$?
if [ $exit_status -eq 0 ]; then
    echo "下载成功"

    sha1_file1=$(sha1sum /run/geolite.mmdb | awk '{print $1}')
    sha1_file2=$(sha1sum /root/jcvpsip/GeoLite2-Country.mmdb | awk '{print $1}')

    if [ "$sha1_file1" == "$sha1_file2" ]; then
        echo -e "SHA checksums match with geolite file.\nnothing will do..."
        echo " `date` :geoip file not changed..." >> /run/log.txt
        rm /run/geolite.mmdb
    else
        echo "SHA checksums do not match with geolite file."
        echo " `date` :Updating geoip file...">>/run/log.txt
        mv /run/geolite.mmdb /root/jcvpsip/GeoLite2-Country.mmdb
    fi
else
    echo "下载geoip文件失败，请检查原因"
    echo " `date` :geoip file not downloaded..." >> /run/log.txt
fi

#机场订阅连接
JC_URL="https://----------"
wget -T 10 -O /run/bigdata.txt $JC_URL
exit_status=$?
if [ $exit_status -eq 0 ]; then
    echo "下载成功"

    sha1_file1=$(sha1sum /run/bigdata.txt | awk '{print $1}')
    sha1_file2=$(sha1sum /var/www/bigdata/bigdata.txt | awk '{print $1}')

    if [ "$sha1_file1" == "$sha1_file2" ]; then
        echo -e "SHA checksums match with bigdata subcrible.\nnothing will do..."
        echo " `date` :airport file not changed..." >> /run/log.txt
        rm /run/bigdata.txt
    else
        echo -e "SHA checksums do not match with bigdata subcrible.\nupdating config.json"
        mv /run/bigdata.txt /var/www/bigdata/bigdata.txt
        echo " `date` :Updating big_airport new subcrible...">>/run/log.txt
        (cd /root/jcvpsip/; python3 jcvpsip.py)
        (cd /root/sing-box-subscribe; ./python3/bin/python3 main.py  --template_index=0)
        scp /root/sing-box-subscribe/config.json root@192.168.1.216:/root/singbox/
        ssh root@192.168.1.216 "modprobe tun"
        ssh root@192.168.1.216 "killall singbox"
        ssh root@192.168.1.216 "service singbox restart"
        ping -c1 -W3 192.168.5.55
        exit_status=$?
        if [ $exit_status -eq 0 ]; then
            (cd /root/convert2clash/; ./python3/bin/python clash_sub.py; scp out.yaml root@192.168.5.55:/etc/ShellCrash/yamls/config.yaml)
            ssh root@192.168.5.55 "systemctl restart shellcrash"
        fi
    fi
else
    echo "下载机场文件失败，请检查原因"
    echo " `date` :airport file not downloaded..." >> /run/log.txt
fi
