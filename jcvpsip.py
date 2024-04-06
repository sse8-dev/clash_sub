#!/bin/python3

import base64
import json
import os
import time
import syslog
import requests
import socket
import geoip2.database

def find_country(target_ip):
# 指定 MaxMind 数据库文件路径
    reader = geoip2.database.Reader('/root/jcvpsip/GeoLite2-Country.mmdb')

# 查询 IP 地址所属国家
    try:
        response = reader.country(target_ip)
        country = response.country.name
#        print(f'IP {target_ip} 所属国家：{country}')
    except geoip2.errors.AddressNotFoundError:
        print(f'IP {target_ip} 未找到国家信息')
        return None
    finally:
        reader.close()
        return country

# 解析Shadowsocks链接函数
def parse_ss_link(link):
    ss_encoded_str = link[5:].split('#')[0]
    ss_encoded_server = link[5:].split('#')[1].split('@')[1].split(':')[0]
    ss_decoded_bytes = base64.b64decode(ss_encoded_str + '==')
    ss_decoded_str = ss_decoded_bytes.decode('utf-8')
    ss_server_ip = ss_decoded_str.split('@')[1].split(':')[0]
    ss_server_name = ss_decoded_str.split('.')[0]
    return ss_server_name, ss_encoded_server, ss_server_ip


# 解析vmess链接函数,反回域名和ip地址

def parse_vmess_link(link):
    vmess_encoded_str = link[8:]
    vmess_encoded_str_padded = vmess_encoded_str + '=='
    vmess_decoded_bytes = base64.urlsafe_b64decode(vmess_encoded_str_padded)
    vmess_decoded_str = vmess_decoded_bytes.decode('utf-8')
    temp_json = json.loads(vmess_decoded_str)
#    print("old PS key:" + temp_json['ps'])

    if ( temp_json['ps'].find('直连') != -1 ):
        vmess_server_ip = temp_json['add']
        real_ip = get_ip_address(vmess_server_ip)
        real_country = find_country(real_ip)
        try:
            vmess_server_domain = temp_json['ps']
        
            #删除机场不规范的命名(包括中英文空格，中文括号，连号)
            vmess_server_name = vmess_server_domain.replace("-","").replace(" ","").replace("  ","").replace("【","[").replace("】","]").replace("[直连]","") + ": " + real_country
            temp_json['ps'] = vmess_server_name
#            print("new PS key:" + temp_json['ps'])
            return temp_json, real_ip
        except Exception as e:
            print("Error: ",e)
            return None, None
    return None,None

def get_jms_config():
    url = 'http://192.168.1.225/bigdata/bigdata.txt'
    response = requests.get(url)
    if response.status_code == 200:
        decoded_content = base64.b64decode(
            response.content.strip()).decode('utf_8')
        vmess_links = decoded_content.strip().split('\n')
        return vmess_links
    else:
        return None


def get_jms_config_test():
    decoded_content = base64.b64decode(''.strip()).decode('utf_8')
    vmess_links = decoded_content.strip().split('\n')
    return vmess_links

def get_ip_address(domain):
    try:
        # 使用 gethostbyname() 函数获取域名对应的 IP 地址
        ip_address = socket.gethostbyname(domain)
        country = find_country(ip_address)
        return ip_address
    except socket.gaierror:
        # 如果解析失败，则返回 None
        return None

def run():
    server_list = []
    json_list = []

    try:
        print("开始处理...")
        vmess_links = get_jms_config()
    except Exception as e:
        print("error: e")
        return

    # 遍历vmess链接
    for link in vmess_links:
        domain_ip = None
        if link.startswith('ss://'):
            domain_ip = parse_ss_link(link)
        elif link.startswith('vmess://'):
            try:
                last_json,real_ip = parse_vmess_link(link)
                if ( real_ip ):
                    server_list.append(real_ip)
                if ( last_json ):
                    json_list.append(last_json)
            except Exception as e:
                print("Error: " + e)

    print("解析正常")

    # 配置文件路径
    conf_file = '/var/www/ros/bigairport.rsc'

    # 写入ROS配置文件
    with open(conf_file, 'w') as f:
        f.write("/ip firewall address-list\n")
        f.write("remove [/ip firewall address-list find list=bigairport]\n")
        for entry in server_list:
            f.write('add address=' + entry + ' list=bigairport\n')
        f.close()

    # 写入修改后的节点订阅文件
    with open('/var/www/bigdata/bigdata.b64', 'w') as file:
        temp_b64 = ''
        for entry in json_list:
            temp_byte = json.dumps(entry,separators=(',', ':')).encode()
            temp_b64 += "vmess://" + base64.b64encode(temp_byte).decode() + '\n'
        file.write(base64.b64encode(temp_b64.encode()).decode())
        file.close()

run()
