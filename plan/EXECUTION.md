# Nuke Asset Browser — 执行计划 (v2.1)

> **目标:** 智能体根据本计划自动推进开发  
> **执行策略:** UI 优先 — 先出界面效果，再逐步接入真实数据  
> **总阶段:** 6 阶段（重新编排）  
> **设计变更:**  
>   - 2026-06-05: 取消分类/分组 → 侧边栏过滤 + 实时搜索；取消 Tab 模式  
>   - 2026-06-05: 右侧边栏布局（右手操作）  
>   - 2026-06-05: PySide6 only, 不做向后兼容  
>   - 2026-06-05: **执行顺序重构 — UI 优先，Mock 数据先行**

---

## 执行哲学

```
传统方式 (原计划):  DB → 存储层 → 业务层 → UI
                   埋头写两周基础设施才看到第一个窗口

UI 优先 (新计划):  数据模型 → UI (Mock 数据) → Nuke 集成 → 存储层替换
                   第一天就能看到窗口！🔥
```

**UI 优先的好处：**
1. 你擅长 UI — 在最擅长的领域先发力 ✅
2. 面试作品是视觉展示 — 界面就是第一印象 ✅
3. Mock 数据隔离 UI 和后端 — 两不耽误 ✅
4. 成就感驱动 — 看到窗口动起来，动力更足 ✅

---

## 执行规则

1. **顺序执行** — 每步依赖上一步完成。出现阻塞时记录到 `_PROGRESS.md` 并继续尝试后续可独立完成的步骤
2. **验收标准** — 每步末尾有 "✅ Done when"，满足后才能标记完成
3. **记录日志** — 执行过程记录到 `_PROGRESS.md`
4. **发现问题** — 记录到 `_PROGRESS.md`，不中断执行流，除非是致命阻塞

---

## 铁律: 必须遵守的工程规范

### 🔴 代码规范

| 要求 | 强制程度 |
|------|----------|
| **类型注解** — 所有函数参数和返回值加 type hint | 🔴 必须 |
| **Docstring** — 每个模块、类、公共方法写 Google-style docstring | 🔴 必须 |
| **异常处理** — 所有外部操作 (DB/文件/网络) 捕获异常，绝不裸奔 | 🔴 必须 |
| **无硬编码路径** — 所有路径通过 config 或常量管理 | 🔴 必须 |
| **日志代替 print** — 使用 `utils/logger.py`，禁止 `print()` | 🔴 必须 |
| **import 规范** — 标准库 → 第三方 → 本地，三级分隔 | 🟠 推荐 |
| **命名规范** — 类名 PascalCase，函数/变量 snake_case，常量 UPPER_CASE | 🔴 必须 |
| **PySide6 only** — 不使用 PySide2 回退，纯 PySide6 + Python 3.11+ | 🔴 必须 |

### 🔴 VFX 管线开发最佳实践

| 实践 | 说明 |
|------|------|
| **优雅降级** | PG 断线 → 自动切 JSON，不弹红错，不崩溃 |
| **DCC 环境感知** | 始终 try/import nuke，不在非 Nuke 环境抛异常 |
| **版本锁定** | 目标 Nuke 16+ / Python 3.11+ / PySide6，不做向后兼容 |
| **资源路径** | 所有 icon/config 路径相对于包目录，不依赖绝对路径 |
| **幂等操作** | 建表、创建目录、初始化等操作可重复执行不报错 |
| **懒加载** | UI 启动时不阻塞，缩略图异步加载，PG 连接延迟初始化 |
| **日志分级** | 生产环境 INFO 起步，DEBUG 只在开发时开 |
| **前后向兼容** | 数据模型变更时提供迁移逻辑，不破坏已有 JSON/PG 数据 |

### 🔴 Docstring 标准 (Google Style)

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述一行。

    Args:
        param1: 参数说明。
        param2: 参数说明。

    Returns:
        返回值说明。

    Raises:
        ValueError: 什么情况下会抛。
    """
```

### 🟢 执行时的行为准则

1. **先读后写** — 修改已有文件前先 `read_file` 读完整内容，不要覆盖
2. **一个 Task 一次提交** — 一个 Task 完成后，向用户报告结果，等用户确认再继续下一个
3. **Task 太大时拆分** — 如果某个 Task 预计超过 30 分钟，主动建议拆分
4. **不确定就问** — 设计决策拿不准时，先问默雷，不猜

---

## 阶段 0: 最小化基础 — 开张前的准备工作

> **目标:** 用最少的工作量把"地基"打好，让 UI 能站住。

---

### T0.1 创建目录结构 + 旧版代码复用分析 ✅

```
动作（已完成）:
  mkdir -p:
    asset_browser/core/
    asset_browser/db/
    asset_browser/bridge/
    asset_browser/ui/widgets/
    asset_browser/ui/dialogs/
    asset_browser/ui/resources/icons/
    asset_browser/utils/
    asset_browser/tests/
    asset_browser/plan/

  同时为每个子目录创建空的 __init__.py

  + 完成旧版代码复用分析报告:
    plan/CODE_REUSE_ANALYSIS.md
```

✅ Done when: 目录树完整，所有 `__init__.py` 存在，代码分析报告完成

---

### T0.2 创建版本信息文件

```
文件: asset_browser/__version__.py

内容:
  __version__ = "2.1.0"
  __description__ = "Nuke Asset Browser - Draft Management Tool"
  __author__ = "Frank (默雷)"
```

✅ Done when: `from asset_browser.__version__ import __version__` 可导入

---

### T0.5 数据模型定义 ★（核心契约）

```
文件: asset_browser/db/models.py

需求:
  - 使用 dataclass 定义纯数据模型 (不依赖 ORM)
  - class Draft:
      id: Optional[int]
      name: str
      type: str           # 'template', 'image', 'video', 'script', 'other'
      file_path: str
      file_size: Optional[int]
      thumbnail_path: Optional[str]
      description: Optional[str]
      tags: list[str]
      metadata: dict
      is_shared: bool
      is_favorite: bool
      created_by: str
      updated_by: Optional[str]
      published_to: Optional[int]
      published_at: Optional[datetime]
      created_at: datetime
      updated_at: datetime

  - 所有类实现 to_dict() / from_dict() 方法
  - ⚠️ 这是 UI 和后端的"接口协议"，必须最先定义好
```

✅ Done when: `Draft(name="test", type="template", file_path="/tmp/test.nk", created_by="frank")` 能创建并 to_dict

---

### T0.3 实现配置管理 (基础版)

```
文件: asset_browser/utils/config.py

需求:
  - 读取优先级: 环境变量 > YAML 配置文件 > 默认值
  - 配置项:
    - user_name (默认: 当前系统用户)
    - thumbnail_size (默认: 260x180)
    - theme (默认: dark)
    - json_cache_path (默认: ~/.cache/asset_browser/)
    - pg_host / pg_port / pg_database / pg_user / pg_password
  - 环境变量前缀: AM_
  - 提供 Config 单例
  - 先实现基础配置项，PG 配置项可以 stub 留空
```

✅ Done when: `from asset_browser.utils.config import config; config.user_name` 返回当前系统用户名

---

## 阶段 1: UI 核心 — Mock 数据先行 ★★★

> **目标:** 你的主战场！用 Mock 数据填充 UI，做出可以直接打开的界面。
> **Mock 数据策略:** 所有 UI 组件从外部接收数据（不自己读数据库），后期替换数据源时 UI 代码零改动。

---

### T1.0 Package 入口 + 独立启动 ★

```
文件: asset_browser/main.py

需求:
  - 这是整个包的**唯一入口**
  - 支持两种运行模式:

    # 模式 A: 独立启动 (开发测试用)
    # python -m asset_browser.main
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = MainWindow()
        window.setWindowTitle("Nuke Asset Browser (Standalone)")
        window.show()
        sys.exit(app.exec())

    # 模式 B: Nuke 插件 (生产用)
    def install_menu():
        """注册到 Nuke 菜单"""
        ...

    def open_browser():
        """打开浏览器窗口 (单例)"""
        ...

  - 运行模式 A 时自动注入 Mock 数据
  - 不依赖 nuke 模块，纯 PySide6 可独立运行
  - 这样你在没开 Nuke 的时候也能调试 UI！

文件结构:
  asset_browser/
    ├── main.py          ← 入口在这里，新增
    ├── __init__.py
    ├── __version__.py
    └── ...
```

✅ Done when: `python -m asset_browser.main` 能弹出空窗口 (MainWindow 先 stub)

---

### T1.3 搜索栏组件

```
文件: asset_browser/ui/widgets/search_bar.py

需求:
  - class SearchBar(QWidget)
  - QLineEdit + 清除按钮
  - 实时搜索: 输入时 200ms 防抖后发出搜索信号
  - 信号: search_changed(keyword: str)
  - 快捷键: Ctrl+F 聚焦搜索框
  - 占位符文本: "🔍 搜索模板..."

备注: 纯 UI 组件，不涉及数据
```

✅ Done when: 输入内容 200ms 后发出搜索信号

---

### T1.4 侧边栏过滤面板（右侧布局）

```
文件: asset_browser/ui/widgets/sidebar_filter.py

需求:
  - class SidebarFilter(QWidget)
  - 位置: 主窗口右侧 (右手操作友好)
  - 固定宽度 ~200px
  - 过滤项:
    ├─ 🔵 全部       → filter: "all"
    ├─ 🟢 我的草稿    → filter: "mine"
    ├─ 🟡 共享       → filter: "shared"
    ├─ ⭐ 收藏      → filter: "favorites"
    └─ ✓ 已发布     → filter: "published"
  - 排序: 最新 / 最热
  - 每个过滤项显示当前数量 (badge)
  - 信号: filter_changed(filter: str), sort_changed(sort: str)
  - 上传按钮: [📤 上传] 在底部

备注: 纯 UI 组件，点击发出信号即可
```

✅ Done when: 点击过滤项发出对应的 filter 信号

---

### T1.7 用户状态组件

```
文件: asset_browser/ui/widgets/user_badge.py

需求:
  - class UserBadge(QWidget)
  - 显示当前用户名 (从 config 读取)
  - 存储状态指示: 🟢 PG / 🟡 JSON / 🔴 离线
  - 显示同步状态: 上次同步时间
  - Phase 1 阶段: 默认显示 "frank" + 🟢 PG (Mock)
```

✅ Done when: 组件显示正确的用户和 Mock 存储状态

---

### T1.8 草稿状态标记组件

```
文件: asset_browser/ui/widgets/draft_badge.py

需求:
  - class DraftBadge(QLabel)
  - 显示草稿状态:
    - "草稿" (未发布) — 灰色
    - "已发布 ✓" — 绿色
    - "有修改" — 橙色
  - 缩略图右上角叠加显示
```

✅ Done when: 缩略图右上角显示状态标记

---

### T1.3 缩略图占位符生成（Phase 1 简化版）

```
文件: asset_browser/core/thumbnail.py (Phase 1 — Mock 版)

需求:
  - get_placeholder_thumbnail(draft_type: str, size=(260,180)) -> QPixmap
  - 根据草稿类型返回不同颜色的占位图:
    - 'template' → 蓝色 + 📄
    - 'image'    → 绿色 + 🖼️
    - 'video'    → 红色 + 🎬
    - 'script'   → 紫色 + 📜
    - 'other'    → 灰色 + 📁
  - 后续 Phase 3 替换为真实 ffmpeg/PySide 缩略图

旧版参考: backups_01/browser_thumbnail.py (占位图和图标映射逻辑)
```

✅ Done when: `get_placeholder_thumbnail("template", (260,180))` 返回蓝色占位图

---

### T1.5 缩略图网格组件（核心 UI 组件）

```
文件: asset_browser/ui/widgets/thumbnail_grid.py

需求:
  - class ThumbnailGrid(QWidget)
  - 基于 QTableWidget / QListView + QStyledItemDelegate
  - 功能:
    - 接收 Draft 列表 → 渲染缩略图网格
    - 右键菜单:
      ├── ⭐ 收藏 / 取消收藏
      ├── 📤 发布到 Asset Manager
      ├── ✏️ 重命名
      ├── 📋 复制路径
      ├── 📂 打开所在目录
      └── 🗑️ 删除
    - 双击: 信号发出 (后期接 Nuke 导入)
    - 拖拽支持 (拖出/拖入 — Phase 2 完善)
    - 缩略图使用 T1.3 占位图 (后期替换为真实缩略图)
    - 异步加载: 占位图先显示，再替换为真实缩略图
  - 信号: draft_selected(draft_id), draft_dropped(file_path)
  - 核心方法:
    set_drafts(drafts: list[Draft])  ← UI 的唯一数据入口
    add_draft(draft)
    remove_draft(draft_id)

从旧项目继承: asset_browser_bak/ui/browser_table_widget.py
              backups_01/browser_container.py (右键菜单、列计算)
```

✅ Done when: 组件能接收 Draft 列表并渲染缩略图网格，右键菜单完整

---

### T1.6 草稿保存对话框

```
文件: asset_browser/ui/dialogs/save_dialog.py

需求:
  - class SaveDraftDialog(QDialog)
  - 从 Node Graph 右键或拖入时弹出
  - 字段:
    - 名称 (自动填充: 选中节点名 / 文件名)
    - 描述 (可选)
    - 标签 (可选，逗号分隔)
    - 可见性: 个人 / 共享
  - 预览缩略图
  - 确定 / 取消
  - 返回 Draft 对象

从旧项目继承: backups_01/browser_template.py
```

✅ Done when: 能打开对话框创建并保存草稿

---

### T1.9 设置对话框

```
文件: asset_browser/ui/dialogs/settings_dialog.py

需求:
  - class SettingsDialog(QDialog)
  - 编辑 (Phase 1: 只显示界面，保存功能先 stub):
    - PG 连接 (host/port/db/user/password)
    - JSON 缓存路径
    - ffmpeg 路径
    - 缩略图质量 / 尺寸
  - "测试连接" 按钮 (Phase 1: 显示"功能开发中")
  - 保存到 config

从旧项目继承: backups_01/browser_ui_settings.py
```

✅ Done when: 设置对话框可打开，配置项显示正常

---

### T1.10 搜索 + 过滤引擎

```
文件: asset_browser/core/search.py

需求:
  - class DraftSearch
  - search(keyword: str, drafts: list[Draft]) → list[Draft]
  - 搜索字段: name, description, tags
  - 支持过滤: 全部 / 我的 / 共享 / 收藏 / 已发布
  - 空关键词返回全部
  - 纯内存操作 (接收 Draft 列表，返回过滤后的列表)
  - 后期替换为 DraftStorage 的 search 方法
```

✅ Done when: 搜索 + 过滤功能正常返回结果

---

### T1.11 主窗口 — UI 大整合 🎯

```
文件: asset_browser/ui/main_window.py

需求:
  - class MainWindow(QWidget)
  - 布局:
    ├── 顶部通栏: SearchBar (搜索框)
    ├── 中央: ThumbnailGrid (缩略图网格) — 主力显示区域
    ├── 右侧: SidebarFilter (过滤面板 + 上传按钮) — 右手操作
    └── 右上角: UserBadge (状态信息)
  - Mock 数据系统:
    MOCK_DRAFTS = [
        Draft(id=1, name="film_grain_001", type="template", ...),
        Draft(id=2, name="light_warp_02", type="image", ...),
        Draft(id=3, name="dust_sparks", type="video", ...),
        ...
    ]
  - 功能:
    - 加载 Mock 数据到 ThumbnailGrid
    - 搜索框输入 → 实时过滤 Mock 数据
    - 侧边栏点击 → 切换过滤
    - 右键菜单工作
    - 上传按钮 → 文件选择器 → SaveDraftDialog
  - 窗口设置:
    - 标题: "Nuke Asset Browser"
    - 尺寸: 1400x800, 最小 1200x600
    - 窗口置顶 (可选)

从旧项目继承: asset_browser_bak/assets_browser.py (窗口初始化模式)
```

✅ **Done when: 在 main.py 模式 A 下 `python -m asset_browser.main` 弹出窗口，看到 Mock 数据渲染的缩略图网格，搜索/过滤/右键全部可用！** 🔥

---

## 阶段 2: Nuke 集成

> **目标:** 把 UI 挂到 Nuke 菜单里，增加 Nuke 原生交互。
> **前置条件:** T1.0 已创建 `main.py`，T1.11 已创建 `MainWindow`

---

### T2.1 Nuke 菜单注册（扩展 T1.0 的 main.py）

```
文件: asset_browser/main.py (扩展 — 添加 Nuke 模式)

需求:
  - 在 T1.0 的 main.py 基础上添加 Nuke 模式:

    # 模式 B: Nuke 插件
    def install_menu():
        try:
            import nuke
            toolbar = nuke.menu("Nuke").addMenu("🏪 Asset Browser")
            toolbar.addCommand("Open Browser", open_browser, "^b")
        except ImportError:
            pass  # 非 Nuke 环境，忽略

    def open_browser():
        """打开浏览器窗口 (单例)"""
        if not hasattr(open_browser, '_window'):
            open_browser._window = MainWindow()
        open_browser._window.show()
        open_browser._window.raise_()

  - 快捷键: Ctrl+Shift+B
  - 工具栏按钮 (可选)

  - 模式 A (独立启动) 保持不变
```

✅ Done when: `python -m asset_browser.main` 仍能独立启动，且 `import asset_browser.main; main.install_menu()` 在 Nuke 中注册菜单

---

### T2.2 Node Graph 右键保存（杀手功能）

```
文件: asset_browser/main.py (扩展)
      asset_browser/utils/nuke_utils.py

需求:
  - nuke_utils.py:
    - get_selected_nodes() → list
    - save_selected_nodes_to_template() → Optional[str]
    - create_node_from_template(template_path: str) → bool

  - main.py:
    - 在 Node Graph 中右键选中节点 → "Save to Asset Browser"
    - 选中多个节点 → 合并为 Group 再保存
    - 弹出 SaveDraftDialog
    - 自动填充: 节点名 → 草稿名, 节点内容 → .nk 临时文件
```

✅ Done when: Node Graph 选中节点可右键保存为草稿

---

### T2.3 拖拽集成

```
文件: asset_browser/ui/widgets/thumbnail_grid.py (扩展)

需求:
  - 拖出: 从 ThumbnailGrid 拖到 Nuke Node Graph
    - .nk 模板 → 导入到 Node Graph
    - 图片 → 创建 Read 节点
  - 拖入: 从 Nuke Node Graph 拖到 ThumbnailGrid
    - 选中节点 → 弹出 SaveDraftDialog
```

✅ Done when: 拖拽模板到 Nuke 节点图能创建节点

---

## 阶段 3: 存储层 — 替换 Mock 数据

> **目标:** 用真实数据库替换 Mock 数据，Mock 时写的 UI 代码一行不动。

---

### T3.1 实现日志工具

```
文件: asset_browser/utils/logger.py

需求:
  - 替代 print 调试
  - 日志级别: DEBUG, INFO, WARNING, ERROR
  - 输出到 stderr (Nuke 里不干扰管线输出)
  - 格式: [时间] [级别] [模块] 消息
  - 提供 get_logger(name) 函数
```

✅ Done when: `from asset_browser.utils.logger import get_logger` 输出格式化日志

---

### T3.2 实现存储抽象基类

```
文件: asset_browser/db/base.py

需求:
  - class DraftStorage(ABC):
      @abstractmethod
      def get_drafts(self, user: str, filter: str = "all") -> list[Draft]: ...
      @abstractmethod
      def get_draft(self, draft_id: int) -> Optional[Draft]: ...
      @abstractmethod
      def create_draft(self, draft: Draft) -> int: ...
      @abstractmethod
      def update_draft(self, draft: Draft) -> bool: ...
      @abstractmethod
      def delete_draft(self, draft_id: int) -> bool: ...
      @abstractmethod
      def toggle_favorite(self, draft_id: int) -> bool: ...
      @abstractmethod
      def search(self, keyword: str, user: str, filter: str = "all") -> list[Draft]: ...
      @abstractmethod
      def is_available(self) -> bool: ...
```

✅ Done when: 抽象类定义完整，`DraftStorage` 不能直接实例化

---

### T3.3 PostgreSQL 连接管理

```
文件: asset_browser/db/connection.py

需求:
  - class DatabasePool (单例)
  - 从 config.py 读取 PG 配置
  - get_connection() → psycopg2 connection (上下文管理器)
  - initialize() → 延迟初始化
  - 连接失败时记录 WARNING 日志, 不抛异常
```

✅ Done when: 能连接或优雅降级

---

### T3.4 PG Schema 建表脚本

```
文件: asset_browser/db/schema.py

需求:
  - CREATE SCHEMA IF NOT EXISTS browser
  - 创建 browser.drafts 表 (扁平化)
  - 创建索引
  - 幂等 (重复执行不报错)
```

✅ Done when: 执行后 PG 中出现 browser schema 和 drafts 表

---

### T3.5 PostgreSQL 存储实现

```
文件: asset_browser/db/pg_store.py

需求:
  - class PGDraftStorage(DraftStorage)
  - 实现所有抽象方法
  - filter: "all"/"mine"/"shared"/"favorites"/"published"
  - search: SQL LIKE
  - 参数化查询 (防注入)
```

✅ Done when: 所有 CRUD 操作通过 PGDraftStorage 可正常执行

---

### T3.6 JSON 存储实现

```
文件: asset_browser/db/json_store.py

需求:
  - class JSONDraftStorage(DraftStorage)
  - 单文件存储: {cache_path}/drafts.json
  - 内存全量加载 + 写时 dump
  - 线程锁保护
  - 文件不存在时自动创建空结构
```

✅ Done when: 所有 CRUD 操作通过 JSONDraftStorage 可正常执行

---

### T3.7 存储自动选择 + 同步引擎

```
文件: asset_browser/db/sync.py

需求:
  - get_storage() → 自动选择 PG or JSON
  - sync_pg_to_json() / sync_json_to_pg()
  - auto_sync() → 定期检测 PG 状态
```

✅ Done when: PG 可用时返回 PGDraftStorage，不可用时返回 JSONDraftStorage

---

### T3.8 存储层单元测试

```
文件: asset_browser/tests/
  tests/test_models.py
  tests/test_json_store.py
  tests/test_pg_store.py (跳过如果 PG 不可用)
  tests/test_sync.py
```

✅ Done when: `pytest tests/` 全部通过

---

### T3.9 真实缩略图生成（替换 Phase 1 占位图）

```
文件: asset_browser/core/thumbnail.py (升级为完整版)

需求:
  - generate_thumbnail(file_path, output_path, size=(260,180)) → bool
  - 支持: .exr/.dpx/.tif/.png/.jpg → QPixmap 缩放
  - 支持: .mov/.mp4 → ffmpeg 抽取关键帧
  - 缓存机制
  - 异步生成 (QThreadPool)

从旧项目继承: backups_01/browser_thumbnail.py
              backups_01/browser_container.py (异步加载模式)
```

✅ Done when: 真实缩略图替换占位图，网格显示正常

---

### T3.10 替换 Mock 数据 → 真实存储

```
文件: asset_browser/ui/main_window.py (修改)

需求:
  - 删除 MOCK_DRAFTS 硬编码数据
  - 初始化时调用 get_storage() 获取 DraftStorage
  - 所有数据操作通过 DraftStorage 接口
  - 搜索/过滤走 DraftStorage.search()
  - UI 代码零改动 — 只替换数据源
```

✅ Done when: 主窗口从真实数据库加载数据，Mock 数据完全移除

---

## 阶段 4: Asset Manager 桥接

### T4.1 VFXContext 读取

```
文件: asset_browser/bridge/context.py
```

✅ Done when: `VFXContext.from_env()` 正确读取环境变量

### T4.2 Asset Manager API 客户端

```
文件: asset_browser/bridge/api_client.py
```

✅ Done when: API 客户端定义完整，调用失败不崩溃

### T4.3 发布对话框

```
文件: asset_browser/ui/dialogs/publish_dialog.py
```

✅ Done when: 发布对话框可正常打开，发布后草稿状态更新

### T4.4 同步引擎

```
文件: asset_browser/bridge/sync_engine.py
```

✅ Done when: 草稿可成功发布

---

## 阶段 5: 完善与打磨

### T5.1 样式表 → `ui/resources/styles.qss`
### T5.2 图标资源 → 从 ref/ 迁移
### T5.3 错误处理与用户提示
### T5.4 性能优化 (缩略图懒加载 + 搜索防抖)
### T5.5 边缘情况处理
### T5.6 用户文档 → `plan/USER_GUIDE.md`

---

## 附录 A: 执行路线图

```
时间线                    做什么                              你看到什么
──────                    ──────                              ──────────
今天          Phase 0: T0.2 T0.5 T0.3    准备数据模型+配置
今天~明天     Phase 1: T1.3~T1.11         UI + Mock 数据       🎉 能打开的窗口！
第3天         Phase 2: T2.1~T2.3          Nuke 集成            Nuke 菜单里有它
第4~7天       Phase 3: T3.1~T3.10         存储层替换           真实数据驱动
第2周         Phase 4: T4.1~T4.4          Asset Manager 桥接   发布功能
第3周         Phase 5: T5.1~T5.6          打磨                 面试作品完成
```

## 附录 B: 依赖关系图

```
Phase 0: 最小化基础
  T0.1 ✅ (目录结构)
    ├── T0.2 (版本信息)
    ├── T0.5 (数据模型) ──★ UI 和后端的契约
    └── T0.3 (配置管理)

Phase 1: UI 核心 ─── 你的主战场！
  T1.3 (搜索栏)     T1.4 (侧边栏过滤)
  T1.7 (用户状态)   T1.8 (状态标记)   
  T1.3s (占位缩略图) T1.5 (缩略图网格)
  T1.6 (保存对话框)  T1.9 (设置对话框)
  T1.10 (搜索引擎)   
        │
        └── T1.11 (主窗口) ← 全部 UI 整合 + Mock 数据
                │
Phase 2: Nuke 集成
    ├── T2.1 (Menu 注册) → Nuke 菜单出现
    ├── T2.2 (右键保存)   → 杀手功能
    └── T2.3 (拖拽集成)

Phase 3: 存储层 (替换 Mock)
  T3.1 (日志) → T3.2 (抽象基类) → T3.3~T3.5 (PG) → T3.6 (JSON)
  → T3.7 (自动选择) → T3.8 (测试) → T3.9 (真实缩略图)
  → T3.10 (替换 Mock) ← UI 零改动

Phase 4: Bridge 层
  T4.1~T4.4

Phase 5: 打磨
  T5.1~T5.6
```

## 附录 C: 验收清单

```
Phase 0: 最小化基础
  ⬜ T0.1  ✅  (已完成)
  ⬜ T0.2  版本信息
  ⬜ T0.5  数据模型 ← 先做这个！
  ⬜ T0.3  配置管理

Phase 1: UI 核心 ★★★
  ⬜ T1.3  搜索栏
  ⬜ T1.4  侧边栏过滤 (右侧)
  ⬜ T1.7  用户状态组件
  ⬜ T1.8  草稿状态标记
  ⬜ T1.3s 缩略图占位符
  ⬜ T1.5  缩略图网格
  ⬜ T1.6  保存对话框
  ⬜ T1.9  设置对话框
  ⬜ T1.10 搜索+过滤引擎
  ⬜ T1.11 主窗口 (Mock 数据) 🎉

Phase 2: Nuke 集成
  ⬜ T2.1  Menu 注册
  ⬜ T2.2  Node Graph 右键保存
  ⬜ T2.3  拖拽集成

Phase 3: 存储层
  ⬜ T3.1  日志工具
  ⬜ T3.2  存储抽象基类
  ⬜ T3.3  PG 连接
  ⬜ T3.4  Schema 建表
  ⬜ T3.5  PG 存储
  ⬜ T3.6  JSON 存储
  ⬜ T3.7  自动选择+同步
  ⬜ T3.8  单元测试
  ⬜ T3.9  真实缩略图生成
  ⬜ T3.10 替换 Mock 数据

Phase 4: Asset Manager
  ⬜ T4.1~T4.4

Phase 5: 打磨
  ⬜ T5.1~T5.6
```
