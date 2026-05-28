# KinD LoadBalancer 实现方案

## 问题背景

KinD (Kubernetes in Docker) 默认不支持 LoadBalancer 类型 Service，因为缺少云厂商的 cloud provider。要在 KinD 中使用 LoadBalancer，需要安装 **MetalLB**。

## 方案：KinD + MetalLB

MetalLB 为裸金属集群（和 KinD 这种模拟环境）提供网络负载均衡功能。

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        KinD Cluster                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │  Pod        │    │  Pod        │    │  Pod        │       │
│  │  kafka-0    │    │  kafka-1    │    │  kafka-2    │       │
│  │  :9092      │    │  :9092      │    │  :9092      │       │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴──────┐      │
│  │              kube-proxy (iptables)                 │      │
│  └──────────────────────┬────────────────────────────┘      │
│                          │                                   │
│  ┌──────────────────────┴────────────────────────────┐      │
│  │              MetalLB (Layer 2)                     │      │
│  │         172.24.0.100 - 172.24.0.150               │      │
│  └──────────────────────┬────────────────────────────┘      │
└─────────────────────────┼───────────────────────────────────┘
                          │ ARP/NDP
┌─────────────────────────┼───────────────────────────────────┐
│   Docker Host Network   │                                   │
│                    ┌────┴────┐                              │
│                    │ Host    │  ← 你的开发机                  │
│                    │ eth0    │                              │
│                    └─────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### 工作原理

MetalLB 在 Layer 2 模式下工作：
1. 当 Service 设置为 `LoadBalancer` 类型时，MetallB 分配一个 IP
2. MetallB 让集群中某个节点"认领"这个 IP（通过 ARP/NDP 广播）
3. 客户端连接这个 IP，数据包被路由到对应节点的 kube-proxy
4. kube-proxy 再将流量转发到实际的 Pod

### 安装步骤

#### 1. 安装 MetalLB

```powershell
# 安装 MetallB（官方 v0.14.5）
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.5/config/manifests/metallb-native.yaml

# 等待 MetallB pods 启动完成
kubectl get pods -n metallb-system -w
```

#### 2. 配置 IP 地址池

创建 `metallb-config.yaml`：

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  # 根据你的 KinD Docker 网络选择空闲 IP 段
  # KinD 创建的容器通常在 172.17-24.x.x 网段
  - 172.24.0.100-172.24.0.150
  autoAssign: true
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: example
  namespace: metallb-system
spec:
  # 不指定 ipAddressPools 表示使用所有地址池
  ipAddressPools:
  - first-pool
```

```powershell
kubectl apply -f metallb-config.yaml
```

#### 3. 修改 Kafka Service 为 LoadBalancer

```powershell
# 查看当前 Service 类型
kubectl get svc kafka-nodeport -n default

# 修改为 LoadBalancer
kubectl patch svc kafka-nodeport -n default -p '{"spec":{"type":"LoadBalancer"}}'

# 验证 EXTERNAL-IP 是否分配成功
kubectl get svc kafka-nodeport -n default
```

期望输出：
```
NAME            TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)          AGE
kafka-nodeport  LoadBalancer   10.96.247.5    172.24.0.100   9094:30092/TCP   2d11h
```

#### 4. 从宿主机测试连接

```powershell
# 测试 MetallB 分配的 IP 是否可达
Test-NetConnection -ComputerName 172.24.0.100 -Port 9094

# 使用该 IP 连接 Kafka
# 在 producer.py 中修改 BOOTSTRAP_SERVERS 为 "172.24.0.100:9094"
```

### Kafka Listener 配置说明

为了让外部客户端正确连接，Kafka 的 `advertised.listeners` 需要匹配实际的访问地址：

| 场景 | advertised.listeners | 客户端连接地址 |
|------|---------------------|---------------|
| NodePort | `EXTERNAL://localhost:9094` | `localhost:30092` |
| LoadBalancer | `EXTERNAL://<LB_IP>:9094` | `<LB_IP>:9094` |

### 完整 Kafka Service 配置示例

如果需要创建新的 LoadBalancer Service：

```yaml
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
      protocol: TCP
```

```powershell
kubectl apply -f kafka-lb-service.yaml
```

### 故障排查

```powershell
# 1. 检查 MetallB 日志
kubectl logs -n metallb-system -l app=metallb --tail=50

# 2. 检查 IPAddressPool 状态
kubectl get ipaddresspool -n metallb-system

# 3. 检查 L2Advertisement 状态
kubectl get l2advertisement -n metallb-system

# 4. 查看 Service 详情
kubectl describe svc kafka-nodeport -n default
```

### 注意事项

1. **IP 地址范围**：必须选择与 KinD Docker 网络不冲突的空闲 IP
2. **KinD 网络**：KinD 创建的容器网络通常是 `172.17-24.x.x`，需要避开已用的 IP
3. **重启集群**：如果 KinD 集群重启，MetallB 配置会丢失，需要重新 apply
4. **多节点 KinD**：如果 KinD 有多个 control-plane 节点，MetallB 会选择其中一个来响应 ARP

### 参考链接

- MetalLB 官方文档：https://metallb.universe.tf/
- MetalLB GitHub：https://github.com/metallb/metallb
