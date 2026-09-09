#!/usr/bin/env python3
"""JD 定制简历生成器 v2

基于用户的原始简历模板(docx)，仅做「内容与顺序」层的定制，不动任何版式：
  - 项目经历区块按目标岗位的相关性重排（可选把实习经历提到最前）
  - 技能条目顺序调整
  - 抬头文本框里的目标岗位名改写

硬性原则：不新增、不删除、不改写任何经历与技术细节，只做取舍之外的重排。
如确需改写文本，必须让用户确认后手动加入 TEXT_OVERRIDES。

用法：
  python tailor_resume.py                              # 用默认 role 生成到 out/
  python tailor_resume.py --role quality --list-roles
  python tailor_resume.py --role pm --out "E:/jianli/out/xx.docx"
  python tailor_resume.py --role embedded --title "嵌入式软件工程师"
"""

import argparse
import re
import shutil
import sys
import zipfile

from docx import Document

TEMPLATE = r"E:/jianli/西安邮电大学--姚康豪.docx"
DEFAULT_OUT_DIR = r"E:/jianli/out"

# ---------- 模板段落索引（已核实，勿随意改；改模板后用 --inspect 重新确认） ----------
IDX = {
    "project_header": 21,          # "项目经历"
    "skill_bullets": [12, 13, 14, 15, 16, 17],   # 技能 1~6
    "internship": (35, 37),        # 凌凯电子：标题 + 产品测试 + 协助排故
    "projects": {                  # 每个项目 = [起始, 结束]（含 项目描述 + 工作内容）
        "烟雾报警": (22, 24),
        "光功率计": (26, 28),
        "简易示波器": (29, 31),
        "点光源": (32, 34),
    },
}

# ---------- 岗位族预设 ----------
# project_order: 项目排列顺序；internship_first: 是否把实习提到项目区最前
# skills: 技能原编号(1-based)的新顺序；title: 抬头默认文案(不含地点)
ROLE_PRESETS = {
    "embedded": {  # 嵌入式 / 固件
        "title": "嵌入式软件工程师",
        "projects": ["简易示波器", "光功率计", "烟雾报警", "点光源"],
        "skills": [1, 2, 4, 5, 3, 6],
        "internship_first": False,
        "hint": "外设同步采样/触发算法/分层架构最能证明固件能力，示波器置顶",
    },
    "firmware_chip": {  # 芯片公司嵌入式软/硬件
        "title": "嵌入式软件工程师",
        "projects": ["简易示波器", "光功率计", "烟雾报警", "点光源"],
        "skills": [1, 2, 4, 5, 3, 6],
        "internship_first": False,
        "hint": "与 embedded 相同顺序，另把 EDA 与仪器技能提前，凸显软硬件双栖能力",
    },
    "hardware": {  # 硬件工程师 / PCB / 电路
        "title": "硬件工程师",
        "projects": ["简易示波器", "点光源", "烟雾报警", "光功率计"],
        "skills": [4, 5, 1, 2, 3, 6],
        "internship_first": True,
        "hint": "EDA 与仪器排到技能最前，实习(100+板卡/改板回归)提到项目区首位",
    },
    "quality": {  # 质量 / 测试 / 可靠性
        "title": "硬件测试工程师",
        "projects": ["烟雾报警", "简易示波器", "光功率计", "点光源"],
        "skills": [5, 4, 1, 3, 2, 6],
        "internship_first": True,
        "hint": "实习经历是核心卖点(可靠性/台账/闭环)，必须置顶",
    },
    "supply_chain": {  # 供应链 / 物料 / 计划
        "title": "供应链专员",
        "projects": ["烟雾报警", "点光源", "光功率计", "简易示波器"],
        "skills": [4, 5, 3, 1, 2, 6],
        "internship_first": True,
        "hint": "实习里的物料一致性检验/装配工艺检验是唯一相关经历，务必置顶",
    },
    "pm": {  # 项目经理 / 项目管培
        "title": "项目管理岗",
        "projects": ["烟雾报警", "简易示波器", "光功率计", "点光源"],
        "skills": [6, 2, 1, 4, 5, 3],
        "internship_first": True,
        "hint": "强调跨模块联调推进(整机系统联调/推动整改)+ 学生会/社团经历",
    },
    "hr": {  # 人力资源
        "title": "人力资源岗",
        "projects": ["烟雾报警", "点光源", "光功率计", "简易示波器"],
        "skills": [6, 2, 5, 4, 1, 3],
        "internship_first": True,
        "hint": "主要靠自我评价里的学生会成员/社团部长；技术项保持最低优先级",
    },
    "sales": {  # 技术类销售 / FAE
        "title": "技术型销售工程师",
        "projects": ["光功率计", "烟雾报警", "简易示波器", "点光源"],
        "skills": [3, 5, 1, 4, 2, 6],
        "internship_first": True,
        "hint": "强调产品化/客户侧物料-坏品处理视角，实习与技术广度优先",
    },
}

# 可选：确需改写文本时在此登记（默认关闭，避免虚构）
TEXT_OVERRIDES = {}


def inspect(template):
    doc = Document(template)
    print(f"模板段落总数: {len(doc.paragraphs)}")
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t:
            print(f"  [{i:02d}] <{p.style.name}> {t[:50]}")


def tailor(template, out, role, title=None, keep_title=False):
    preset = ROLE_PRESETS[role]
    shutil.copyfile(template, out)
    doc = Document(out)
    ps = doc.paragraphs

    # 1) 项目重排（逐段插入并实时推进锚点，保证块内与块间都保序）
    anchor = ps[IDX["project_header"]]._p
    blocks = list(IDX["projects"].items())
    if preset["internship_first"]:
        s, e = IDX["internship"]
        blocks = [("__internship__", (s, e))] + blocks

    order = (["__internship__"] if preset["internship_first"] else []) + preset["projects"]
    for name in order:
        s, e = dict(blocks)[name]
        for i in range(s, e + 1):
            node = ps[i]._p
            anchor.addnext(node)
            anchor = node

    # 2) 技能重排
    skill_map = {n: IDX["skill_bullets"][n - 1] for n in range(1, 7)}
    anchor = ps[IDX["skill_bullets"][0]]._p.getprevious()
    for n in preset["skills"]:
        node = ps[skill_map[n]]._p
        anchor.addnext(node)
        anchor = node

    doc.save(out)

    return out


def main():
    ap = argparse.ArgumentParser(description="按 JD/岗位族定制简历（保持原 docx 版式）")
    ap.add_argument("--role", default="embedded", help="岗位族预设键名")
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default=None, help="抬头目标岗位名（默认不写地点）")
    ap.add_argument("--keep-title", action="store_true", help="不改抬头")
    ap.add_argument("--list-roles", action="store_true")
    ap.add_argument("--inspect", action="store_true", help="打印模板段落索引")
    args = ap.parse_args()

    if args.inspect:
        inspect(args.template)
        return
    if args.list_roles:
        for k, v in ROLE_PRESETS.items():
            print(f"{k:14s} {v['title']:12s} | {v['hint']}")
        return
    if args.role not in ROLE_PRESETS:
        print(f"[error] 未知 role: {args.role}。可用：{', '.join(ROLE_PRESETS)}")
        sys.exit(1)

    out = args.out or f"{DEFAULT_OUT_DIR}/西安邮电大学-姚康豪-{ROLE_PRESETS[args.role]['title']}.docx"
    tailor(args.template, out, args.role, args.title, args.keep_title)

    check = Document(out)
    print(f"[ok] 已生成: {out}  (段落数 {len(check.paragraphs)})")
    print(f"[role] {args.role} — {ROLE_PRESETS[args.role]['hint']}")
    print("--- 项目/经历顺序 ---")
    for p in check.paragraphs:
        t = p.text.strip()
        if t.startswith(("2026.", "2025.")):
            print("   ", t[:46])


if __name__ == "__main__":
    main()
