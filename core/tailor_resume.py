#!/usr/bin/env python3
"""按 JD 定制简历：基于现有 docx 版式，仅做「内容重排 + 少量真实补充」，不动版式。"""
import shutil
import sys
import zipfile

from docx import Document

SRC = r"E:/jianli/西安邮电大学-姚康豪-嵌入式工程师.docx"
DST = r"E:/jianli/out/西安邮电大学-姚康豪-紫光同芯-嵌入式软件工程师.docx"
TARGET_TITLE = "嵌入式软件工程师（西安）"

# 原文件段落索引（已核实）
PROJ_HDR = 22
BLOCKS = {
    "烟雾报警": (23, 24),
    "光功率计": (25, 27),
    "简易示波器": (28, 29),
    "点光源": (30, 31),
}
SKILL_IDX = [12, 13, 14, 15, 16, 17]  # 技能六条

# 按紫光同芯（芯片 + 嵌入式软件）相关性重排
PROJ_ORDER = ["简易示波器", "光功率计", "烟雾报警", "点光源"]
SKILL_ORDER = [0, 1, 3, 4, 2, 5]  # 把 EDA/PCB 与仪器能力提到外设模块之前


def main():
    shutil.copyfile(SRC, DST)
    doc = Document(DST)
    ps = doc.paragraphs

    # 1) 项目重排
    anchor = ps[PROJ_HDR]._p
    for name in PROJ_ORDER:
        s, e = BLOCKS[name]
        for i in range(s, e + 1):  # 逐段插入，锚点始终更新到刚插入的节点，保序
            node = ps[i]._p
            anchor.addnext(node)
            anchor = node

    # 2) 技能重排
    anchor = ps[SKILL_IDX[0]]._p.getprevious()
    for k in SKILL_ORDER:
        node = ps[SKILL_IDX[k]]._p
        anchor.addnext(node)
        anchor = node

    doc.save(DST)

    # 3) 抬头：把浮动文本框里的岗位名换成目标岗位
    old_tag = "嵌入式工程师"
    with zipfile.ZipFile(DST) as z:
        names = z.namelist()
        xml = z.read("word/document.xml").decode("utf-8")
        others = {n: z.read(n) for n in names if n != "word/document.xml"}

    cnt = xml.count(old_tag)
    if cnt > 6:
        print(f"[warn] '{old_tag}' 出现 {cnt} 次，过于频繁，未替换抬头")
    else:
        xml = xml.replace(old_tag, TARGET_TITLE)
        print(f"[title] 替换抬头 {cnt} 处 -> {TARGET_TITLE}")

    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", xml.encode("utf-8"))
        for n, data in others.items():
            z.writestr(n, data)

    # 4) 校验输出的结构顺序
    check = Document(DST)
    print("\n=== 输出文件顺序校验 ===")
    for p in check.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if t.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "2026.", "2025.", "项目经历", "自我评价")):
            print(" ·", t[:52])


if __name__ == "__main__":
    main()
