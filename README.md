# AI-JOB · CN Edition

> 一个面向 **2027 届中国校招** 的 AI 求职工作流：7 维 JD 评估 + JD 定制简历（docx 排序与中文 PDF 渲染）+ 申请进度追踪 + 一键本地看板。

把「求职海投」变成「按岗位族的精准批量投递」：Agent 跑 10 步流程（从画像到追踪），岗位族预设一键切换排序，简历只重排不虚构，所有材料与个人数据默认本地化、不入库。

---

## 它解决什么问题

应届求职最常见的三个坑，这套工作流都管：

1. **海投低、命中低** —— 一份通用简历投遍全网，回复率惨不忍睹。**JD 评估**打分，按相关性排序再决定投不投。
2. **简历千篇一律** —— HR 一眼看出是模板产物。**针对每个 JD 重排经历顺序**：嵌入式岗把简易示波器放第一，HR 岗把凌凯实习提到最前。
3. **过程混乱** —— 投了哪些、面到哪轮全靠脑记。**本地 CSV 看板** + 7 天日历，零网络、零构建。

## 五分钟跑起来

```bash
# 1. 安装唯一需要的 Python 依赖
pip install reportlab

# 2. 把你的简历放进 my-materials/（已在 .gitignore，不会被推上去）
cp "~/简历/西安邮电大学-姚康豪.docx" my-materials/

# 3. 启动看板（Windows）
dashboard\start-dashboard.bat
# → http://localhost:8420/dashboard.html

# 4. 按 JD 定制简历（内置 8 个岗位族预设）
python core/tailor_resume.py --list-roles
python core/tailor_resume.py --role firmware_chip -o out/紫光同芯.docx
python core/tailor_resume.py --role quality      -o out/质量岗.docx
python core/tailor_resume.py --role hr           -o out/人力资源岗.docx
```

启用 AI Agent（Claude Code / Codex / Cursor）后只要说一句：
「**按 SKILL.md 初始化我的求职工作流**」——Agent 会引导你填画像、跑 7 维评估、出定制简历、跟踪进度，全程不虚构、不自动提交。

## 核心能力

### 1. 7 维 JD 评估（中国校招专属）

`knowledge/evaluation_framework_cn.md` 是 SKILL.md 第 3 步筛选环节的**唯一评分标准**：

| 维度 | 权重 | 评估什么 |
|------|------|----------|
| 技能匹配 | 30% | required / preferred 命中与缺口 |
| 经验匹配 | 25% | 年限、方向、独立交付能力 |
| 文化匹配 | 15% | 画像行为 vs JD 描述的工作风格 |
| 薪资结构 | 10% | 总包折算与画像期望对标 |
| 工作强度 | 10% | 大小周 / 加班信号 / on-call 词 |
| 稳定性 | 5% | 融资、裁员、五险一金线索 |
| 通勤城市 | 5% | base 匹配、远程可能性 |

任意 **Deal-breaker**（外包、996、硬性技能缺口）命中 → 总分强制 ≤30 直接跳过。评估分数写入 `job_pool.csv` 的 `evaluation_score` 列，看板里一眼能排序。

### 2. JD 定制简历（基于现有 docx，不动版式）

`core/tailor_resume.py` —— **只重排不虚构**：

- 项目经历按岗位族相关性重排（如嵌入式岗：示波器→光功率计→烟雾报警→点光源追踪）
- 技能条目按相关性排序
- **非技术岗自动把实习经历置顶**（HR/PM/质量/供应链/销售都靠实习 + 社团经历说话）
- 严格保留你原 docx 的版式（段间距、字体、表格、浮动文本框）
- 内置 8 个岗位族预设：`embedded`、`firmware_chip`、`hardware`、`quality`、`supply_chain`、`pm`、`hr`、`sales`

### 3. 中文简历 PDF 渲染

`core/resume_render.py` —— 纯 Python + reportlab + 系统字体，**零 LaTeX 依赖**：

```bash
python core/resume_render.py --name "姚康豪" --title "嵌入式软件工程师" \
    --email "..." --phone "..." --summary "..." \
    --skills "C语言,STM32,Keil" \
    --sections '{"教育":"...","项目":"..."}' \
    --output out/resume.pdf
```

Windows/macOS/Linux 全平台：自动检测系统中文字体（微软雅黑/黑体/苹方/Noto）。

### 4. 本地看板（零构建、零网络）

`dashboard/` 是纯静态 HTML + 一个 25 行的 Node 静态文件服务器。无需 `npm install`，双击 `start-dashboard.bat` 即可。CSV 实时读取，刷新即最新。

## 项目结构

```
SKILL.md                            Agent 10 步工作流 + 安全约定（从这里开始）
core/                               纯 Python 工具
  resume_render.py                  中文简历 → 一页 PDF（reportlab）
  tailor_resume.py                  JD 定制 docx（按岗位族预设重排，零虚构）
  jobs_search.py                    公开数据集职位搜索（可选）
  channel_list.py                   投递渠道/邮件模板生成
knowledge/
  evaluation_framework_cn.md        7 维 JD 评分（SKILL.md 唯一标准）
  methodology/                      画像/行为/写作/面试准备 等方法论
templates/                         Agent 引导式填写的空白模板
  candidate_profile.template.json   你的画像 + evaluation_inputs 节
  application_rules.template.md     优先/考虑/跳过/转交
  experience_bank.template.md       经历池，按岗位族标 强/中
  answer_bank.template.md           可复用真实回答
  resume_routing.template.md        不同 JD 用哪个简历版本
  dashboard-template/               空 CSV 看板
dashboard/                          实时本地看板
  dashboard.html                    看板界面
  server.js                         25 行静态文件服务器（无依赖）
  start-dashboard.bat / .sh        一键启动
  *.csv                             看板数据
references/                         Agent SOP
  setup-workflow.md                 初始化引导
  application-playbook.md           浏览器/ATS 操作手册
  safety-and-boundaries.md          隐私、知情同意、绝不自动化的事项
profile/                            【私有目录，已 .gitignore】你的画像、经历池、规则
out/                                【私有目录，已 .gitignore】生成的简历成品
data/jobs/                          【私有目录，已 .gitignore】岗位库
```

## 隐私保护（硬性约束）

本仓库**只发布工作流与模板**——**不发布任何个人数据**。

- `profile/` `out/` `data/jobs/` `my-materials/` 全部已在 `.gitignore`
- 推送前自动校验：`git status --short` 必须为空才会 `git push`
- 看板完全离线，所有 CSV 只在本地读写

填了你真实信息的工作副本请**保持私有**，不要把含手机/邮箱/家庭地址的 fork 公开。

## 8 个岗位族预设（`core/tailor_resume.py --list-roles`）

| role | 目标岗位 | 排序要点 |
|------|---------|---------|
| `embedded` | 嵌入式软件工程师 | 示波器→光功率计→烟雾报警→点光源 |
| `firmware_chip` | 芯片公司嵌入式岗 | 同上 + EDA/仪器技能提前 |
| `hardware` | 硬件工程师 | EDA/仪器置顶 + 实习经历置顶 |
| `quality` | 硬件测试/质量 | 实习(100+ 板卡/可靠性)必置顶 |
| `supply_chain` | 供应链专员 | 实习(物料一致性检验)必置顶 |
| `pm` | 项目管理岗 | 实习推动整改/联调 + 社团经历 |
| `hr` | 人力资源岗 | 主要靠学生会/社团经历 |
| `sales` | 技术型销售/FAE | 实习 + TouchGFX 界面放前 |

每个预设的排序理由都写在脚本注释里，方便你根据自己的真实情况微调。

## 安全边界

Agent **绝不**：

- 猜测身份、工作资格、薪资等高敏感事实
- 绕过 CAPTCHA / Cloudflare / 反爬机制
- 自动用未知账号登录 / 2FA
- 编造经历、学历、作品集
- 把"已收藏"岗位算作"已投递"
- 在没你明示确认的情况下点最终提交

完整清单见 `references/safety-and-boundaries.md`。

## 上游与许可证

MIT License —— 见 `LICENSE`。

本仓库为以下三个开源项目的合并/改编：

- **[DanielPan12/JobHuntBot](https://github.com/DanielPan12/JobHuntBot)** — Agent 10 步工作流与本地看板（Yvonne He 的 *ApplyPilot* 改编）
- **[sunyet-01/ai-job-search-cn](https://github.com/sunyet-01/ai-job-search-cn)** — 7 维评估框架、纯 Python 工具
- **[MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)** — ai-job-search-cn 的上游

三者均 MIT。`LICENSE` 文件保留了三方原始版权声明 + 本改编版权行。
