---
title: obsidian使用群晖Nas多端同步
date: 2025-07-13T15:29:35+08:00
tags:
  - obsidian
---
### mac和widows

使用Synology Drive 直接同步obsidian文件夹，简单方便。
### ios端

由于ios的限制，没有办法直接用icloud和存放在Nas上的文件进行同步。所以使用webdav进行同步。
1. ios端安装obsidian然后安装插件remotely Save
2. 群晖Nas 安装webdav server 启动http或者https
3. 使用ip `192.168.x.x:5005/yourFolderName` 账号 密码 
	在ios插件中登陆（如果没有公网ip是不能再非家庭wifi的情况同步，除非弄穿透，不过在家里能够同步已经能够满足我的使用场景）
### 2025.08.31更新

同步总是有问题，最终切换到icould。