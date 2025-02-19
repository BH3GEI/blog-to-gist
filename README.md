# Blog to Gist Sync

自动将博客文章同步到 GitHub Gist 的工具。

## 功能

- 每6小时自动同步一次
- 支持手动触发同步
- 保持文章格式和元数据
- SEO 友好的 Gist 描述

## 配置

1. 在仓库的 Settings → Secrets and variables → Actions 中添加 `GIST_TOKEN`
2. Token 需要有 gist 权限
