# WSL 常用精简命令
## 实例管理
```powershell
# 查看所有WSL实例
wsl -l -v

# 关闭全部WSL
wsl --shutdown

# 注销删除实例
wsl --unregister 实例名

# 设置默认启动实例
wsl --set-default 实例名

# 切换默认WSL版本
wsl --set-version 实例名 2
```

## 启动登录
```powershell
# 启动默认实例
wsl

# 指定实例启动
wsl -d 实例名

# 指定用户登录
wsl -d 实例名 -u 用户名
```

## 导入导出迁移
```powershell
# 导出备份
wsl --export 实例名 备份文件.tar

# 导入自定义名称+路径
wsl --import 新名称 存放路径 备份.tar --version 2
```

## 系统相关
```powershell
# 查看WSL版本
wsl --version

# 开启WSL功能
wsl --install

# 设默认WSL2
wsl --set-default-version 2
```

## 快捷操作
```powershell
# 进入当前Windows目录
wsl cd .

# 挂载Windows磁盘
cd /mnt/c
```