# Kafka 集群不同架构实现方案

## 概述

本文档对比四种不同的 Kafka 集群部署架构，从简单到复杂，帮助你选择适合自己场景的方案。

---

## 架构总览

| 架构 | 节点数 | 负载均衡 | 外部访问方式 | 复杂度 | 适用场景 |
|------|--------|----------|-------------|--------|----------|
| **架构 A** | KinD 单节点 | 无 | port-forward | 低 | 快速测试 |
| **架构 B** | KinD 三节点 | 无 | port-forward x3 | 中 | 本地开发 |
| **架构 C** | KinD 三节点 | MetalLB | LoadBalancer | 中 | 学习研究 |
| **架构 D** | 3x VM + k3s | ServiceLB | LoadBalancer | 中高 | 模拟生产 |
| **架构 E** | 3x VM + k3s | HAProxy | 单一入口 | 高 | 生产级模拟 |

---

## 架构 A：KinD 单节点 + port-forward

### 架构图

```
┌─────────────────────────────────────────────┐
│            Your Development Machine          │
│                                             │
│   PowerShell                                │
│   ┌─────────────────────────────────────┐   │
│   │ kubectl port-forward kafka-0 9094:9094│   │
│   └─────────────────────────────────────┘   │
│                    │                        │
│                    ▼                        │
│   ┌─────────────────────────────────────┐   │
│   │         KinD Cluster (1 node)        │   │
│   │                                     │   │
│   │   ┌─────────────────────────────┐   │   │
│   │   │      kafka-0 (Pod)          │   │   │
│   │   │      :9092 :9094 :9093      │   │   │
│   │   └─────────────────────────────┘   │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 配置

```powershell
# 创建 KinD 集群（默认单节点）
kind create cluster --name kafka-cluster

# 部署 Kafka
kubectl apply -f kafka-3nodes.yaml

# port-forward
kubectl port-forward pod/kafka-0 9094:9094
```

### Kafka 配置

```bash
listeners=INTERNAL://:9092,EXTERNAL://:9094,CONTROLLER://:9093
advertised.listeners=INTERNAL://kafka-0.kafka-headless:9092,EXTERNAL://localhost:9094
```

### 优点

- 快速启动
- 资源占用少
- 适合验证想法

### 缺点

- 单点故障
- 无法真正模拟多节点集群

---

## 架构 B：KinD 三节点 + port-forward x3

### 架构图

```
┌───────────────────────────────────────────────────────────────────┐
│                      Your Development Machine                      │
│                                                                     │
│   Terminal 1              Terminal 2              Terminal 3        │
│   ┌────────────┐          ┌────────────┐          ┌────────────┐     │
│   │pf 9094→k0  │          │pf 9095→k1 │          │pf 9096→k2 │     │
│   └─────┬──────┘          └─────┬──────┘          └─────┬──────┘     │
└─────────┼────────────────────────┼────────────────────────┼───────────┘
          │                        │                        │
          ▼                        ▼                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                        KinD Cluster (3 nodes)                       │
│                                                                     │
│   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐ │
│   │  kafka-0   │◄────────►│  kafka-1   │◄────────►│  kafka-2   │ │
│   │  :9092     │    KRaft   │  :9092     │    KRaft   │  :9092     │ │
│   │  :9094(ext)│          │  :9094(ext)│          │  :9094(ext)│ │
│   └─────────────┘          └─────────────┘          └─────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### KinD 配置

创建 `kind-config.yaml`：

```yaml
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
name: kafka-cluster
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
```

```powershell
kind create cluster --config kind-config.yaml
```

### 配置步骤

```powershell
# 1. 部署 Kafka
kubectl apply -f kafka-3nodes.yaml

# 2. 开启 3 个 port-forward（需要 3 个终端）
# 终端 1
kubectl port-forward -n default pod/kafka-0 9094:9094
# 终端 2
kubectl port-forward -n default pod/kafka-1 9095:9094
# 终端 3
kubectl port-forward -n default pod/kafka-2 9096:9094
```

### Kafka 配置（关键修改）

必须让每个 broker 广告不同的端口：

```bash
# 使用 NODE_ID 动态计算端口
export NODE_ID=$(echo $HOSTNAME | sed -e 's/kafka-//')
sed -i "s|advertised.listeners=.*|advertised.listeners=INTERNAL://\$HOSTNAME.kafka-headless.default.svc.cluster.local:9092,EXTERNAL://localhost:\$((9094 + NODE_ID))|g" /opt/kafka/config/kraft/server.properties

# 结果：
# kafka-0 → EXTERNAL://localhost:9094
# kafka-1 → EXTERNAL://localhost:9095
# kafka-2 → EXTERNAL://localhost:9096
```

### 客户端连接

```python
# producer.py
BOOTSTRAP_SERVERS = "127.0.0.1:9094,127.0.0.1:9095,127.0.0.1:9096"
```

### 优点

- 模拟真实多节点集群
- 负载分布在多个节点
- 适合开发测试

### 缺点

- 需要多个终端/port-forward
- 客户端需要知道所有 broker 地址
- port-forward 可能不稳定

---

## 架构 C：KinD 三节点 + MetalLB LoadBalancer

### 架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KinD Cluster (3 nodes)                        │
│                                                                       │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐          │
│   │  kafka-0    │      │  kafka-1    │      │  kafka-2    │          │
│   │  :9092      │      │  :9092      │      │  :9092      │          │
│   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘          │
│          │                    │                    │                 │
│   ┌──────┴────────────────────┴────────────────────┴──────┐        │
│   │                    kube-proxy                           │        │
│   └──────────────────────────┬─────────────────────────────┘        │
│                              │                                       │
│   ┌──────────────────────────┴─────────────────────────────┐         │
│   │                    MetalLB (Layer 2)                    │         │
│   │                  172.24.0.100 - 172.24.0.150           │         │
│   └──────────────────────────┬─────────────────────────────┘         │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ ARP/NDP
┌──────────────────────────────┼──────────────────────────────────────┐
│   Docker Host / Windows       │                                      │
│                              ┌─┴─┐                                    │
│                              │客户端│                                  │
│                              └──┬─┘                                    │
└────────────────────────────────┼─────────────────────────────────────┘
                                 │
                          172.24.0.100:9094
```

### 安装 MetalLB

```powershell
# 1. 安装 MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.5/config/manifests/metallb-native.yaml

# 2. 等待就绪
kubectl get pods -n metallb-system -w
```

### 配置 IP 地址池

```yaml
# metallb-config.yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.24.0.100-172.24.0.150
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: example
  namespace: metallb-system
spec:
  ipAddressPools:
  - first-pool
```

```powershell
kubectl apply -f metallb-config.yaml
```

### 修改 Kafka Service

```powershell
# 将 NodePort 改为 LoadBalancer
kubectl patch svc kafka-nodeport -n default -p '{"spec":{"type":"LoadBalancer"}}'

# 查看分配的 IP
kubectl get svc kafka-nodeport -n default
```

输出：
```
NAME            TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)          AGE
kafka-nodeport  LoadBalancer   10.96.247.5    172.24.0.100   9094:30092/TCP   2d11h
```

### Kafka 配置

```bash
# 需要让 Kafka 广告 LoadBalancer 的 IP
advertised.listeners=INTERNAL://$HOSTNAME.kafka-headless:9092,EXTERNAL://172.24.0.100:9094
```

### 客户端连接

```python
# producer.py
BOOTSTRAP_SERVERS = "172.24.0.100:9094"
```

### 优点

- 单一入口，客户端配置简单
- 自动负载均衡
- 更接近生产环境

### 缺点

- 需要额外安装配置 MetalLB
- IP 地址需要与 Docker 网络协调

---

## 架构 D：3x VM + k3s + ServiceLB

### 架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Your Hypervisor (VMware)                        │
│                                                                       │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│   │   VM 1       │    │   VM 2       │    │   VM 3       │          │
│   │  k3s-agent   │    │  k3s-agent   │    │  k3s-agent   │          │
│   │   kafka-0   │    │   kafka-1   │    │   kafka-2   │          │
│   │  eth0: 192.168.1.101 │  eth0: 192.168.1.102 │  eth0: 192.168.1.103 │   │
│   └──────────────┘    └──────────────┘    └──────────────┘          │
│          ▲                  ▲                  ▲                     │
│          │                  │                  │                     │
│   ┌──────┴──────────────────┴──────────────────┴──────┐              │
│   │              k3s Server (可能在同一 VM)            │              │
│   │                    192.168.1.100                   │              │
│   └──────────────────────────┬─────────────────────────┘              │
│                              │                                        │
│   ┌──────────────────────────┴─────────────────────────┐             │
│   │              ServiceLB (k3s 内置)                    │             │
│   │              192.168.1.200 - 192.168.1.220          │             │
│   └──────────────────────────┬─────────────────────────┘             │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
┌──────────────────────────────┼────────────────────────────────────────┐
│   Your Laptop                │                                        │
│   ┌──────────────────────────┴────────────────────────────────────┐   │
│   │                      客户端                                     │   │
│   │                  192.168.1.200:9094                           │   │
│   └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### k3s 安装

**Server 节点 (VM 1)**：
```bash
curl -sfL https://get.k3s.io | sh -s - server --cluster-init
```

**Agent 节点 (VM 2, 3)**：
```bash
# 在 VM1 获取 token
cat /var/lib/rancher/k3s/server/node-token

# 在 VM2, VM3 加入
curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.101:6443 K3S_TOKEN=<TOKEN> sh -
```

### ServiceLB 自动分配 IP

k3s 内置 ServiceLB，会自动为 LoadBalancer Service 分配空闲 IP。

```powershell
# 创建 Kafka Service
kubectl apply -f kafka-lb-service.yaml
```

```yaml
# kafka-lb-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka-lb
  labels:
    app: kafka
spec:
  type: LoadBalancer
  selector:
    app: kafka
  ports:
    - name: external
      port: 9094
      targetPort: 9094
```

```powershell
# 查看分配的 IP
kubectl get svc kafka-lb
```

输出：
```
NAME      TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)          AGE
kafka-lb  LoadBalancer   10.42.0.100   192.168.1.200   9094:30092/TCP   1d
```

### Kafka 配置

```bash
# 每个 broker 广告 Service IP
advertised.listeners=INTERNAL://$HOSTNAME.kafka-headless:9092,EXTERNAL://192.168.1.200:9094
```

### 优点

- 真实 VM 环境，资源完全隔离
- k3s 内置 LoadBalancer，无需额外配置
- 更接近生产环境

### 缺点

- 需要 3 台 VM，资源需求高
- 需要 VMware 许可证
- 运维复杂度增加

---

## 架构 E：3x VM + k3s + HAProxy（生产级）

### 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Your Hypervisor                                  │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                        HAProxy (独立 VM 或容器)                  │   │
│   │                         192.168.1.50:9094                       │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│          ┌─────────────────────────┼─────────────────────────┐           │
│          │                         │                         │           │
│   ┌──────┴──────┐          ┌──────┴──────┐          ┌──────┴──────┐   │
│   │   VM 1      │          │   VM 2      │          │   VM 3      │   │
│   │  k3s-agent  │          │  k3s-agent  │          │  k3s-agent  │   │
│   │   kafka-0   │          │   kafka-1   │          │   kafka-2   │   │
│   │ 192.168.1.101│         │ 192.168.1.102│         │ 192.168.1.103│  │
│   └─────────────┘          └─────────────┘          └─────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼──────────────────────────────────────┐
│   客户端                           │                                       │
│   只需连接 192.168.1.50:9094       │                                       │
└───────────────────────────────────┴──────────────────────────────────────┘
```

### HAProxy 配置

```haproxy
# /etc/haproxy/haproxy.cfg
global
    log stdout local0
    maxconn 4096

defaults
    log     global
    mode    tcp
    option  tcplog
    timeout connect 5s
    timeout client  50s
    timeout server  50s

listen kafka
    bind *:9094
    mode tcp
    balance roundrobin
    option tcp-check
    # Kafka broker 直接 IP
    server kafka-0 192.168.1.101:9092 check inter 3s rise 2 fall 3
    server kafka-1 192.168.1.102:9092 check inter 3s rise 2 fall 3
    server kafka-2 192.168.1.103:9092 check inter 3s rise 2 fall 3
```

### Kafka 配置

```bash
# 所有 broker 广告 HAProxy 地址
advertised.listeners=INTERNAL://$HOSTNAME.kafka-headless:9092,EXTERNAL://192.168.1.50:9094
```

### 优点

- 单一入口，客户端配置极简
- HAProxy 提供健康检查和高级负载均衡策略
- 完全模拟生产环境
- 可以后续扩展为 keepalived HA

### 缺点

- 额外增加 HAProxy 组件
- 需要额外 VM/资源
- HAProxy 单点（可用 keepalived 解决）

---

## 对比总结

### 网络访问对比

| 架构 | 客户端连接地址 | 需要知道所有 broker | 负载均衡 |
|------|---------------|---------------------|----------|
| A | localhost:9094 | 是 | 无 |
| B | localhost:9094,9095,9096 | 是 | 客户端实现 |
| C | 172.24.0.100:9094 | 否 | MetalLB |
| D | 192.168.1.200:9094 | 否 | ServiceLB |
| E | 192.168.1.50:9094 | 否 | HAProxy |

### 适用场景

| 架构 | 推荐场景 |
|------|---------|
| A | 一次性验证、CI/CD 快速测试 |
| B | 日常开发、需要多节点测试 |
| C | 学习 Kubernetes 网络、了解 LoadBalancer |
| D | 模拟生产环境、团队培训 |
| E | 完整的生产级模拟、项目演示 |

### 资源需求

| 架构 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| KinD (A/B/C) | 4+ | 8GB+ | 20GB+ |
| 3x VM (D/E) | 8+ | 16GB+ | 100GB+ |

---

## 推荐选择

```
┌─────────────────────────────────────────────────────────┐
│                    快速选择指南                           │
└─────────────────────────────────────────────────────────┘

                        │
                        ▼
              ┌─────────────────┐
              │  你要做什么？    │
              └────────┬────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
  学习/研究         日常开发        模拟生产
       │               │               │
       ▼               ▼               ▼
  架构 C 或 D      架构 B         架构 E
```

- **学习 Kubernetes 网络** → 架构 C (KinD + MetalLB)
- **日常 Kafka 开发** → 架构 B (KinD 三节点 + port-forward)
- **完整生产模拟** → 架构 E (3x VM + k3s + HAProxy)
