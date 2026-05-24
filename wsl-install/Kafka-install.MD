# Kafka 安装

## 安装 Strimzi Kafka Operator

1. 创建独立的命名空间
```bash
sudo kubectl create namespace kafka
```

2. 安装 1.0.0 自定义资源定义 (CRDs)
```bash
sudo kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.0.0/strimzi-crds-1.0.0.yaml -n kafka
```

3. 再安装 1.0.0 核心集群控制器 (Cluster Operator)
```bash
sudo kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.0.0/strimzi-cluster-operator-1.0.0.yaml -n kafka
```

4. kafka 3副本创建
创建kafka-3-replicas.yaml 配置文件
```bash
nano kafka-3-replicas.yaml
```
配置如下：
```yaml
# ==========================================
# 1. 基础环境与全局上帝权限 (RBAC)
# ==========================================
apiVersion: v1
kind: Namespace
metadata:
  name: kafka
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: strimzi-cluster-operator
  namespace: kafka
---
# 🚀 强行绑定上帝权限，彻底杜绝 1.0.0 新版租约(Lease)权限产生的任何 Forbidden 闪退
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: strimzi-cluster-operator
subjects:
  - kind: ServiceAccount
    name: strimzi-cluster-operator
    namespace: kafka
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
# ==========================================
# 2. Strimzi 1.0.0 Operator 控制器（最新版·WSL2 调优）
# ==========================================
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strimzi-cluster-operator
  namespace: kafka
spec:
  replicas: 1
  selector:
    matchLabels:
      name: strimzi-cluster-operator
  template:
    metadata:
      labels:
        name: strimzi-cluster-operator
    spec:
      serviceAccountName: strimzi-cluster-operator
      containers:
        - name: strimzi-cluster-operator
          image: quay.io/strimzi/operator:1.0.0 # 🚀 回归最新的 1.0.0 版本
          imagePullPolicy: IfNotPresent
          # 🚀 核心修复 1：压榨容器内核边界，防止 JVM 盲目申请大内存导致 WSL2 崩溃
          resources:
            limits:
              cpu: "1"
              memory: "512Mi"
            requests:
              cpu: "200m"
              memory: "256Mi"
          env:
            # 🚀 核心修复 2：针对 1.0.0 的 OpenJDK 21 进行极限降额
            # -Xms128m/-Xmx384m: 把内存砍到最低
            # -XX:-UseLargePages: 彻底禁用大页内存映射，这是破除 WSL2 无日志闪退的关键！
            # -XX:+UseSerialGC: 换用最轻量化的串行垃圾回收器
            - name: JAVA_OPTS
              value: "-Xms128m -Xmx384m -XX:-UseLargePages -XX:+UseSerialGC"
            - name: STRIMZI_NAMESPACE
              value: "kafka"
            - name: STRIMZI_DEFAULT_KAFKA_EXPORTER_IMAGE
              value: quay.io/strimzi/kafka:latest-kafka-3.7.0
            - name: STRIMZI_DEFAULT_CRUISE_CONTROL_IMAGE
              value: quay.io/strimzi/cruise-control:latest
            - name: STRIMZI_LEADER_ELECTION_ENABLED
              value: "true"
---
# ==========================================
# 3. Kafka 1.0.0 架构：三副本持久化节点池
# ==========================================
apiVersion: kafka.strimzi.io/v1
kind: KafkaNodePool
metadata:
  name: kraft-pool
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 3
  roles:
    - broker
    - controller
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: false
        class: local-path
  template:
    pod:
      topologySpreadConstraints: []
---
# ==========================================
# 4. Kafka 集群元数据与网络暴露
# ==========================================
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: my-cluster
  namespace: kafka
  annotations:
    strimzi.io/node-pools: "enabled"
    strimzi.io/kraft: "enabled"
spec:
  kafka:
    version: 3.7.0
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: external
        port: 9094
        type: nodeport
        tls: false
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
```

5. 应用配置
```bash
sudo kubectl apply -f kafka-3-replicas.yaml
```

5. 进入滚动监听状态
```bash
sudo kubectl get pods -n kafka -w
```

6. 查看集群状态
```bash
sudo kubectl get kafka my-cluster -n kafka
```

7. 查看volume 状态
```bash
sudo kubectl get pvc -n kafka

# 使用local-path,在如下路径可以看到看到 Kafka 的 log 日志分片和数据：
ls -l /var/lib/rancher/k3s/storage/
```

8. 查看operator状态
```bash
sudo kubectl describe pod -n kafka -l name=strimzi-cluster-operator
```

## 常见问题处理

### 失败后删除服务重来
1. 删除kafka集群和节点池
```bash
sudo kubectl delete kafka my-cluster -n kafka --ignore-not-found=true
sudo kubectl delete kafkanodepool kraft-pool -n kafka --ignore-not-found=true
```

2. 查看operator报错日志
```bash
sudo kubectl logs -n kafka -l name=strimzi-cluster-operator --tail=100
```

### 权限命名冲突
```bash
# 1. 安全地干掉旧的、卡死的集群权限绑定
sudo kubectl delete clusterrolebinding strimzi-cluster-operator

# 2. 重新一键应用你的一体化 YAML，建立正确的持久化三副本通路
 sudo kubectl apply -f kafka-3-replicas.yaml
```

生产环境避免权限命名冲突
* 通过 Helm Chart 自动渲染命名空间（最主流）
* 在 YAML 配置文件中为资源命名“加后缀”
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: strimzi-cluster-operator-kafka-prod # 🚀 加上特定的后缀
subjects:
  - kind: ServiceAccount
    name: strimzi-cluster-operator
    namespace: kafka
roleRef:
  kind: ClusterRole
  name: strimzi-cluster-operator
  apiGroup: rbac.authorization.k8s.io
```