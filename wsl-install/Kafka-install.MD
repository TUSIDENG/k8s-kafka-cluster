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
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
  namespace: kafka
spec:
  kafka:
    version: 3.7.0
    replicas: 3
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
      inter.broker.protocol.version: "3.7"
    storage:
      # 🚀 从 ephemeral 改为持久化存储卷声明（Persistent Claim）
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 5Gi # 限制每个节点最多使用 5GB 磁盘空间
          deleteClaim: false # 即使 Pod 删了，也绝对不自动删除底层的硬盘数据
          class: local-path  # 🚀 使用 K3s 自带的本地动态持久化存储类
    template:
      pod:
        spec:
          topologySpreadConstraints: []
  kraft: {}
```

5. 应用配置
```bash
sudo kubectl apply -f kafka-3-replicas.yaml
```
