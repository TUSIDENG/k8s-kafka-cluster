# wsl + debian系统搭建

## 安装master虚拟机和两个k3s-worder虚拟机

### 安装master

```powershell
$basePath="D:\wsl\cluster"
$installPath = Join-Path $basePath "k3s-master"
mkdir $installPath -Force

# 在线导入官方Debian镜像到指定目录
wsl --install -d Debian --location $installPath
```

**设置用户名和密码**
用户名：ks3-mster
密码：123456

详见图![ks3-msate-vm-install](imgs/k3s-master-vm-set-01.png)

##### 设置国内镜像源

```bash
sudo tee /etc/apt/sources.list.d/debian.sources <<EOF
Types: deb
URIs: https://mirrors.aliyun.com/debian
Suites: bookworm bookworm-updates
Components: main contrib non-free non-free-firmware
EOF

sudo tee -a /etc/apt/sources.list.d/debian.sources <<EOF
Types: deb
URIs: https://mirrors.aliyun.com/debian-security
Suites: bookworm-security
Components: main contrib non-free non-free-firmware
EOF

sudo apt clean
sudo apt update

# 安装curl
sudo apt install -y curl
```

##### 设置镜像加速器
1. 创建并编辑文件
```bash
sudo nano /etc/rancher/k3s/registries.yaml
```

2. 写入加速器配置
```yaml
mirrors:
     docker.io:
       endpoint:
         - "https://docker.1panel.live"
         - "https://hub.rat.dev"
         - "https://atomhub.openatom.cn"
         - "https://docker.m.daocloud.io"
```

##### 安装nginx并测试验证
1. 创建控制器
```bash
sudo kubectl create deployment nginx-test --image=nginx:alpine
```

2. 暴露服务为NodePort(Service)
Pod 正常运行后，执行以下命令，将 Nginx 的 80 端口映射到宿主机（也就是允许通过 30000+ 的外部端口访问）：

```bash
sudo kubectl expose deployment nginx-test --port=80 --type=NodePort --name=nginx-nodeport-service
```

3. 查看并获取映射端口
运行以下命令，获取 K8s 随机分配给你的本地端口：
```bash
sudo kubectl get svc nginx-nodeport-service
```

因为 WSL2 的本地网络回环有时会有概率性“罢工”导致 localhost 拒绝连接，拿到 5 位数端口后，请尝试以下两种路径访问：

路径 A（最直接）：
在 WSL2 终端输入 hostname -I | awk '{print $1}' 获取你当前这台虚拟机的真实 IP（如 172.28.30.32）。
然后直接在 Windows 浏览器输入：http://172.28.30.32:新端口号。

路径 B（本地回环）：
在 Windows 浏览器直接输入：http://localhost:新端口号。

只要 Pod 状态显示为 Running 且服务创建成功，这两种路径至少有一种可以立刻带你看到 Nginx 的欢迎界面！


##### 获取k3s-master ip和token名用于安装k3s-worker

```bash
# 获取ip
hostname -I | awk '{print $1}'

# 获取token
sudo cat /var/lib/rancher/k3s/server/node-token
```

### 安装k3s-worker1

```powershell
$basePath="D:\wsl\cluster"
$installPath = Join-Path $basePath "k3s-worker1"
mkdir $installPath -Force

# 在线导入官方Debian镜像到指定目录
wsl --install -d Debian --name k3s-worker1 --location $installPath
```

**设置用户名和密码**
用户名：k3s-worker1
密码：123456

##### 安装k3s-client
```bash
curl -sfL https://get.k3s.io | K3s_URL=https://<Master-IP>:6443 K3s_TOKEN=<Your-Token> sh -
```

## 常见问题

##### k3s安装失败如何卸载？
```bash
# uninstall K3s from a server node
/usr/local/bin/k3s-uninstall.sh

# To uninstall K3s from an agent node
/usr/local/bin/k3s-agent-uninstall.sh
```