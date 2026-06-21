#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 Shadowrocket lazy_group.conf 中策略组的 policy-select-name。

逻辑：
  1. 校验 196-212 行确实是策略组定义（防上游结构变化导致改错位置）
  2. 将 196-212 行强制覆盖为 TARGET_BLOCK 模板（屏蔽上游对这些行的改动）
  3. 在 TARGET_BLOCK 上应用 POLICY_OVERRIDES，替换指定键的 policy-select-name

退出码：
  0  修改成功
  1  行号校验失败（上游结构变了，需人工检查）
  2  文件不存在
"""
import re
import sys
from pathlib import Path

# 196-212 行的目标内容模板（17 行）
TARGET_BLOCK = """AI = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
YouTube = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Netflix = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Disney+ = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Max = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
TikTok = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Spotify = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Telegram = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Twitter = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Facebook = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
PayPal = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
Amazon = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
苹果服务 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=DIRECT
谷歌服务 = select,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
微软服务 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY
哔哩哔哩 = select,DIRECT,PROXY,香港节点,台湾节点,policy-select-name=DIRECT
游戏平台 = select,DIRECT,PROXY,香港节点,台湾节点,日本节点,新加坡节点,韩国节点,美国节点,policy-select-name=PROXY"""

# policy-select-name 对应表（仅这些键会被修改，其余保持模板原值）
POLICY_OVERRIDES = {
    "AI": "美国节点",
    "YouTube": "美国节点",
    "Netflix": "新加坡节点",
    "Disney+": "美国节点",
    "Max": "美国节点",
    "TikTok": "美国节点",
    "Spotify": "美国节点",
    "谷歌服务": "美国节点",
}

# 行号范围（1-indexed）
START_LINE = 196  # AI = select,...
END_LINE = 212    # 游戏平台 = select,...


def apply_overrides(block: str, overrides: dict) -> str:
    """对模板块应用 policy-select-name 覆盖。"""
    out = []
    for line in block.splitlines():
        if " = " in line:
            key = line.split(" = ", 1)[0].strip()
            if key in overrides:
                line = re.sub(
                    r"policy-select-name=[^,]+",
                    f"policy-select-name={overrides[key]}",
                    line,
                )
        out.append(line)
    return "\n".join(out)


def main() -> int:
    conf_path = Path("automation/shadowrocket/lazy_group.conf")
    if not conf_path.exists():
        print(f"ERROR: {conf_path} not found", file=sys.stderr)
        return 2

    text = conf_path.read_text(encoding="utf-8")
    # 用 splitlines(keepends=False) 再手动保留换行风格
    lines = text.split("\n")
    # 去掉末尾空行（文件以 \n 结尾时 split 会产生一个空串）
    trailing_newline = text.endswith("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines.pop()

    # 行号校验（1-indexed → 0-indexed）
    start_idx = START_LINE - 1
    end_idx = END_LINE - 1

    if len(lines) < END_LINE:
        print(
            f"ERROR: file has only {len(lines)} lines, expected >= {END_LINE}",
            file=sys.stderr,
        )
        return 1

    expected_first_key = "AI"
    expected_last_key = "游戏平台"
    if not lines[start_idx].startswith(f"{expected_first_key} = "):
        print(
            f"ERROR: line {START_LINE} is not '{expected_first_key} = ...': "
            f"got {lines[start_idx]!r}",
            file=sys.stderr,
        )
        return 1
    if not lines[end_idx].startswith(f"{expected_last_key} = "):
        print(
            f"ERROR: line {END_LINE} is not '{expected_last_key} = ...': "
            f"got {lines[end_idx]!r}",
            file=sys.stderr,
        )
        return 1

    # 生成最终块（模板 + 对应表覆盖）
    final_block = apply_overrides(TARGET_BLOCK, POLICY_OVERRIDES)
    final_block_lines = final_block.splitlines()

    if len(final_block_lines) != (END_LINE - START_LINE + 1):
        print(
            f"ERROR: TARGET_BLOCK has {len(final_block_lines)} lines, "
            f"expected {END_LINE - START_LINE + 1}",
            file=sys.stderr,
        )
        return 1

    # 替换 196-212 行
    new_lines = lines[:start_idx] + final_block_lines + lines[end_idx + 1 :]
    new_text = "\n".join(new_lines) + ("\n" if trailing_newline else "")

    if new_text == text:
        print("No changes needed (already up to date).")
        return 0

    conf_path.write_text(new_text, encoding="utf-8")

    # 报告改了哪些键
    changed = []
    for k, v in POLICY_OVERRIDES.items():
        changed.append(f"  {k} -> policy-select-name={v}")
    print(f"Modified {len(POLICY_OVERRIDES)} policy groups in lines {START_LINE}-{END_LINE}:")
    print("\n".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
