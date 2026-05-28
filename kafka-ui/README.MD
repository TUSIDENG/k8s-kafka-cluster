# Kafka UI
使用Kafka UI查看Kafka集群状态和操作。

## docker-compose
使用docker-compose部署Kafka UI。
```bash
docker-compose up -d
```
docker-compose方式部署,虽然能通过host.docker.internal访问Kafka UI。
但是不可用，会显示集群下线。

## k8s helm部署
使用k8s helm部署Kafka UI。

### 安装helm
```powershell
scoop install helm
```

### 1. 创建ConfigMap

**方式一：环境变量格式（推荐）**
```powershell
# 先创建namespace
kubectl create namespace kafka-ui

# 创建ConfigMap
kubectl create configmap kafka-ui-config `
  --from-literal=KAFKA_CLUSTERS_0_NAME=local `
  --from-literal=KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka-headless.default.svc.cluster.local:9092 `
  --namespace kafka-ui
```

**方式二：YAML配置文件格式**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-ui-config
  namespace: kafka-ui
data:
  config.yml: |-
    kafka:
      clusters:
        - name: local
          bootstrapServers: kafka-headless.default.svc.cluster.local:9092
```

### 2. 安装kafka-ui

**使用环境变量ConfigMap安装：**
```powershell
# 添加kafbat-ui helm仓库
helm repo add kafbat-ui https://kafbat.github.io/helm-charts

# 安装kafka-ui，引用已创建的ConfigMap
helm install kafka-ui kafbat-ui/kafka-ui `
  --namespace kafka-ui `
  --set existingConfigMap=kafka-ui-config
```

**使用YAML配置文件ConfigMap安装：**
```powershell
# 先应用ConfigMap
kubectl apply -f configmap.yaml

# 安装kafka-ui
helm install kafka-ui kafbat-ui/kafka-ui `
  --namespace kafka-ui `
  --set yamlApplicationConfigConfigMap.name=kafka-ui-config `
  --set yamlApplicationConfigConfigMap.keyName=config.yml
```

### 3. 访问kafka-ui

```powershell
# 方式一：直接端口转发到Service（推荐，更简单）
kubectl --namespace kafka-ui port-forward svc/kafka-ui 8080:8080

# 方式二：获取Pod名称，转发到Pod
$POD_NAME = (kubectl get pods --namespace kafka-ui -l "app.kubernetes.io/name=kafka-ui,app.kubernetes.io/instance=kafka-ui" -o jsonpath="{.items[0].metadata.name}")

kubectl --namespace kafka-ui port-forward $POD_NAME 8080:8080
```

访问 http://localhost:8080 即可看到Kafka集群界面。

### 4. 卸载

```powershell
helm uninstall kafka-ui -n kafka-ui
kubectl delete configmap kafka-ui-config -n kafka-ui
kubectl delete namespace kafka-ui
```