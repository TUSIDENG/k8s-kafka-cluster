# Kafka集群部署方式对比

本文档介绍在Kubernetes环境下部署Kafka集群的三种方式。

## 方式对比

| 特性 | 原生YAML | Helm Chart | Operator |
|------|----------|------------|----------|
| 复杂度 | 中等 | 简单 | 较复杂 |
| 学习曲线 | 陡峭（需深入理解K8s） | 平缓 | 陡峭（需理解CRD） |
| 生产就绪 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 自动化运维 | 手动 | 半自动 | 全自动 |
| 故障恢复 | 手动 | 手动 | 自动 |
| 升级策略 | 重建 | helm upgrade | 滚动升级 |
| 适用场景 | 学习/定制化 | 开发/测试 | 生产环境 |

---

## 方式一：原生YAML（Kubernetes Manifest）

### 原理
直接使用Kubernetes原生资源对象（StatefulSet、Service、ConfigMap等）部署，每个组件独立管理。

### 文件结构
```
kafka-yaml/
├── kafka-3nodes.yaml      # StatefulSet + Service
├── configmap.yaml         # 配置
└── pvc.yaml               # 存储声明
```

### 部署命令
```bash
kubectl apply -f kafka-3nodes.yaml
```

### 适用场景
- **学习Kafka和Kubernetes**：理解 StatefulSet、Headless Service 等概念
- **定制化需求**：需要深度修改Kafka配置
- **简单集群**：节点数量固定，配置不常变更

### 优点
- 无额外依赖，直接使用kubectl
- 完全可控，配置透明
- 适合理解底层原理

### 缺点
- 配置繁琐，易出错
- 升级麻烦，需要重建
- 无自动化故障恢复
- 难以管理多环境（dev/staging/prod）

---

## 方式二：Helm Chart

### 原理
使用Helm包管理器，通过模板化配置一键部署。Helm Chart封装了Kubernetes资源清单，提供了可配置的values参数。

### 部署命令
```bash
# 添加仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 安装Kafka（KRaft模式）
helm install kafka bitnami/kafka \
  --set kraft.enabled=true \
  --set replicaCount=3 \
  --set persistence.size=2Gi \
  --set service.type=NodePort

# 查看部署
helm list
kubectl get pods -l app.kubernetes.io/name=kafka
```

### 适用场景
- **开发/测试环境**：快速部署、快速销毁
- **简单生产需求**：配置相对标准
- **多环境管理**：通过values文件区分dev/staging/prod

### 优点
- 一键部署，简单快捷
- 版本管理（helm list/rollback）
- 参数化配置，避免重复
- 支持helm repo共享

### 缺点
- 模板复杂性封装，对底层不透明
- 有状态服务升级仍有一定风险
- Operator能力不足，无CRD管理

---

## 方式三：Strimzi Operator（推荐生产环境）

### 原理
通过Kubernetes Operator模式，定义Kafka CRD资源。Operator控制器监听资源变化，自动完成部署、扩缩容、升级等操作。

### 部署命令
```bash
# 1. 部署Operator
kubectl create namespace kafka-operator
kubectl apply -f 'https://strimzi.io/install/latest?namespace=kafka-operator' -n kafka-operator

# 2. 等待Operator就绪
kubectl wait --for=condition=ready pod -l strimzi.io/kind=operator -n kafka-operator --timeout=120s

# 3. 创建Kafka集群
cat <<EOF | kubectl apply -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafka:
    version: 3.8.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
      - name: external
        port: 9094
        type: nodeport
    storage:
      type: persistent-claim
      size: 100Gi
      class: fast-storage
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      class: fast-storage
EOF

# 4. 验证
kubectl get kafka
kubectl get pods -l app.kubernetes.io/name=kafka
```

### 适用场景
- **生产环境**：高可用、自动化运维
- **大规模集群**：需要频繁扩缩容
- **企业级需求**：需要KafkaTopic/User等CRD管理
- **跨环境部署**：dev/staging/prod一致性

### 优点
- **CRD资源管理**：KafkaTopic、KafkaUser等自定义资源
- **自动化运维**：
  - 自动故障检测和恢复
  - 滚动升级不停服
  - 自动平衡分区
- **生产就绪**：
  - 内置监控指标
  - 安全认证集成
  - 存储自动扩缩容
- **声明式配置**：只需声明期望状态，Operator自动实现

### 缺点
- 学习曲线陡峭（需理解Operator、CRD概念）
- 初期配置复杂
- Operator本身也需要维护

---

## 快速选择指南

```
学习/实验/定制化需求？
├── 是 → 原生YAML
└── 否
    ├── 开发/测试环境？
    │   ├── 是 → Helm Chart（快速部署）
    │   └── 否
    │       ├── 小规模生产？
    │       │   └── 是 → Helm Chart
    │       └── 大规模/企业级生产？
    │           └── 是 → Strimzi Operator
```

---

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Kubernetes | 1.21+ |
| Helm | 3.8+ |
| kubectl | 与K8s版本匹配 |

### Windows Docker Desktop用户
```powershell
# 安装Helm（使用Chocolatey）
choco install helm -y

# 验证安装
helm version
kubectl cluster-info
```

---

## 资源清理

```bash
# 原生YAML
kubectl delete -f kafka-3nodes.yaml

# Helm
helm uninstall kafka
kubectl delete pvc -l app.kubernetes.io/name=kafka

# Operator
kubectl delete -f 'https://strimzi.io/install/latest?namespace=kafka-operator' -n kafka-operator
kubectl delete kafka my-cluster
```
