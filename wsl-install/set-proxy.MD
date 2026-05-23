# 设置全局代理

## 全局代理配置
```bash
#!/bin/sh
# 获取 Windows 主机 IP
export PROXY_IP=$(ip route show | grep -i default | awk '{print $3}')

# 全局代理配置（NAT模式下指向宿主机代理）
export http_proxy="http://$PROXY_IP:6789"
export https_proxy="http://$PROXY_IP:6789"
# 如果你的代理同时支持 socks5，也可以加上，否则只保留 http/https 即可
export all_proxy="socks5://$PROXY_IP:6789"
export no_proxy="localhost,127.0.0.1,172.16.0.0/12,192.168.0.0/16,.docker.internal"

# 大写环境变量，兼容部分程序（如 curl、wget、apt）
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
# export ALL_PROXY="$all_proxy"
export NO_PROXY="$no_proxy"
```

## 创建代理配置文件，并复制上面的配置

sudo nano /etc/profile.d/proxy.sh
