# Nuke Asset Browser 重构计划 (v2.1)

> **版本:** v2.1.0  
> **日期:** 2026-06-05 (重建设计)  
> **定位:** 公司生产环境级 Nuke 内部草稿管理器  
> **哲学:** 搜索优先，分类退居 — 一个界面，搞定一切

---

## 1. 项目定位

### 1.1 一句话定义

> **Nuke 内部的"共享便利店"** — 所有合成师随手浏览素材、上传临时模板的轻量工具，草稿完善后一键升格为管线正式资产。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **快速** | 启动快、浏览快、操作快，不拖 Nuke 后腿 |
| **共享** | 公司环境多人协作，草稿可共享可隔离 |
| **公司级** | PostgreSQL 持久化，支持并发、权限、审计 |
| **离线不废** | 断线自动降级 JSON 缓存，恢复后自动同步 |
| **可升格** | 草稿一键"升格"为 Asset Manager 的正式资产 |
| **搜索优先** | 不依赖分类，搜索和过滤就是导航方式 |
| **右键即用** | 所有操作通过右键菜单完成，干净高效 |

---

## 2. 界面设计 — 全平铺 + 右侧边栏过滤 + 实时搜索

> **侧边栏居右设计:** 符合右手操作习惯，鼠标从右侧面板点击过滤项后，向左移动到缩略图网格的操作路径最短。

```
┌──────────────────────────────────────────────────────┐
│  🔍 搜索模板... (实时过滤，200ms 防抖)               │
├──────────────────────────────────────┬───────────────┤
│                                      │               │
│     缩略图网格 (实时搜索结果)          │  侧边栏过滤    │
│                                      │               │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐        │ ├─ 🔵 全部   │
│  │ 📄 │ │ 📄 │ │ 📄 │ │ 📄 │        │ ├─ 🟢 我的    │
│  │噪点 │ │灯光 │ │调色 │ │合成 │        │ ├─ 🟡 共享    │
│  │纹理 │ │模板 │ │LUT  │ │预设 │        │ ├─ ⭐ 收藏   │
│  └────┘ └────┘ └────┘ └────┘        │ └─ ✓ 已发布  │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐        │               │
│  │ 📄 │ │ 📄 │ │ 📄 │ │ 📄 │        │  排序          │
│  │...  │ │...  │ │...  │ │...  │        │ ├─ 最新      │
│  └────┘ └────┘ └────┘ └────┘        │ └─ 最热      │
│                                      │               │
│     右键菜单:                         │ [📤 上传]    │
│     ┌──────────────────────┐         │               │
│     │ ⭐ 收藏              │         │               │
│     │ 📤 发布到 Asset Mgr  │         │               │
│     │ ✏️ 重命名            │         │               │
│     │ 📋 复制路径          │         │               │
│     │ 🗑️ 删除             │         │               │
│     │ 📂 打开所在目录       │         │               │
│     └──────────────────────┘         │               │
└──────────────────────────────────────┴───────────────┘
```

### 布局说明

| 区域 | 位置 | 内容 |
|------|------|------|
| **搜索栏** | 顶部通栏 | QLineEdit，实时搜索，200ms 防抖 |
| **缩略图网格** | 中央主力区域 | 缩略图瀑布流，右键菜单，拖拽支持 |
| **侧边栏过滤** | **右侧** | 过滤按钮 + 排序 + 上传按钮，右手操作友好 |

### 核心交互逻辑

| 操作 | 行为 |
|------|------|
| **搜索框输入** | 实时过滤，200ms 防抖，搜 name / description / tags |
| **侧边栏点击** (右侧) | 切换过滤：全部 / 我的 / 共享 / 收藏 / 已发布 |
| **双击草稿** | 导入到 Nuke Node Graph |
| **拖拽到 Node Graph** | 创建节点 (.nk → 导入模板, 图片 → Read 节点) |
| **从 Node Graph 拖入** | 快速保存草稿（自动命名） |
| **Node Graph 右键选中节点** | "Save to Asset Browser" → 弹出保存对话框 |
| **右键草稿** | 收藏 / 发布 / 重命名 / 复制路径 / 删除 |
| **点击上传按钮** | 文件选择器 → 上传并编辑信息 |

---

## 3. 旧代码分析

### 3.1 目录结构与行数

```
asset_browser_bak/
├── __init__.py                  (0行, 空)
├── assets_browser.py           (99行, 主面板入口)
├── test.py                     (13行, 测试字典)
├── database/
│   ├── __init__.py              (0行, 空)
│   └── browser_database.py     (134行, JSON CRUD)
├── ui/
│   ├── __init__.py              (0行, 空)
│   ├── browser_table_widget.py  (89行, 缩略图网格)
│   ├── browser_tree_widget.py   (93行, 分类树) ← 废弃
│   └── browser_combobox_widget.py (70行, 分组下拉) ← 废弃
├── utils/
│   ├── __init__.py              (0行, 空)
│   └── browser_settings.py     (64行, 设置管理)
├── backups_01/                  (旧版单体架构, 含完整功能)
│   ├── browser_container.py    (1032行, 单体容器)
│   ├── browser_ui_operation.py (1010行, UI 操作逻辑)
│   ├── browser_ui_settings.py  (276行, 设置 UI)
│   ├── browser_template.py     (194行, 模板管理)
│   ├── browser_thumbnail.py    (121行, 缩略图)
│   └── ...
└── ref/                         (截图与图标资源)
```

**新版本不再使用的旧组件：**
- `browser_tree_widget.py` — 分类树 → 替换为侧边栏过滤
- `browser_combobox_widget.py` — 分组下拉 → 替换为侧边栏过滤

**继承的旧组件：**
- `browser_table_widget.py` → 缩略图网格 (交互保留，数据源重写)
- `browser_thumbnail.py` → 缩略图生成 (重用)
- `browser_ui_settings.py` → 设置对话框 (继承)
- `browser_template.py` → 模板编辑 (继承)
- `browser_ui_operation.py` → 操作逻辑参考

### 3.2 存在的问题 (继承)

| 问题 | 严重度 | 描述 |
|------|--------|------|
| JSON 单用户 | 🔴 | 多人同时用会覆盖数据，公司环境不可用 |
| 代码不完整 | 🟠 | add/remove group/category 全是 stub |
| 硬编码路径 | 🔴 | icon 写死 `/Volumes/KirinTor/...` |
| 导入别名混淆 | 🟠 | 代码内用 `asset_browser`，目录却是 `asset_browser_bak` |
| 无权限/审计 | 🔴 | 不知道谁传了/删了什么 |
| 无 Nuke 集成规范 | 🟠 | 只有 `start()` 函数，没有 menu 注册 |
| 无日志 | ⚪ | 全靠 `print()` |

### 3.3 旧版代码复用清单

详见 `plan/CODE_REUSE_ANALYSIS.md`，核心可复用组件：

| 优先级 | 源文件 | 复用为 | 方式 |
|--------|--------|--------|------|
| 🔴 | `backups_01/browser_thumbnail.py` | `core/thumbnail.py` + UI 引用 | 直接继承 |
| 🔴 | `backups_01/browser_container.py` | `ui/widgets/thumbnail_grid.py` | 重构继承，数据源替换 |
| 🟠 | `backups_01/browser_ui_settings.py` | `ui/dialogs/settings_dialog.py` | 继承布局，换配置项 |
| 🟠 | `backups_01/browser_template.py` | `ui/dialogs/save_dialog.py` | 继承 FormLayout |
| 🟡 | `backups_01/browser_ui_operation.py` | MainWindow controller | 操作模式参考 |
| ❌ | `ui/browser_tree_widget.py` | 废弃 | 替换为侧边栏过滤 |
| ❌ | `ui/browser_combobox_widget.py` | 废弃 | 替换为侧边栏过滤 |

---

## 4. 新架构

### 4.1 存储架构

```
                    Nuke Asset Browser v2.1
                           │
              ┌────────────┴────────────┐
              │                         │
        PostgreSQL                  JSON 缓存
        (主力存储)                  (离线兜底)
              │                         │
      ┌───────┴───────┐         ┌───────┴───────┐
      │  共享草稿库    │         │ 本地缓存/断线   │
      │  多用户并发    │         │ 恢复后自动同步   │
      │  created_by    │         │                │
      │  is_shared     │         │                │
      └───────────────┘         └───────────────┘
              │                         │
              └──────────┬──────────────┘
                         ▼
              ┌──────────────────────┐
              │   发布/同步桥        │
              │   草稿 → 升格发布     │
              │   PG ↔ JSON 自动同步  │
              └──────────────────────┘
```

### 4.2 存储选择逻辑

```
PG 可用? ──yes──→ 用 PostgreSQL (主力)
  │
  no
  │
  ▼
JSON 缓存可用? ──yes──→ 离线模式, 只读本地缓存
  │
  no
  │
  ▼
提示用户检查 PG 连接
```

### 4.3 新目录结构

```
asset_browser/
├── __init__.py                  # 包声明
├── __version__.py               # 版本号
├── main.py                      # 唯一入口: 独立启动模式 / Nuke 插件模式
│                                #   python -m asset_browser.main 即可弹出窗口
│
├── core/                        # 核心业务逻辑
│   ├── __init__.py
│   ├── browser.py               # 浏览器核心逻辑
│   ├── search.py                # 搜索与过滤 (实时搜索)
│   └── thumbnail.py             # 缩略图生成 (ffmpeg/PySide)
│
├── db/                          # 数据层 — 双存储抽象
│   ├── __init__.py
│   ├── base.py                  # DraftStorage 抽象基类
│   ├── pg_store.py              # PostgreSQL 实现 (主力)
│   ├── json_store.py            # JSON 实现 (离线兜底)
│   ├── connection.py            # PG 连接管理 + 连接池
│   ├── schema.py                # PG 建表 DDL / 迁移
│   └── sync.py                  # PG ↔ JSON 双向同步
│
├── bridge/                      # ↔ Asset Manager 桥接层
│   ├── __init__.py
│   ├── api_client.py            # Asset Manager API 客户端
│   ├── sync_engine.py           # 同步引擎 (草稿→正式)
│   └── context.py               # VFXContext 读取 (环境变量)
│
├── ui/                          # UI 层 — 单界面设计
│   ├── __init__.py
│   ├── main_window.py           # 主窗口
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── thumbnail_grid.py    # 缩略图网格 (核心)
│   │   ├── sidebar_filter.py    # 侧边栏过滤面板 (新)
│   │   ├── search_bar.py        # 搜索栏 (实时过滤)
│   │   ├── user_badge.py        # 当前用户 + 存储状态
│   │   └── draft_badge.py       # 草稿状态标记
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── settings_dialog.py   # 设置对话框
│   │   ├── publish_dialog.py    # 发布到 Asset Manager
│   │   └── save_dialog.py       # 保存草稿对话框 (右键/拖入)
│   └── resources/
│       ├── icons/
│       └── styles.qss
│
├── utils/
│   ├── __init__.py
│   ├── config.py                # 配置管理
│   ├── logger.py                # 日志
│   ├── nuke_utils.py            # Nuke API 工具函数
│   └── path_utils.py            # 路径处理
│
├── tests/
│   ├── __init__.py
│   ├── test_pg_store.py
│   ├── test_json_store.py
│   ├── test_sync.py
│   └── test_bridge.py
│
└── plan/
    └── asset_browser_rebuild.md ← 本文件
```

### 4.4 核心数据模型

#### PostgreSQL (browser schema)

```sql
CREATE SCHEMA IF NOT EXISTS browser;

-- 草稿资产 (不需要分组/分类了)
CREATE TABLE browser.drafts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,             -- 'template', 'image', 'video', 'script', 'other'
    file_path TEXT NOT NULL,
    file_size BIGINT,
    thumbnail_path TEXT,
    description TEXT,
    tags JSONB DEFAULT '[]',               -- e.g. '["噪点","纹理","灯光"]'
    metadata JSONB DEFAULT '{}',            -- 灵活扩展
    is_shared BOOLEAN DEFAULT false,        -- false = 仅自己可见
    is_favorite BOOLEAN DEFAULT false,      -- 收藏标记
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    published_to INTEGER,                   -- 对应 Asset Manager 的 asset_id
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_drafts_created_by ON browser.drafts(created_by);
CREATE INDEX idx_drafts_is_shared ON browser.drafts(is_shared);
CREATE INDEX idx_drafts_is_favorite ON browser.drafts(is_favorite);
CREATE INDEX idx_drafts_tags ON browser.drafts USING GIN (tags);
CREATE INDEX idx_drafts_type ON browser.drafts(type);
CREATE INDEX idx_drafts_name_trgm ON browser.drafts USING GIN (name gin_trgm_ops);
```

> **注意：** 取消了 `groups` 和 `categories` 表。扁平化的 drafts 表 + 搜索/过滤 替代了分类体系。新增 `is_favorite` 字段支撑收藏功能。

#### JSON 缓存结构 (扁平化)

```json
{
  "version": 2,
  "last_sync": "2026-06-05T17:30:00Z",
  "user": "frank",
  "drafts": [
    {
      "id": 101,
      "name": "film_grain_001",
      "type": "template",
      "file_path": "/jobs/vfx001/drafts/film_grain_001.nk",
      "thumbnail_path": "...",
      "tags": ["噪点", "胶片"],
      "is_shared": false,
      "is_favorite": true,
      "created_by": "frank",
      "published_to": null,
      "created_at": "2026-06-05T10:00:00Z"
    }
  ]
}
```

#### 存储抽象接口

```python
class DraftStorage(ABC):
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

> filter 参数可选值: "all", "mine", "shared", "favorites", "published"

---

## 5. 技术决策

### 5.1 存储方案

| 维度 | JSON (离线兜底) | PostgreSQL (主力) |
|------|----------------|-------------------|
| 公司环境多用户 | ❌ | ✅ 连接池并发 |
| 权限控制 | ❌ | ✅ `created_by` 隔离 |
| 离线可用 | ✅ | ❌ 依赖网络 |
| 查询能力 | ❌ 全量过滤 | ✅ SQL + JSONB 索引 |
| 实现复杂度 | 低 | 中 |

### 5.2 技术栈版本

| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.11+ | Nuke 16+ 内置版本，享受最新语言特性 |
| **PySide6** | 6.x | 纯 PySide6，不做 PySide2 回退兼容 |
| **Nuke** | 16+ | 目标 Nuke 版本，使用最新 API |
| **psycopg2** | 2.9+ | PostgreSQL 驱动 (或 psycopg3) |

> **设计决策:** 这是面试作品，使用最新技术栈展示了申请人跟踪行业最新版本的能力。不做向后兼容意味着代码更简洁、更现代化、无历史包袱。

### 5.3 缩略图策略

| 文件类型 | 方案 |
|----------|------|
| 单帧图片 (exr/dpx/png/jpg) | PySide QPixmap 直接加载 |
| 图片序列 | 取中间帧 |
| 视频 (mov/mp4) | ffmpeg 抽取关键帧 |
| Nuke Script (.nk) | 用户自选封面帧 / 默认图标 |
| 其他 | 默认图标 + 类型标记 |

### 5.4 与 Asset Manager 的 API 协议

```
GET    /api/v1/assets?show=X&seq=Y&shot=Z   # 查询正式资产
GET    /api/v1/assets/<id>                    # 资产详情
POST   /api/v1/assets                         # 创建正式资产 (发布)
```

### 5.5 配置管理

```
优先级: 环境变量 > 配置文件 > 默认值

环境变量:
  AM_PG_HOST=localhost
  AM_PG_PORT=5432
  AM_PG_DB=pipeline_db
  AM_PG_USER=frank
  AM_PG_PASSWORD=

配置文件:
  ~/.config/asset_browser/config.yaml
```

---

## 6. 展示亮点

| 展示点 | 观众感知 | 技术底子 |
|--------|----------|----------|
| 多人共享草稿库 | "团队协作" | PostgreSQL 多用户并发 |
| 搜索即所得 | "用户体验好" | 实时防抖搜索 |
| 个人/共享/收藏隔离 | "权限意识" | created_by + is_shared + is_favorite |
| 离线也能用 | "生产环境可靠" | JSON 缓存 + 自动同步 |
| 右键保存 Node Graph 节点 | "懂 Nuke" | Nuke API + 菜单集成 |
| 一键发布到管线 | "全流程思维" | Bridge 层对接 Asset Manager |

---

## 7. 实施阶段

### 阶段 0: 项目骨架 + 存储抽象层

- 目录结构 ✓ (已完成)
- 配置管理 / 日志 / 数据模型 / 存储层实现

### 阶段 1: UI 核心

- 搜索栏 (实时过滤)
- 侧边栏过滤面板
- 缩略图网格 (右键菜单)
- 主窗口集成

### 阶段 2: Nuke 集成

- Menu 注册 / 快捷键
- Node Graph 右键 → 保存草稿
- 拖拽导入导出

### 阶段 3: Asset Manager 桥接

- API 客户端
- 发布对话框 + 同步引擎

### 阶段 4: 打磨

- 样式 / 图标 / 错误处理 / 性能 / 文档
