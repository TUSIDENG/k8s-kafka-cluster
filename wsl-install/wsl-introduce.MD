# WSL 2 架构的虚拟机

* 共享轻量级虚拟机（Utility VM）： 所有的 WSL 2 发行版（Ubuntu, Debian 等）其实都运行在同一个轻量级 Hyper-V 虚拟机里。

* 共享网络栈： 它们共享同一个 Linux 内核和同一个虚拟网络接口（通常是 eth0）。所以，当你在这两个不同的终端里运行 hostname -I 时，它们看到的其实是同一张网卡，拿到的自然就是同一个 IP（即 Hyper-V 虚拟交换机分配给这个 WSL 宿主机的 IP，比如你的 172.28.30.32）。

<span color="red">**wsl 虚拟机综合上不适合部署和演练k8s集群**</span>