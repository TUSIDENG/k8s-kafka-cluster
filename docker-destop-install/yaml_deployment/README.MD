# YAML 部署kafka集群

## 部署kafka集群
```bash
# 部署
kubectl apply -f kafka-3nodes.yaml

# 删除
kubectl delete -f kafka-3nodes.yaml

# 监控
kubectl get pods -w

# 查看pod kafka0详细信息
kubectl describe pod kafka-0
```

## 获取kafka服务信息

1. 获取kafka服务信息
```bash
# 查看服务
kubectl get svc

# 查看 Kafka 服务端口（应该显示 NodePort 9094）
kubectl get svc kafka-headless
```

2. 获取node ip
```bash
# 查看节点
kubectl get nodes -o wide
```

3. 转发node port
```bash
# 转发node port 9094 到本地 9092
# 可以通过 http://localhost:9092 访问 Kafka 服务
kubectl port-forward svc/kafka-nodeport 9092:9094
```

## 常见问题

#### 转发端口被占用，如何解决？
1. 查看占用端口的进程
```powershell
# 查看占用端口的进程
netstat -ano | findstr :9092
```

2. 杀死占用进程
```powershell
# 24480替换为实际占用端口的进程ID
taskkill /F /PID 24480
```