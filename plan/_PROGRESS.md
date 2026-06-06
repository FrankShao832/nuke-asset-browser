# 执行进度

> **版本:** v2.1.0  
> **执行策略:** UI 优先 — Mock 数据先行  
> **设计变更 (2026-06-05):**
>   - 取消分类/分组 → 侧边栏过滤 + 实时搜索
>   - 取消 Tab 模式 → 单界面
>   - 侧边栏居右 (右手操作)
>   - PySide6 only (Python 3.11+, Nuke 16+)
>   - **执行顺序重构:** Phase 1 UI 先做 → Phase 3 存储层后接

---

## Phase 0: 最小化基础

### ✅ T0.1 创建目录结构 + 旧版代码复用分析
- 创建时间: 2026-06-05
- 代码复用分析: `plan/CODE_REUSE_ANALYSIS.md`
  - 直接继承: `browser_thumbnail.py`
  - 重构继承: `browser_container.py` (网格+右键+异步)
  - 继承布局: `browser_ui_settings.py`, `browser_template.py`
  - 废弃: `browser_tree_widget.py`, `browser_combobox_widget.py`

### ✅ T0.2 版本信息文件
### ✅ T0.5 数据模型定义 ← core/models.py
### ⬜ T0.3 配置管理

---

## Phase 1: UI 核心 — Mock 数据先行 ★★★

### ✅ T1.0 Package 入口 + 独立启动 (main.py)
### ✅ T1.3 搜索栏组件 — 防抖输入 + Ctrl+F 聚焦
### ✅ T1.4 侧边栏过滤面板 (右侧布局)
### ✅ T1.7 用户状态组件
### ✅ T1.8 草稿状态标记
### ✅ T1.3s 缩略图占位符生成
### ✅ T1.5 缩略图网格组件 ← 核心 UI
### ✅ T1.6 草稿保存对话框
### ✅ T1.9 设置对话框
### ✅ T1.10 搜索 + 过滤引擎
### ✅ T1.11 主窗口 — UI 大整合 🎯 ← Mock 数据全流程跑通

---

## Phase 2: Nuke 集成

---

## Phase 2: Nuke 集成

### ⬜ T2.1 Menu 注册
### ⬜ T2.2 Node Graph 右键保存
### ⬜ T2.3 拖拽集成

---

## Phase 3: 存储层实现 (替换 Mock)

### ⬜ T3.1 日志工具
### ⬜ T3.2 存储抽象基类
### ⬜ T3.3 PG 连接管理
### ⬜ T3.4 Schema 建表
### ⬜ T3.5 PG 存储实现
### ⬜ T3.6 JSON 存储实现
### ⬜ T3.7 自动选择 + 同步
### ⬜ T3.8 单元测试
### ⬜ T3.9 真实缩略图生成
### ⬜ T3.10 替换 Mock 数据 → 真实存储

---

## Phase 4: Asset Manager 桥接

### ⬜ T4.1 VFXContext
### ⬜ T4.2 API 客户端
### ⬜ T4.3 发布对话框
### ⬜ T4.4 同步引擎

---

## Phase 5: 打磨

### ⬜ T5.1 样式表
### ⬜ T5.2 图标资源
### ⬜ T5.3 错误处理
### ⬜ T5.4 性能优化
### ⬜ T5.5 边缘情况
### ⬜ T5.6 用户文档
