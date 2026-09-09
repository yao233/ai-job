#!/usr/bin/env python3
"""投递渠道清单生成器 (K6)

对一份 JD 评估后,输出「投递行动清单」——用户手动执行的渠道清单。
AI 只生成材料,绝不代替用户执行任何对外动作。

用法:
  python3 core/channel_list.py --company "Stripe" --role "Machine Learning Engineer" \
      --url "https://stripe.com/jobs/..." --official_url "https://stripe.com/jobs" \
      --email "hr@example.com" --output out/channels_stripe.md
"""
import argparse
import os
import urllib.parse
from datetime import date, timedelta
from pathlib import Path


def build_platform_links(company: str, role: str) -> list:
    """生成国内主流招聘平台的搜索链接(用户自己点开投递,不自动投)"""
    q = f"{company} {role}"
    enc = urllib.parse.quote(q)
    return [
        ("BOSS直聘", f"https://www.zhipin.com/web/geek/job?query={enc}&city=100010000"),
        ("猎聘", f"https://www.liepin.com/zhaopin/?key={enc}"),
        ("智联招聘", f"https://sou.zhaopin.com/?jl=530&kw={enc}"),
        ("前程无忧 51job", f"https://we.51job.com/pc/search?keyword={enc}&searchType=2&sortType=0"),
    ]


def build_followup_plan(company: str, role: str) -> list:
    """跟进计划:时间点 + 话术草稿(用户自己发送)"""
    today = date.today()
    return [
        (f"投递当天 ({today})",
         f"您好,我对贵司 {role} 岗位非常感兴趣,已通过官网投递简历,期待与您进一步沟通。"),
        (f"投递后 5 天 ({today + timedelta(days=5)})",
         f"您好,冒昧跟进一下 {role} 岗位的进展。我对这个岗位的理解是[一句话],如果有机会,希望能和团队聊聊。"),
        (f"投递后 12 天 ({today + timedelta(days=12)})",
         "您好,想再次确认一下该岗位是否还在招聘。若已招满也感谢您的时间,期待未来有机会合作。"),
    ]


def main():
    ap = argparse.ArgumentParser(description="投递渠道清单生成器")
    ap.add_argument("--company", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--url", default="", help="JD 原文链接")
    ap.add_argument("--official_url", default="", help="公司官网 careers 页")
    ap.add_argument("--email", default="", help="JD 中标注的官方招聘邮箱(可选)")
    ap.add_argument("--output", default="out/channels.md")
    args = ap.parse_args()

    lines = []
    lines.append(f"# 投递行动清单:{args.company} · {args.role}")
    lines.append("")
    lines.append(f"> 生成日期:{date.today()}  |  本清单仅提供渠道与材料,**投递动作由你手动完成**。")
    lines.append("")
    if args.url:
        lines.append(f"**JD 原文**:{args.url}")
    lines.append("")

    lines.append("## 1. 官方渠道(最优先)")
    lines.append("| 渠道 | 操作 |")
    lines.append("|---|---|")
    if args.official_url:
        lines.append(f"| 官网 careers 页 | 打开并搜索岗位 → 在线投递 [{args.official_url}]({args.official_url}) |")
    else:
        lines.append(f"| 官网 careers 页 | 搜索「{args.company} careers」→ 找到岗位页投递(建议优先于平台) |")
    if args.email:
        lines.append(f"| 官方招聘邮箱 | 使用下方邮件模板,发送至 {args.email}(自己发) |")
    lines.append("")

    lines.append("## 2. 平台渠道(按需选择)")
    lines.append("| 平台 | 搜索链接(点开→自己投) |")
    lines.append("|---|---|")
    for name, link in build_platform_links(args.company, args.role):
        lines.append(f"| {name} | [点此搜索]({link}) |")
    lines.append("")

    lines.append("## 3. 邮件模板(如走官方邮箱)")
    lines.append("```")
    lines.append(f"主题:申请 {args.role} - [你的姓名]")
    lines.append("")
    lines.append(f"尊敬的招聘团队:")
    lines.append("")
    lines.append(f"您好!我是[你的姓名],目前[你的状态,如:从事 X 年 Y 领域工作]。")
    lines.append(f"看到贵司正在招聘 {args.role},我非常感兴趣。")
    lines.append("[这里写 2-3 句与岗位最相关的经历/亮点]")
    lines.append("")
    lines.append("我的简历已附上,期待有机会进一步交流。")
    lines.append("")
    lines.append("此致")
    lines.append("敬礼")
    lines.append("[你的姓名] | [电话] | [邮箱]")
    lines.append("```")
    lines.append("")

    lines.append("## 4. 跟进计划(自己发,最多 2 次)")
    for when, draft in build_followup_plan(args.company, args.role):
        lines.append(f"- **{when}**:{draft}")
    lines.append("")

    lines.append("## 5. 记录投递结果")
    lines.append("投递后回到产品更新追踪表:渠道、日期、状态(已投/笔试/面试/offer/拒)。")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"[channels] OK -> {args.output}")


if __name__ == "__main__":
    main()
