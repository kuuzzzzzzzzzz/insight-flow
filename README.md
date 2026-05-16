# InsightFlow｜智能数据洞察分析系统

## 项目介绍
InsightFlow 是一个通用 AI 数据分析 Agent 项目，支持用户通过自然语言提出分析问题，系统自动完成 SQL 生成、安全校验、数据查询、多图表展示和中文业务洞察生成。

一句话介绍：
基于自然语言交互的数据分析 Agent，支持自动生成 SQL、执行查询、生成图表和输出中文业务洞察。当前版本重点支持内容平台用户增长分析场景。

## 项目定位
- 通用定位：智能数据洞察分析系统（通用 AI 数据分析 Agent）
- 当前重点场景：内容平台用户增长分析（含 B站 UP 主公开视频数据 Beta）

## 核心功能
- Demo 数据生成与 CSV 接入
- 指标计算与 SQLite 入库
- DeepSeek SQL 生成（无 Key 自动 fallback）
- SQL 安全检查与执行
- 多图表展示与中文分析结论
- 查询历史记录与可视化页面

## 项目架构
Connectors -> Ingestion -> Metrics -> SQLite -> SQL Agent -> SQL Guard -> SQL Executor -> Chart/Insight -> Memory -> Frontend/Streamlit

## Agent 工作流
用户问题 → Planner → SQLAgent → SQLGuard → SQLite → ChartAgent → InsightAgent → 分析报告

## 技术栈
Python, FastAPI, Vue3, Element Plus, ECharts, Pandas, SQLite, OpenAI SDK(DeepSeek Compatible)

## 安装与运行
### 后端
```bash
cd D:\Projects\mini-airda-plus
python -m pip install -r backend\requirements.txt
python backend\main.py
```

### 前端
```bash
cd D:\Projects\mini-airda-plus\frontend
npm install
npm run dev
```

### Streamlit（保留旧入口）
```bash
cd D:\Projects\mini-airda-plus
python src/main.py --demo
streamlit run app/streamlit_app.py
```

## DeepSeek 配置
1. 复制 `.env.example` 为 `.env`
2. 配置以下变量：
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com`）
- `DEEPSEEK_MODEL`（默认 `deepseek-chat`）
- `BILIBILI_COOKIE`（可选，用于 B站数据拉取）

运行 `python src/main.py --demo` 时会打印：
- 有 Key：`当前模式：DeepSeek API 模式`
- 无 Key：`当前模式：fallback 本地模拟模式`

## 当前重点指标
- 播放率 `play_rate`
- 完播率 `completion_rate`
- 互动用户率 `engagement_user_rate`
- 主页访问率 `profile_visit_rate`
- 关注转化率 `follow_conversion_rate`
- 新用户占比 `new_user_ratio`
- 次日留存率 `next_day_retention_rate`
- 7日留存率 `day7_retention_rate`

## B站数据说明
- 当前已接入 B站 UP 主公开视频数据 Beta（UID/主页链接输入）。
- B站公开接口主要提供内容表现数据（播放、点赞、评论、分享等）。
- 为了打通用户增长分析链路，项目会对部分增长字段做规则模拟扩展（如留存/转化相关字段），用于分析流程验证与展示。
- B站接口可能受风控影响，支持可选 `BILIBILI_COOKIE` 以提升可用性。

## 可扩展场景
- 产品数据分析
- 用户行为分析
- 内容运营分析
- 电商经营分析
- 课程/知识付费分析
- 更多外部数据源 Connector

## 示例问题
1. 哪些视频播放量最高？
2. 哪些视频高播放低关注？
3. 哪个内容分类带来的新增用户最多？
4. 最近 7 天关注转化率趋势如何？
5. 哪个环节流失最大？
6. 各内容分类的次日留存率怎么样？

## 后续优化方向
1. 外部数据源稳定性与更多 Connector 扩展
2. SQL 多轮纠错与语义澄清
3. 自动报告模板与任务编排
4. 缓存、异步执行与性能优化

## 当前限制
- B站接口可能受风控或频率限制影响，偶发失败属于已知情况。
- 抖音入口当前为预留占位，暂未实现真实解析。
- 数据库使用 SQLite，适合本地演示、作品集与教学场景，不定位生产级多租户系统。
