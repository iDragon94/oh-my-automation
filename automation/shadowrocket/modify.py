#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 Shadowrocket lazy_group.conf 中策略组的 policy-select-name。

设计：按键名定位，不依赖行号。
  - 扫描文件每一行，提取 `key = ...` 形式的键名
  - 若 key 在 TARGET_GROUPS 中，把整行替换为预计算好的最终行
    （模板行 + policy-select-name 覆盖）
  - 不在 TARGET_GROUPS 中的行（含上游新增的策略组）原样保留
  - 报告哪些目标键被替换、哪些在文件中未找到（上游可能删了/改名了）

退出码：
  0  成功（至少替换了一个键，或文件已是目标状态）
  1  文件结构异常（一个目标键都没找到，说明上游大改，需人工检查）
  2  文件不存在
"""
import re
import sys
from pathlib import Path

# ---- 配置区 ----

# 17 个策略组的模板行（policy-select-name 为默认值，未经 override）
TEMPLATE_LINES = {
    "AI":       "AI = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "YouTube":  "YouTube = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Netflix":  "Netflix = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Disney+":  "Disney+ = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Max":      "Max = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "TikTok":   "TikTok = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Spotify":  "Spotify = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Telegram": "Telegram = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Twitter":  "Twitter = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Facebook": "Facebook = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "PayPal":   "PayPal = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "Amazon":   "Amazon = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "苹果服务":  "苹果服务 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=DIRECT",
    "谷歌服务":  "谷歌服务 = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "微软服务":  "微软服务 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
    "哔哩哔哩":  "哔哩哔哩 = select,DIRECT,PROXY,香港节点,台湾节点,policy-select-name=DIRECT",
    "游戏平台":  "游戏平台 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY",
}

# policy-select-name 对应表（仅这些键会被覆盖，其余保持模板默认值）
POLICY_OVERRIDES = {
    "AI":      "美国节点",
    "YouTube": "美国节点",
    "Netflix": "新加坡节点",
    "Disney+": "美国节点",
    "Max":     "美国节点",
    "TikTok":  "美国节点",
    "Spotify": "美国节点",
    "谷歌服务": "美国节点",
}

# ---- 预计算：每个目标键的最终行（模板 + override 应用后） ----

def _build_final_lines() -> dict:
    final = {}
    for key, tmpl in TEMPLATE_LINES.items():
        if key in POLICY_OVERRIDES:
            tmpl = re.sub(
                r"policy-select-name=[^,]+",
                f"policy-select-name={POLICY_OVERRIDES[key]}",
                tmpl,
            )
        final[key] = tmpl
    return final

FINAL_LINES = _build_final_lines()


# ---- 主逻辑 ----

def _extract_key(line: str) -> str | None:
    """从 `key = value` 行提取 key；非赋值行返回 None。"""
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#") or stripped.startswith("["):
        return None
    if " = " not in line:
        return None
    return line.split(" = ", 1)[0].strip()


def main() -> int:
    conf_path = Path("automation/shadowrocket/lazy_group.conf")
    if not conf_path.exists():
        print(f"ERROR: {conf_path} not found", file=sys.stderr)
        return 2

    text = conf_path.read_text(encoding="utf-8-sig")
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines.pop()

    replaced_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        key = _extract_key(line)
        if key and key in FINAL_LINES:
            new_lines.append(FINAL_LINES[key])
            replaced_keys.add(key)
        else:
            new_lines.append(line)

    # 汇总
    missing_keys = [k for k in FINAL_LINES if k not in replaced_keys]

    if not replaced_keys:
        print(
            "ERROR: 0 target groups found in file — upstream structure may have "
            "changed drastically. Manual inspection required.",
            file=sys.stderr,
        )
        return 1

    new_text = "\n".join(new_lines) + ("\n" if trailing_newline else "")

    if new_text == text:
        print(f"No changes needed ({len(replaced_keys)} groups already up to date).")
    else:
        conf_path.write_text(new_text, encoding="utf-8", newline="")
        print(f"Replaced {len(replaced_keys)}/{len(FINAL_LINES)} policy groups:")
        for k in FINAL_LINES:
            mark = "OK " if k in replaced_keys else "-- "
            override = f" -> {POLICY_OVERRIDES[k]}" if k in POLICY_OVERRIDES else ""
            print(f"  {mark}{k}{override}")

    if missing_keys:
        print(
            f"WARNING: {len(missing_keys)} target group(s) not found in file "
            f"(upstream may have removed/renamed them): {', '.join(missing_keys)}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
