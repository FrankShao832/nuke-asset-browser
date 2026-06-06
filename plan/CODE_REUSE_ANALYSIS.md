# 旧版代码可复用分析报告

> 日期: 2026-06-05  
> 分析范围: `asset_browser_bak/` + `backups_01/`

---

## 一、可直接复用的组件

### 🔄 `backups_01/browser_thumbnail.py` (122行) — 缩略图显示控件

```
BrowserThumbnail(QWidget)
├── 缩略图 QLabel 显示 (260x180)
├── 文件名 QLabel 显示 (底部)
├── 文件类型 → 图标映射 (.nk → nuke图标, .obj/.abc/.fbx → mesh图标)
├── 加载中 GIF 动画 (QMovie)
├── 透明度效果 (QGraphicsOpacityEffect)
└── QGridLayout 布局 (thumbnail + filename)
```

**复用方式：** 直接继承，数据源从文件路径改为 Draft 对象

---

### 🔄 `backups_01/browser_container.py` (1033行) — 缩略图网格容器

```
BrowserTable(QTableWidget)
├── calculate_columns()       → 根据容器宽度自动计算列数
├── modify_tables()           → 表格样式设置 (无网格/无表头/拖拽启用)
├── context_menu()            → 右键菜单模板 (Metadata/收藏/删除/打开目录)
├── load_thumbnails()         → 缩略图加载逻辑
├── load_executables()        → ffmpeg/ffprobe 路径发现
├── update_favourite_json()   → 收藏操作
├── re_cache()                → 重新生成缩略图
├── delete_confirmation()     → 安全删除弹窗
├── QThreadPool 异步加载       → 缩略图不阻塞 UI
└── pyseq 图片序列支持         → 序列帧识别
```

**复用方式：** 重构为 `thumbnail_grid.py`，保留交互逻辑，数据源替换

---

### 🔄 `backups_01/browser_ui_settings.py` (277行) — 设置面板

```
UiSettings(QFrame)
├── GroupBox 布局 (General / FFmpeg / JSON路径 / Proxy)
├── QLineEdit + Browse按钮 (目录选择)
├── Always-on-top 复选框
├── 线程数设置
└── 字号/对齐样式模板
```

**复用方式：** 继承 UI 布局，配置项替换为 PG 连接 + JSON 路径等

---

### 🔄 `backups_01/browser_template.py` (195行) — 模板编辑对话框

```
Template(QWidget)
├── 缩略图预览 (左侧 160x160)
├── FormLayout (名称/描述/标签)
├── QComboBox (分组/分类选择)
└── 600x200 固定尺寸弹窗
```

**复用方式：** 继承 FormLayout 布局，去掉分组/分类，改为标签输入

---

### 🔄 `backups_01/browser_ui_operation.py` (1011行) — UI 操作控制器

```
UpdateUI
├── toggle_search()                 → 搜索栏显示/隐藏
├── load_groups_ui()                → 填充下拉框
├── load_category_ui()              → 填充树形分类
├── enable_settings_ui/content_ui() → 视图切换模式
├── trigger_settings_signals()      → 设置信号绑定模式
├── warning_popup()                 → 通用警告弹窗
└── save_settings() / reset_settings() → 配置保存/重置
```

**复用方式：** 作为操作逻辑参考，重写为新 MainWindow 的 controller

---

## 二、参考借鉴的组件

### 📌 `asset_browser_bak/assets_browser.py` (99行) — 主面板入口

```
AssetsBrowserPanel(QWidget)
├── 窗口配置 (1200x600, minimum 1200x600, topmost)
├── 布局: 左(缩略图网格) | 右(分组选择+分类树)
├── group_selection_changed() → 切换分组
└── category_selection_changed() → 选择分类 (stub)
```

**参考点：** 窗口初始化和布局的组织方式，行为模式改为新设计

---

### 📌 `backups_01/browser_database.py` (133行) — 数据库操作

```
BrowserDatabase
├── ingest_to_json()     → 数据写入
├── read_from_json()     → 数据读取
├── remove_category()    → 删除
├── update_category()    → 更新
└── update_items()       → 草稿项更新 (含收藏、发布状态)
```

**参考点：** CRUD 接口设计思路 (将被 DraftStorage 抽象层替代)

---

### 📌 `utils/browser_settings.py` / `backups_01/browser_settings.py` (各65行)

```
BrowserSettings
├── 自动创建 settings.json (如不存在)
├── 从 JSON 加载配置
├── 默认值 + 用户可覆盖
└── 配置路径: ~/Documents/Assets_Browser/preference/settings.json
```

**参考点：** 自动创建默认配置的模式 (将被新的 config.py 替代)

---

## 三、不使用的组件 (废弃)

| 文件 | 行数 | 废弃原因 |
|------|------|---------|
| `ui/browser_tree_widget.py` | 93 | 分类树 → 替换为侧边栏过滤 |
| `ui/browser_combobox_widget.py` | 70 | 分组下拉 → 替换为侧边栏过滤 |
| `database/browser_database.py` | 135 | JSON CRUD → 替换为 DraftStorage 抽象层 |
| `utils/browser_settings.py` | 65 | JSON 配置 → 替换为 config.py (YAML+环境变量) |

---

## 四、硬编码路径问题

旧版所有 icon 路径都存在硬编码:

```python
# ❌ 旧版问题
icon = QIcon('/Volumes/KirinTor/nuke_projects/nuke_dev/asset_browser/icons/settings.png')

# ✅ 新版方案
icon = QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'icons', 'settings.png'))
```

---

## 五、复用总结

| 优先级 | 文件 | 内容 | 复用方式 |
|--------|------|------|---------|
| 🔴 | `browser_thumbnail.py` | 缩略图显示控件 | 直接继承 |
| 🔴 | `browser_container.py` | 缩略图网格+右键+异步加载 | 重构继承 |
| 🟠 | `browser_ui_settings.py` | 设置面板UI布局 | 继承布局，换内容 |
| 🟠 | `browser_template.py` | 模板编辑对话框布局 | 继承 FormLayout |
| 🟡 | `browser_ui_operation.py` | 操作控制器模式 | 作为参考 |
| 🟡 | `browser_database.py` | CRUD 接口设计 | 接口思路参考 |
