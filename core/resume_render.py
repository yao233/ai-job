#!/usr/bin/env python3
"""中文简历 PDF 渲染引擎 (V7 验证)

纯 Python + reportlab + macOS 系统字体,零外部依赖。
用法:
  python3 core/resume_render.py --name "张三" --title "后端工程师" --email "zhangsan@example.com" \
      --phone "138-0000-0000" --summary "..." --sections '{"教育":"...","经历":"..."}' \
      --output out/test_resume.pdf

后续接入 LLM 生成 JSON 简历数据后,此脚本只做"数据 -> 一页 PDF"的渲染。
"""
import argparse
import json
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# 中文字体候选(macOS / Windows / Linux),按优先级
FONT_CANDIDATES = [
    # Windows
    ("C:/Windows/Fonts/msyh.ttc", 0, "MSYH"),
    ("C:/Windows/Fonts/msyhbd.ttc", 0, "MSYH-Bold"),
    ("C:/Windows/Fonts/simhei.ttf", 0, "SimHei"),
    ("C:/Windows/Fonts/simsun.ttc", 0, "SimSun"),
    # macOS
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0, "STHeiti-Medium"),
    ("/System/Library/Fonts/STHeiti Light.ttc", 0, "STHeiti-Light"),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0, "HiraginoSansGB"),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0, "Songti"),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0, "ArialUnicode"),
    # Linux (常见发行版)
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0, "WQYMicrohei"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0, "NotoSansCJK"),
]


def register_font() -> str:
    """注册第一个可用的中文字体,返回字体名"""
    for path, subfont, name in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                print(f"[font] using {path} (subfont {subfont}) as '{name}'")
                return name
            except Exception as e:
                print(f"[font] {path} failed: {e}")
    raise RuntimeError("no usable CJK font found")


def render(data: dict, output: str) -> None:
    font = register_font()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title=data.get("name", "简历"),
    )
    styles = {
        "name": ParagraphStyle("name", fontName=font, fontSize=20, leading=26, spaceAfter=2),
        "contact": ParagraphStyle("contact", fontName=font, fontSize=9.5, leading=13, textColor="#555555"),
        "section": ParagraphStyle("section", fontName=font, fontSize=12.5, leading=16,
                                  spaceBefore=8, spaceAfter=3, textColor="#1a5fb4"),
        "body": ParagraphStyle("body", fontName=font, fontSize=10.5, leading=15.5, alignment=TA_LEFT),
        "bullet": ParagraphStyle("bullet", fontName=font, fontSize=10.5, leading=15,
                                 leftIndent=8, bulletIndent=0, spaceAfter=1),
    }
    story = []
    # 姓名 + 标题
    title_line = data.get("name", "")
    if data.get("title"):
        title_line += f"  ·  {data['title']}"
    story.append(Paragraph(title_line, styles["name"]))
    # 联系方式
    contact_parts = []
    for k in ("email", "phone", "location", "github"):
        if data.get(k):
            contact_parts.append(f"{k}: {data[k]}")
    if contact_parts:
        story.append(Paragraph("  |  ".join(contact_parts), styles["contact"]))
    # 一句话简介
    if data.get("summary"):
        story.append(Paragraph(f"<b>{data['summary']}</b>", styles["body"]))
    # 技能
    if data.get("skills"):
        story.append(Paragraph("技能", styles["section"]))
        story.append(Paragraph(" · ".join(data["skills"]), styles["body"]))
    # 自定义区块:教育/经历/项目等
    for section_title, content in (data.get("sections") or {}).items():
        story.append(Paragraph(section_title, styles["section"]))
        if isinstance(content, list):
            for item in content:
                story.append(Paragraph(item, styles["body"]))
        else:
            for line in str(content).split("\n"):
                story.append(Paragraph(line, styles["body"]))
    doc.build(story)
    print(f"[render] OK -> {output} ({os.path.getsize(output)} bytes)")


def main():
    ap = argparse.ArgumentParser(description="中文简历 PDF 渲染")
    ap.add_argument("--name", default="张三")
    ap.add_argument("--title", default="后端工程师")
    ap.add_argument("--email", default="zhangsan@example.com")
    ap.add_argument("--phone", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--skills", default="")
    ap.add_argument("--sections", default="{}", help='JSON: {"教育":"...","经历":"..."} 或列表')
    ap.add_argument("--output", default="out/resume.pdf")
    args = ap.parse_args()
    try:
        sections = json.loads(args.sections)
    except json.JSONDecodeError:
        sections = {}
    data = {
        "name": args.name, "title": args.title, "email": args.email,
        "phone": args.phone, "location": args.location, "summary": args.summary,
        "skills": [s.strip() for s in args.skills.split(",") if s.strip()],
        "sections": sections,
    }
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    render(data, args.output)


if __name__ == "__main__":
    main()
