---
title: 这个blog的诞生
date: 2025-07-12T21:21:15+08:00
tags:
  - blog
---

1. 使用模版仓库[template-quartz](https://github.com/sosiristseng/template-quartz)，按照readme完成github.io页面deploy
2. 这时候是默认的样式，替换submodel
```bash
//克隆到本地
git clone --recursive https://github.com/ZenQ-Sun/Quartz.git
//去除旧的subModule
git submodule deinit quartz
git rm quartz
rm -rf .git/modules/quartz
//添加新的subModule
git submodule add https://github.com/jackyzha0/jackyzha0.github.io quartz

//最后提交你的改动
git add .
git commit -m "change subModule"
git push
```
3. 修改.github/workflows/ci.yml
```yml
cp quartz.config.ts quartz.layout.ts quartz
# 在这一行后添加清空 submodule 的 content 目录，只使用根目录的 content
rm -rf quartz/content/*

#提交改动，检查deploy是否成功
```
