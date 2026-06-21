# oh-my-automation

个人自动化脚本与定时任务集合。

## 目录结构

```
automation/
  shadowrocket/      # Shadowrocket 规则配置（每日自动更新）
    lazy_group.conf
    modify.py
```

## 自动更新

通过 GitHub Actions 定时拉取并处理文件，详见 `.github/workflows/daily-update.yml`：
每天 8:30（HKT）拉取上游最新 `lazy_group.conf`，运行 `modify.py` 按个人偏好修改
部分策略组的 `policy-select-name`，有变化才提交回仓库。

## 来源与许可

`automation/shadowrocket/lazy_group.conf` 基于
[johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever)
的 `lazy_group.conf` 衍生，每日自动同步并按个人偏好修改以下策略组的默认选择节点：

| 策略组 | 默认选择节点 |
|---|---|
| AI | 美国节点 |
| YouTube | 美国节点 |
| Netflix | 新加坡节点 |
| Disney+ | 美国节点 |
| Max | 美国节点 |
| TikTok | 美国节点 |
| Spotify | 美国节点 |
| 谷歌服务 | 美国节点 |

上游原始文件采用
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
许可发布。根据该协议要求，本衍生作品同样以 CC BY-SA 4.0 授权，
详见 [LICENSE](./LICENSE)。
