# kubectl 常用命令速查

## 目录

1. [基础命令](#基础命令)
2. [资源管理](#资源管理)
3. [集群管理](#集群管理)
4. [调试诊断](#调试诊断)
5. [配置管理](#配置管理)
6. [Kafka专用命令](#kafka专用命令)

---

## 基础命令

```bash
# 查看kubectl版本
kubectl version

# 查看集群信息
kubectl cluster-info

# 获取帮助
kubectl --help
kubectl <command> --help

# 查看资源列表
kubectl get <resource>

# 查看资源详情
kubectl describe <resource> <name>

# 创建资源
kubectl apply -f <file.yaml>

# 删除资源
kubectl delete -f <file.yaml>
kubectl delete <resource> <name>
```

---

## 资源管理

### Pod操作

```bash
# 查看Pod列表
kubectl get pods
kubectl get pods -o wide  # 显示更多信息
kubectl get pods -n <namespace>  # 指定命名空间
kubectl get pods -w  # 实时监控pod状态

# 查看Pod详情
kubectl describe pod <pod-name>

# 进入Pod执行命令
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -- <command>

# 查看Pod日志
kubectl logs <pod-name>
kubectl logs <pod-name> -f  # 实时日志
kubectl logs <pod-name> --tail=50  # 最后50行
kubectl logs <pod-name> -p  # 查看已终止Pod的日志

# 删除Pod（StatefulSet会自动重建）
kubectl delete pod <pod-name>
```

### Service操作

```bash
# 查看Service列表
kubectl get svc
kubectl get service

# 查看Service详情
kubectl describe svc <service-name>

# 端口转发（本地访问集群内服务）
kubectl port-forward svc/<service-name> <local-port>:<remote-port>
kubectl port-forward pod/<pod-name> <local-port>:<remote-port>
```

### StatefulSet操作

```bash
# 查看StatefulSet列表
kubectl get statefulset
kubectl get sts

# 查看StatefulSet详情
kubectl describe statefulset <sts-name>

# 扩缩容
kubectl scale statefulset <sts-name> --replicas=<num>

# 更新StatefulSet
kubectl apply -f <file.yaml>
```

### ConfigMap & Secret

```bash
# 查看ConfigMap
kubectl get configmap
kubectl describe configmap <name>

# 查看Secret
kubectl get secret
kubectl describe secret <name>

# 创建ConfigMap
kubectl create configmap <name> --from-file=<file>
kubectl create configmap <name> --from-literal=key=value

# 创建Secret
kubectl create secret generic <name> --from-literal=key=value
```

---

## 集群管理

```bash
# 查看节点状态
kubectl get nodes
kubectl describe node <node-name>

# 查看命名空间
kubectl get namespaces
kubectl get ns

# 创建命名空间
kubectl create namespace <name>

# 设置默认命名空间
kubectl config set-context --current --namespace=<name>

# 查看所有资源
kubectl get all
kubectl get all -n <namespace>

# 标签管理
kubectl label pods <pod-name> key=value
kubectl get pods -l <label-key>=<label-value>
```

---

## 调试诊断

```bash
# 查看资源事件
kubectl get events
kubectl get events -w  # 实时监控

# 查看资源yaml定义
kubectl get <resource> <name> -o yaml
kubectl get <resource> <name> -o json

# 检查资源配置
kubectl explain <resource>
kubectl explain pod.spec.containers

# 验证yaml语法
kubectl apply --dry-run=client -f <file.yaml>

# 查看API资源
kubectl api-resources
kubectl api-versions

# 强制删除资源
kubectl delete <resource> <name> --grace-period=0 --force
```

---

## 配置管理

```bash
# 查看当前上下文
kubectl config get-contexts

# 切换上下文
kubectl config use-context <context-name>

# 查看kubeconfig配置
kubectl config view

# 添加集群配置
kubectl config set-cluster <name> --server=<url>

# 添加用户配置
kubectl config set-credentials <name> --token=<token>

# 添加上下文
kubectl config set-context <name> --cluster=<cluster> --user=<user> --namespace=<ns>
```

---

## 常用别名（可选）

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgn='kubectl get namespaces'
alias kd='kubectl describe'
alias ka='kubectl apply -f'
alias kdel='kubectl delete'
```

---

## 快捷键

| 操作 | 快捷键 |
|------|--------|
| 自动补全 | `Tab` |
| 退出编辑 | `Esc` |
| 搜索 | `/pattern` |
| 翻页 | `PgUp/PgDn` |
| 退出日志 | `Ctrl+C` |
