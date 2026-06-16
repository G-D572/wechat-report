# 微信群聊分析报告

每日自动分析微信群聊记录，生成可视化数据报告网页。

## 工作方式

1. 用**留痕 (MemoTrace)** 导出微信聊天记录 → 保存为本仓库的 `messages.txt`
2. `git push` 到 GitHub
3. GitHub Actions **每天自动**运行分析脚本 → 生成网页
4. GitHub Pages 自动部署 → 获得一个公开网址

## 文件说明

```
wechat-report/
├── messages.txt          ← 聊天记录（你每天更新这个文件）
├── index.html            ← 自动生成的报告网页（不用手动改）
├── scripts/analyze.py    ← Python 分析脚本
└── .github/workflows/    ← GitHub Actions 自动运行配置
```

## 网址

部署后你的报告网页地址：
`https://<你的GitHub用户名>.github.io/wechat-report/`

## 每日操作

只需要两步：
1. 用留痕导出最新聊天记录，替换 `messages.txt`
2. `git add messages.txt && git commit -m "更新" && git push`
