---
title: obsidian发布blog流程
date: 2025-07-13
tags:
  - obsidian
---
1. 在obsidian posts文件夹下编写内容。
2. 使用posts-sync.py 同步文件到content，并且处理图片引用（使用Cursor生成，强烈推荐Cursor，非常好用）（python文件我也同步到git仓库，使用时注意修改文件夹路径）
3. git 提交刚刚的改动，触发action自动部署，done！