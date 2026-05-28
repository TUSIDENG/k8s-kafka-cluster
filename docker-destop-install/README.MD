# 使用docker desktop部署kafka集群

## 原生yaml部署

参见[原生yaml部署](yaml_deployment\README.MD)

---

## Kafka专用命令

### 查看Kafka集群状态

```powershell
# 查看Kafka Pod
kubectl get pods -l app=kafka

# 查看Kafka Service
kubectl get svc -l app=kafka

# 查看StatefulSet
kubectl get sts kafka
```

### 进入Kafka容器执行命令

```powershell
# 进入容器
kubectl exec -it kafka-0 -- /bin/bash
```
**在容器中执行命令**
```bash
# 创建 Topic
/opt/kafka/bin/kafka-topics.sh --create --topic test-topic --partitions 3 --replication-factor 3 --bootstrap-server localhost:9092

# 查看 Topic 列表
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 查看 Topic 详情
/opt/kafka/bin/kafka-topics.sh --describe --topic test-topic --bootstrap-server localhost:9092

# 生产消息
/opt/kafka/bin/kafka-console-producer.sh --topic test-topic --bootstrap-server localhost:9092

# 消费消息
/opt/kafka/bin/kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092 --from-beginning
```

### 直接执行Kafka命令（无需进入容器）

```powershell
# 创建 Topic（直接执行）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-topics.sh --create --topic test-topic --partitions 3 --replication-factor 3 --bootstrap-server localhost:9092

# 查看 Topic 列表（直接执行）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 查看 Topic 详情（直接执行）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-topics.sh --describe --topic test-topic --bootstrap-server localhost:9092

# 删除 Topic（直接执行）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-topics.sh --delete --topic test-topic --bootstrap-server localhost:9092

# 查看 Broker 信息
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# 查看消费者组
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh --list --bootstrap-server localhost:9092

# 非交互式生产消息（通过echo管道）
echo "Hello Kafka" | kubectl exec -i kafka-0 -- /opt/kafka/bin/kafka-console-producer.sh --topic test-topic --bootstrap-server localhost:9092

# 批量生产测试消息（PowerShell）
for ($i = 1; $i -le 10; $i++) {
  "Message $i" | kubectl exec -i kafka-0 -- /opt/kafka/bin/kafka-console-producer.sh --topic test-topic --bootstrap-server localhost:9092
}

# 消费消息（从开头消费）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092 --from-beginning --max-messages 10

# 消费消息并保存到文件
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092 --from-beginning > messages.txt

# 后台消费（持续消费）
kubectl exec kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092 &
```

### 端口转发访问Kafka

```powershell
# 转发到Service（推荐）
kubectl port-forward svc/kafka-nodeport 9092:9094

# 转发到Pod, 每个broker一个端口转发,才能访问到对应的broker
# 使用LoadBalancer Service端口，就不用转发所有端口了
kubectl port-forward -n default pod/kafka-0 9094:9094

kubectl port-forward -n default pod/kafka-1 9095:9094

kubectl port-forward -n default pod/kafka-2 9096:9094
```

### 查看Kafka日志

```powershell
# 查看单个Pod日志
kubectl logs kafka-0
kubectl logs kafka-0 -f

# 查看多个Pod日志
kubectl logs -l app=kafka
```