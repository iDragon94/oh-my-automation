# oh-my-automation

个人自动化脚本与定时任务集合。

## 目录结构

```
automation/
  shadowrocket/      # Shadowrocket 规则配置（每日自动更新）
    lazy_group.conf
```

## 自动更新

通过 GitHub Actions 定时拉取并处理文件，详见 `.github/workflows/`。
