import yaml
import requests
import sys
import os
import socket

from yaml.loader import FullLoader

# 根据机场节点的原始yaml订阅配置文件，根据自定义的筛选/过滤规则进行处理，得到优化后的配置文件
class MyNodes:
    def __init__(self, name: str, group: str, url: str, inclusion: list, exclusion: list, dedup: bool):
        self.name = name
        self.group = group
        self.url = url
        self.inclusion = inclusion
        self.exclusion = exclusion
        self.nodes = []
        self.dedup = dedup

        if isinstance(self.url,dict):
            self.data = self.url
        else:    
            status_code = 200
            try:
                headers = {
                    "User-Agent": "ClashForAndroid/2.5.12",  # V2board 根据 UA 下发配置
                }
                r = requests.get(url, headers=headers)
                status_code = r.status_code
                assert status_code == 200
                self.data = yaml.load(r.text, Loader=FullLoader)
                # 缓存
                with open("{}.yaml".format(group), "w", encoding="utf-8") as f:
                    f.write(r.text)
            except Exception as e:
                if status_code != 200:
                    self.log(f"HTTP Error: {status_code}")
                self.log("加载异常")
                if os.path.exists("{}.yaml".format(group)):
                    self.log("使用上次缓存")
                    with open("{}.yaml".format(group), "r", encoding="utf-8") as f:
                        self.data = yaml.load(f, Loader=FullLoader)
                else:
                    self.data = None
                    self.log("节点组为空")

    def purge(self):
        self.nodes = self.data['proxies']
        nodes_good = []
        # blacklist keywords
        for node in self.nodes:
            for k in self.exclusion:
                if k in node['name'].lower() or k in node['server'].lower():
                    self.nodes.remove(node)
                    self.log("Drop: {}".format(node['name']))
                    break

        # whitelist keywords
        for node in self.nodes:
            for k in self.inclusion:
                if k in node['name'].lower() or k in node['server'].lower():
                    nodes_good.append(node)
                    # site.log("Take: {}".format(node['name']))
                    break

        # deduplicate
        if self.dedup:
            used = set()
            for node in nodes_good:
                try:
                    ip = socket.getaddrinfo(node['server'], None)[0][4][0]
                    p = (ip, node['port'])
                    if p in used:
                        self.log("Drop: {}, dup!".format(node['name']))
                        nodes_good.remove(node)
                    else:
                        site.log("Take: {}".format(node['name']))
                        used.add(p)
                except:
                    self.log(f"Failed to resolve node {node['name']}: {node['server']}")
        else:
            self.log("Dedup disabled")
            for node in nodes_good:
                self.log("Take: {}".format(node['name']))

        self.nodes = nodes_good

    def get_titles(self):
        return list(map(lambda x: x['name'], self.nodes))

    def log(self, message: str):
        print("[{}] {}".format(self.name, message))

# 动态生成处理类对象
def process_node_rule(config: dict, nodes_info = None) -> MyNodes:
    # enable dedup by default
    if "dedup" not in config:
        config['dedup'] = True

    # 根据附加信息是否存在，决定具体处理方法
    if nodes_info != None:
        return MyNodes(config['name'], config['group'], nodes_info, config['inclusion'], config['exclusion'], config['dedup'])
    else:
        return MyNodes(config['name'], config['group'], config['url'], config['inclusion'], config['exclusion'], config['dedup'])

# 根据节点规则，获得处理后的全部新节点
def get_last_nodes(nodes_info = None):
    with open("nodes.yaml", "r", encoding="utf-8") as f:
        rule_data = yaml.load(f, Loader=FullLoader)
        mynodes = []
        for c in rule_data:
            c['inclusion'] = list(map(lambda x: x.lower(), c['inclusion']))
            c['exclusion'] = list(map(lambda x: x.lower(), c['exclusion']))
            if nodes_info != None:
                mynode = process_node_rule(c, nodes_info)
            else:
                mynode = process_node_rule(c)
            if mynode.data != None:
                mynode.purge()

            mynodes.append(mynode)
        return mynodes

# 获得处理后的配置文件
def new_config_data(mynodes, old_config):
    for mynode in mynodes:
        #if mynode.data != None:
        if mynode.nodes != None:
            mynode.purge()
            old_config['proxies'] += mynode.nodes
            old_config['proxy-groups'][list(map(lambda x: x['name'], old_config['proxy-groups'])).index(mynode.group)]['proxies'] += mynode.get_titles()

    # 对节点名去重
    old_config['proxies'] = list({x['name']: x for x in old_config['proxies']}.values())

    return old_config

if __name__ == "__main__":
    output_file = sys.argv[2] if len(sys.argv) == 3 else "out.yaml"
    mynodes = get_last_nodes()
    print("---------------------")

    with open("template.yaml", "r",  encoding="utf-8") as f1:
        old_config = yaml.load(f1, Loader=FullLoader)

    new_config_data = new_config_data(mynodes, old_config)

    with open(output_file, "w", encoding="utf-8") as f2:
        f2.write(yaml.dump(new_config_data, default_flow_style=False, allow_unicode=True))
