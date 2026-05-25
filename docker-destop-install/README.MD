# 安装kind k8s集群
![kind-install](imgs/Kind_K8s_create_01.png)

# 部署k8s集群
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