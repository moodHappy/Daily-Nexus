# 🌍 Daily-Nexus (全知日历枢纽)

一个高度自动化的全维度每日知识聚合器。通过 Python 脚本每天定时拉取全球精选资讯，并生成极具美感的静态日历枢纽页（依托 GitHub Pages 免费托管）。

---

## ✨ 核心特性 (Omni-Digest)

* **📚 每日高阶词汇 (Word of the Day)**：从专属高阶词库池随机抽取，调用 Dictionary API 获取英文释义、例句与同反义词。
* **🔍 维基百科焦点 (Wiki Trending)**：自动抓取 Wikipedia 过去 24 小时内最热门的词条及摘要。
* **🖼️ 今日世界掠影 (Wiki POTD)**：获取并展示 Wikipedia 每日高清推荐大图与背后的故事。
* **📡 全球 RSS 聚合**：自动追踪并拉取 BBC World, NYT, NHK, TechCrunch, Wired 等全球顶尖媒体的最新头条。
* **📅 交互式日历枢纽**：纯前端实现的高性能日历索引，支持年份/月份秒切，直观展示每日归档状态。
* **☁️ 云端档案管理**：内置本地配置中心，支持在网页端直接对 GitHub 仓库进行文件级精准抹除与状态同步。

---

## 🛠 技术栈

* **核心驱动**：Python 3 (`requests`, `feedparser`)
* **前端呈现**：原生 HTML5 / CSS3 / Vanilla JavaScript (自适应移动端)
* **部署与托管**：GitHub Actions + GitHub Pages
* **数据存储**：JSON + 静态 HTML 路由

---

## 🚀 部署指南

### 1. 基础环境与 Fork
1. **Fork 本仓库**到你的 GitHub 账号下（例如 `moodHappy/daily-nexus`）。
2. 在项目根目录确保存在 `requirements.txt` 文件，内容如下：
   ```text
   requests
   feedparser
   ```

### 2. 配置自动化 (GitHub Actions)
在仓库的 `.github/workflows/` 目录下创建一个 `.yml` 文件（例如 `daily_build.yml`），配置每天自动运行 `script.py` 并提交变更至 `main` 分支。

### 3. 开启 GitHub Pages
在仓库的 `Settings` -> `Pages` 中，将 Source 设置为 `Deploy from a branch`，并选择 `main` 分支的 `/docs` 目录，保存后即可获得你的专属访问链接。

---

## ⚙️ 高级玩法：网页端云管理

为了保持归档库的整洁，项目内置了直接在网页端删除过期归档并同步至 GitHub 的功能：

1. **获取 Token**：前往 GitHub 申请一个 Classic Personal Access Token (需勾选 `repo` 权限)。
2. **本地配置**：打开你的 Daily-Nexus 网页，点击左上角的 **⚙️ (齿轮图标)** 打开配置中心。
3. **填入信息**：
   * **GitHub Token**: 填入刚申请的 Token。
   * **GitHub 用户名**: 你的用户名（如 `moodHappy`）。
   * **GitHub 仓库名**: 你的仓库名（如 `daily-nexus`）。
   *(注：密钥仅保存在你的浏览器本地 `localStorage`，极其安全)*
4. **抹除模式**：在日历区域 **快速双击空白处** 即可唤醒隐藏的“删除模式”，点击列表右侧的 🗑️ 即可实现云端销毁。

---

## 📝 许可证与免责声明

* 本项目代码部分基于 MIT 协议开源。
* 新闻、词典及维基百科内容的版权归原数据提供方（BBC, NYT, NHK, Wikimedia, DictionaryAPI 等）所有。本项目仅作为个人阅读与学习自动化技术的练手之作，请勿用于商业用途或高频恶意请求。
