* clash_sub的python脚本
## 说明 :
本项目提供解析ss/ssr/v2ray/clashR/clash订阅链接为Clash配置文件的自动化脚本,供学习交流使用。
### 感谢：https://github.com/celetor/convert2clash
* 上述程序不具体节点筛选功能
### 感谢：https://github.com/nonPointer/ClashHelper
* 上述程序不具备直接使用vmess格式的BASE64原始节点的功能

### 修改目的
* 本程序结合了上面的两个程序代码，可以直接根据原始vmess的BASE64节点，和自定义模板，直接生成本地配置文件，结合cron，可以方便自动化本地部署。
* 为啥采用BASE64源头文件？部分机场提供的订阅节点命名不规范，未录入国家等信息，编写了一个简单的程序进行自定义处理，包括规范命名，添加国家代码，删除流量提示信息等。并同步生成ros的节点地址列表文件。
```
clash_sub.py中的参数 :
 1. sub_url=订阅地址（多个地址;隔开）
 2. output_path=转换成功后文件输出路径 默认输出至当前文件夹的out.yaml中
 3. config_url=来自互联网的规则策略 默认值为https://cdn.jsdelivr.net/gh/Celeter/convert2clash@main/config.yaml
 4. config_path=来自本地的规则策略 默认选择当前文件的config.yaml文件
```
优先使用config_path的本地模板策略。正常情况下只需修改sub_url即可使用。
### 使用说明:
 1. 建立虚拟环境：python3 -m venv python
 2. 先执行./python/bin/pip install -r requirements.txt
 2. 再执行./python/bin/python clash_sub.py
