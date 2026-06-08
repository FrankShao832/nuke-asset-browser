# Nuke Asset Browser v2.0.0 — 全项目技术地图

> 一份帮你快速理解整个项目的导航文档  
> 读完它，你就知道代码在哪、为什么这样写、阅读顺序

---

## 一、项目定位 —— 一句话

> **Nuke 内部的"共享便利店"**  
> 合成师随手浏览素材、上传临时工具的轻量管理器，草稿完善后可一键升格为管线正式资产。

### 使用者视角

```
[打开浏览器] → [搜索/过滤找到草稿] → [悬停预览]
                                    → [双击导入 Nuke]
                                    → [拖入 Node Graph]
                                    → [右键收藏/删除]
[在 Nuke 中选中节点] → [右键保存到浏览器]
```

---

## 二、脑图 —— 技术架构全景

```
                    ┌──────────────────────────────────┐
                    │        main.py (唯一入口)          │
                    │  独立启动 / Nuke 插件 / 右键保存    │
                    └───────────┬──────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
   │    UI 层     │     │   Core 业务层  │     │    DB 存储层  │
   │  (PySide6)   │     │  (纯 Python)  │     │  (psycopg2)  │
   ├─────────────┤     ├──────────────┤     ├──────────────┤
   │ main_window │     │ models.py    │     │ base.py      │
   │             │     │  Draft 模型   │     │  DraftStorage│
   │ thumbnail_  │     │  Mock 数据    │     │  (ABC 接口)  │
   │ grid.py     │     │              │     │              │
   │ FlowLayout  │     │ search.py    │     │ pg_store.py  │
   │             │     │  搜索/过滤    │     │  PG 实现     │
   │ sidebar_    │     │  排序引擎     │     │              │
   │ filter.py   │     │              │     │ json_store.py│
   │             │     │ thumbnail.py  │     │  离线兜底     │
   │ search_bar  │     │  缩略图生成   │     │              │
   │             │     │  EXR/DPX/MOV │     │ connection.py│
   │ save_       │     │  序列/视频    │     │  连接池管理   │
   │ dialog.py   │     │              │     │              │
   │             │     │ sequence.py  │     │ schema.py    │
   │ settings_   │     │  序列检测     │     │  建表 + 迁移  │
   │ dialog.py   │     │              │     │              │
   │             │     │              │     │ sync.py      │
   │ toast.py    │     └──────────────┘     │  自动选择+同步│
   │ 通知系统     │                         └──────────────┘
   │             │
   │ theme.py    │           ┌──────────────────┐
   │ 统一样式     │           │    Bridge 桥接层   │
   └─────────────┘           │  (Phase 4 预留)    │
          │                  │                    │
          ▼                  │ api_client.py     │
   ┌─────────────┐           │ context.py        │
   │ Nuke 集成    │           │ sync_engine.py    │
   │ nuke_utils  │           └──────────────────┘
   │ 菜单/拖拽   │
   └─────────────┘
```

---

## 三、代码阅读顺序 —— 从哪开始看

我给了一个**五步阅读法**，按这个顺序看代码，逻辑是顺着长出来的：

### 🔹 第一步：数据模型 — 万物之始

| 文件 | 为什么先读它 |
|------|-------------|
| `core/models.py` | 核心中的核心。`Draft` 是一个 `dataclass`，项目里所有数据都是它——你理解了 Draft，就理解了整个项目的数据流动 |
| `__version__.py` | 就 5 行，看一眼就行 |

**重点理解：**
```python
@dataclass
class Draft:
    id: int              # 自增主键
    name: str            # 草稿名
    draft_type: str      # template/image/video/script/other
    path: str            # 文件实际路径
    author: str          # 作者名
    status: str          # draft/published/modified
    visibility: str      # private/shared
    favorite: bool       # 收藏
    ...
    frame_range: str     # 序列帧范围 "1001-1048"
    sequence_pattern: str # 序列文件名模板 "render_%04d.exr"
```

> 💡 **技巧：** `@dataclass` 自动生成 `__init__`、`__repr__`、`__eq__`。用 `field(default_factory=list)` 给可变类型默认值，避免多个实例共享同一个列表。

---

### 🔹 第二步：入口文件 — 程序的启动方式

| 文件 | 为什么读它 |
|------|-----------|
| `main.py` | 入口即目录。三种运行模式（独立/Nuke 插件/脚本）都在这里 |

**重点理解：**
```python
# 模式 A: python -m asset_browser.main  → run_standalone()
# 模式 B: import asset_browser.main      → install_menu() + open_browser()
# 模式 C: 在 Nuke 中选中节点 → 右键 "Save to Asset Browser" → save_selection_as_draft()
```

> 💡 **技巧：** `sys.path.insert(0, _PARENT_DIR)` 保证包可发现。  
> `install_menu()` 注册到 Nuke 菜单用 `nuke.menu("Nuke").addCommand()`。  
> `_windows` 单例字典保证浏览器只会开一个窗口。

---

### 🔹 第三步：UI 层 — 你能看到的全部

按**从上到下、从外到内**的顺序读：

| 阅读顺序 | 文件 | 理解要点 |
|---------|------|---------|
| **3.1** | `ui/theme.py` | 全局颜色、字号、样式表 — 整个界面"长什么样"全在这里 |
| **3.2** | `ui/main_window.py` | 主窗口骨架 — 顶栏 → 网格+侧边栏 → 状态栏。**所有组件的粘合剂** |
| **3.3** | `ui/widgets/search_bar.py` | 搜索框 — 300ms 防抖，`QTimer.singleShot` 延迟触发 |
| **3.4** | `ui/widgets/sidebar_filter.py` | 右侧面板 — Filter 按钮组 + Sort 按钮组 + Upload 按钮 |
| **3.5** | `ui/widgets/thumbnail_grid.py` | **最大的文件 (748 行)** — 核心组件！自定义 FlowLayout + ThumbnailCard |
| **3.6** | `ui/widgets/draft_badge.py` | 状态标记（Draft/Published/Modified） |
| **3.7** | `ui/widgets/user_badge.py` | 左上角用户信息 |
| **3.8** | `ui/widgets/toast.py` | Toast 通知系统 — 用 `QLabel` 自己画的 |
| **3.9** | `ui/dialogs/save_dialog.py` | 保存草稿对话框 |
| **3.10** | `ui/dialogs/settings_dialog.py` | 设置对话框（3 个 Tab） |

**核心设计思路：**

```
MainWindow (指挥者)
  ├── UserBadge (左上)
  ├── SearchBar (右上)
  ├── ThumbnailGrid (中央 80%)
  │     ├── FlowLayout (自定义布局管理器)
  │     └── ThumbnailCard × N (每张卡片)
  │           ├── DraftBadge (状态标签)
  │           ├── 缩略图 (动态加载)
  │           └── 名称 + 作者 + 收藏星
  ├── SidebarFilter (右侧 260px)
  │     ├── 5 个 Filter 按钮
  │     ├── 2 个 Sort 按钮
  │     └── Upload 按钮
  └── StatusBar (底部)
        ├── 状态文字 (all/latest/过滤条件)
        ├── 进度条 (居中，导入时显示)
        ├── 计数 (Showing X of Y)
        └── 存储后端 (🟢 PG / 🟡 JSON / 🔴 Memory)
```

> 💡 **技巧：** 用 `Signal`（`draft_selected`、`draft_activated`、`delete_requested`）解耦组件。UI 组件不知道数据存在哪里、怎么存的——它们只管发信号。

---

### 🔹 第四步：Core 业务层 — 真正的"大脑"

| 阅读顺序 | 文件 | 理解要点 |
|---------|------|---------|
| **4.1** | `core/search.py` | 搜索+过滤+排序引擎 — 全部在内存中执行 |
| **4.2** | `core/thumbnail.py` | **第二大的文件 (684 行)** — 缩略图生成全家桶 |
| **4.3** | `core/sequence.py` | 序列检测引擎 — 识别帧序列文件 |

**`core/search.py` 重点：**

```python
class DraftSearch:
    def search(self) -> list[Draft]:
        # 1. 按 keyword 过滤 name/description/tags
        # 2. 按 filter 过滤 (全部/我的/共享/收藏/已发布)
        # 3. 按 sort 排序 (latest/hottest)
        # 返回过滤后的 Draft 列表
```

**全部在内存中**进行，不依赖数据库——因为数据量本身很小（几十到几百条）。

> 💡 **技巧：** `latest` 排序按 `d.id DESC`（自增 ID 天然有序），而不是 `created_at`，避免同天创建的草稿排序不稳定。

**`core/thumbnail.py` 重点——缩略图加载 5 级链路：**

```
get_thumbnail(draft_id, path, draft_type) 需要一张图
  │
  ├─ 1️⃣ path 是本地文件? → QPixmap(path)
  ├─ 2️⃣ 缓存中有? → thumbnails/{draft_id}.png
  ├─ 3️⃣ 序列类型? → 取第一帧生成缩略图
  │   └─ EXR? → OpenEXR + numpy → gamma 2.2 → QImage
  │   └─ DPX? → ffmpeg 解码 → raw RGB → QImage
  ├─ 3b️ 视频类型? → ffmpeg 首帧 → QImage
  ├─ 4️⃣ 直接是图片文件? → QPixmap
  └─ 5️⃣ 都不行 → 纯色块 + 图标（保底方案）
```

> 💡 **技巧：**
> - EXR 色彩空间用**纯 gamma 2.2**（与 Nuke Viewer 一致），不做自动曝光
> - EXR 负值像素需要 `np.maximum(rgb, 0.0)` clamp，否则 gamma 产生 NaN
> - DPX 用 ffmpeg 解码，不做额外 gamma——ffmpeg 已经转为 sRGB
> - MOV 视频用 `fps={count/duration}` filter 均匀抽帧（不是 `select=mod(n,100)`）

**`core/sequence.py` 重点——序列检测：**

```python
def detect_sequences(folder_path) -> list[SequenceInfo]:
    # 1. 扫描文件夹中所有文件
    # 2. 文件名中提取数字后缀 (如 render_1001.exr → 1001)
    # 3. 按 basename+padding 分组
    # 4. 同组连续数字合并为序列
    # 返回 [SequenceInfo(folder, pattern, start, end, ...)]
```

> 💡 **技巧：** `SequenceInfo.nuke_pattern()` 生成 Nuke 认识的格式 `folder/render_%04d.exr 1001-1048`。

---

### 🔹 第五步：DB 存储层 — 数据怎么存

| 阅读顺序 | 文件 | 理解要点 |
|---------|------|---------|
| **5.1** | `db/base.py` | 抽象基类 `DraftStorage`——定义 CRUD 接口 |
| **5.2** | `db/connection.py` | PG 连接池——延迟初始化 + 优雅降级 |
| **5.3** | `db/schema.py` | 建表 + 迁移 SQL |
| **5.4** | `db/pg_store.py` | PostgreSQL 实现 |
| **5.5** | `db/json_store.py` | JSON 文件兜底 |
| **5.6** | `db/sync.py` | 自动选择后端 + 数据同步 |

**存储架构：** 双后端 + 抽象基类

```
              ┌──────────────────┐
              │  DraftStorage    │  ← 抽象基类 (接口契约)
              │  (ABC)           │
              └────────┬─────────┘
                       │ 继承
               ┌───────┴───────┐
               ▼               ▼
        ┌────────────┐  ┌────────────┐
        │ PGStorage  │  │ JSONStorage│
        │ (生产主力)  │  │ (离线兜底)  │
        │ PostgreSQL │  │  JSON 文件  │
        │ 16.13      │  │ ~/.nuke/   │
        │ pipeline_db│  │ drafts.json│
        └────────────┘  └────────────┘
                ▲               ▲
                │               │
               ─┴── get_storage() ──┴─
                    PG 优先 → JSON 降级 → 纯内存
```

> 💡 **技巧：**
> - 用 `psycopg2.SimpleConnectionPool` 管理连接，`min=1, max=5`
> - 连接失败只 log warning，不抛异常——程序继续运行
> - `RealDictCursor` 让查询返回 dict 行，字段名直接访问
> - JSON 用 `dataclasses.asdict()` 序列化，`Draft(**data)` 反序列化
> - `sync.py` 的 `sync_to_pg()` 把 JSON 数据全量迁移到 PG（幂等）

**`_init_storage()` 在 MainWindow 中的决策链路：**

```python
def _init_storage(self):
    ensure_schema()        # 建表（幂等）
    try:
        self._store = PGDraftStorage()    # 优先 PG
    except Exception:
        try:
            self._store = JSONDraftStorage()  # 降级 JSON
        except Exception:
            self._store = JSONDraftStorage(...)  # 最后纯内存
    # 状态栏显示 🟢 / 🟡 / 🔴
```

---

## 四、技术选项与决策依据

### 4.1 为什么选 PySide6 不选 PySide2？

| | PySide2 | PySide6 |
|--|---------|---------|
| **目标 Nuke** | Nuke 12-15 | Nuke 16+ |
| **Qt 版本** | Qt 5 | Qt 6 |
| **Python** | 3.7-3.9 | 3.11+ |
| **结论** | 不向后兼容 | ✅ **选择** |

**决策逻辑：** 目标用户已升级到 Nuke 16+，Python 3.11+。不做旧版本兼容可以省去大量 `try/except` 条件分支代码。

### 4.2 为什么 UI 优先，不做 MVC？

```
传统方式:   DB → 存储层 → 业务层 → UI (埋两周才看到窗口)
UI 优先:   数据模型 → UI (Mock 数据) → 存储层替换 (第一天就看到窗口)
```

**理由：**
1. 你最擅长 UI，先出效果成就感足
2. Mock 数据隔离 UI 和后端，两边不耽误
3. `DraftStorage` 基类保证 UI 切换后端时**零代码改动**

### 4.3 为什么 FlowLayout 不用 QTableWidget？

| | QTableWidget | FlowLayout (自定义) |
|--|-------------|-------------------|
| **布局灵活性** | 固定行列 | 自动换行，卡片不等宽 |
| **卡片样式** | 受 Table cell 限制 | 完全自由 (QLabel/QWidget) |
| **性能** | 大量 cell 时卡 | 只创建可见卡片 |
| **自定义** | 难 (要 subcalss model/delegate) | 易 (直接控制 layout) |

**决策逻辑：** 一张卡片是一个 `QWidget`（不是 cell），可以自由叠加 `DraftBadge`、缩略图、文字等子元素。

### 4.4 为什么 PostgreSQL + JSON 双后端？

| 场景 | 后端 | 理由 |
|------|------|------|
| 公司多人环境 | PG | 并发安全，权限隔离，连接池 |
| 个人离线 | JSON | 不需要装 PG，开机即用 |
| 断线应急 | JSON | PG 断线自动降级，不弹红错 |

### 4.5 为什么缩略图不用 Qt 内置图像插件？

Qt 的 `QImageReader` **不支持**：
- EXR（OpenEXR Qt plugin 需要额外编译）
- DPX（Qt 不支持高位深+不同端序的 DPX）

**所以自己造轮子：**
- EXR → `OpenEXR` + `numpy` 库（pip 安装即可）
- DPX → `ffmpeg`（系统自带，无需额外依赖）
- MOV 视频 → `ffmpeg`（首帧缩略图 + 等间隔抽帧）

### 4.6 为什么不用 Web 技术（Electron/Flask）？

Nuke 是**原生 Qt 应用**。最轻量的做法是用它自带的 PySide6，不走 HTTP 通信、不启动额外的 Web 服务。一个窗口，一个进程，搞定。

---

## 五、关键技术要领

### 5.1 自定义 FlowLayout

```python
class FlowLayout(QLayout):
    """自动换行的流式布局"""
    
    def addItem(self, item):
        self._items.append(item)
    
    def hasHeightForWidth(self): return True
    
    def heightForWidth(self, width):
        # 计算给定宽度下需要多高
        # 遍历 item，每行放满就换行
        ...
    
    def invalidate(self):
        # 关键修复！重置 item geometry 避免闪烁
        for item in self._items:
            item_w, item_h = item.widget().sizeHint().toTuple()
            item.setGeometry(QRect(-9999, -9999, item_w, item_h))
        super().invalidate()
```

**`invalidate()` 修复：** Qt 不会自发触发自定义 Layout 的 invalidate。切换过滤器后旧 geometry 残留导致最后一枚卡片跳到 (0,0)。显式重置 geometry 解决。

### 5.2 缩略图懒加载

```python
# 只在卡片进入视口时才加载缩略图
def load_thumbnail_if_visible(self):
    viewport = self.parent().parent().viewport()  # QScrollArea viewport
    card_pos = self.mapTo(viewport, QPoint(0, 0))
    card_rect = QRect(card_pos, self.size())
    visible_rect = viewport.rect()
    
    if visible_rect.intersects(card_rect):
        if not self._thumb_loaded:
            self._load_thumbnail()  # 真正解码图片
```

- 首次显示 + 滚动时触发
- LRU 缓存（200 上限），避免反复读盘
- `QTimer.singleShot(50)` 延迟触发，确保布局完成后再检测

### 5.3 300ms 防抖搜索

```python
class SearchBar(QLineEdit):
    search_text_changed = Signal(str)
    
    def textChanged(self, text):
        # 取消上次的定时器
        # 重新设一个 300ms 后的定时器
        # 300ms 内没有新输入 → 发射信号
        self._debounce_timer.start(300)
```

### 5.4 悬停播放

```python
class ThumbnailCard(QWidget):
    # 鼠标移入 → 24fps 定时器轮播序列帧
    # 鼠标移出 → 停止播放，恢复静态缩略图
    # 首次播放时边播边缓存 PNG，之后秒切
    
    def enterEvent(self, event):
        self._playback_index = 0
        self._playback_timer.start(42)  # 1000/24 ≈ 42ms
    
    def leaveEvent(self, event):
        self._playback_timer.stop()
        self._thumb_label.setPixmap(self._static_thumb)
```

### 5.5 Toast 通知系统

```python
class Toast(QLabel):
    """自已用 QLabel 画的浮动通知，不用 QMessageBox"""
    
    @classmethod
    def appear(cls, parent, text, level=INFO):
        toast = cls(parent, text, level)
        toast.show()
        toast.raise_()            # 置顶
        # 2 秒后自动关闭
        QTimer.singleShot(2000, toast.close)
```

> ⚠️ **踩坑：** 自定义 `show()` 方法覆盖了 `QWidget.show()` → 改名为 `appear()`。

### 5.6 macOS Drag-Drop 重绘

```
问题：macOS 拖拽上下文中 repaint()/processEvents() 无效
解决：QTimer.singleShot(0, callback) 把实际工作推迟到事件循环恢复后
```

```python
def dropEvent(self, event):
    self._pending_urls = [u for u in urls if u.isLocalFile()]
    self.drop_started.emit()          # 先显示进度条
    QTimer.singleShot(0, self._process_pending_drops)  # 延迟扫描
    event.acceptProposedAction()
```

### 5.7 优雅降级 —— 不崩溃的哲学

整个项目遵循"不因异常而崩溃"的原则：

| 场景 | 降级行为 |
|------|---------|
| PG 连不上 | → JSON 文件 → 纯内存 |
| 缩略图解码失败 | → 纯色块占位 |
| 文件不存在 | → 空状态提示 |
| ffmpeg 未安装 | → DPX/视频降级为占位图 |
| 配置读取失败 | → 默认值兜底 |

---

## 六、关键文件大小参考

| 文件 | 行数 | 复杂度 | 阅读难度 |
|------|------|--------|---------|
| `ui/widgets/thumbnail_grid.py` | 748 | ⭐⭐⭐⭐⭐ | **最难** |
| `core/thumbnail.py` | 684 | ⭐⭐⭐⭐ | 难（格式解码知识） |
| `ui/main_window.py` | 434 | ⭐⭐⭐ | 中等（粘合剂） |
| `ui/theme.py` | 347 | ⭐⭐ | 简单（全是样式） |
| `ui/widgets/sidebar_filter.py` | 237 | ⭐⭐ | 简单 |
| `db/connection.py` | 226 | ⭐⭐⭐ | 中等（连接池） |
| `db/pg_store.py` | 195 | ⭐⭐ | 简单（SQL CRUD） |
| `utils/config.py` | 187 | ⭐⭐ | 简单 |
| `ui/widgets/thumbnail_grid.py` 的 `FlowLayout` | ~120 | ⭐⭐⭐⭐ | 最难的部分（自定义 QLayout） |

---

## 七、技术栈一览

| 组件 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | Nuke 16+ 内置 |
| **PySide6** | 6.11.1 | GUI 框架 |
| **psycopg2** | 2.9.12 | PostgreSQL 驱动 |
| **OpenEXR** | 3.4.12 | EXR 缩略图解码 |
| **numpy** | 2.4.6 | EXR 像素处理 |
| **ffmpeg** | 系统自带 | DPX/MOV 缩略图解码 |
| **pytest** | 9.0.3 | 单元测试 |
| **Git** | — | `main` + `dev` 分支 |
| **Conda** | — | 虚拟环境管理 |

---

## 八、读代码的最佳路线（按目标）

### 如果你想理解 整体架构
```
models.py → main.py → main_window.py → theme.py → search.py → base.py
```
30 分钟就能搭起框架。

### 如果你想改 UI
```
theme.py → main_window.py → thumbnail_grid.py → sidebar_filter.py → search_bar.py → toast.py
```
先看 `theme.py` 的 `Color` 和 `Styles`，再追进具体组件。

### 如果你想改存储
```
base.py → pg_store.py → json_store.py → connection.py → schema.py → sync.py
```
`DraftStorage` 接口定义在 `base.py`，猜也能猜到方法名，读起来很顺。

### 如果你想加文件格式支持
```
thumbnail.py → sequence.py → thumbnail_grid.py (ThumbnailCard)
```
在 `thumbnail.py` 的 `get_thumbnail()` 里加解码分支，然后在 `thumbnail_grid.py` 的 `_draft_from_drop()` 里加类型判断。

### 如果你想加新的 UI 功能
```
main_window.py → 新组件 → main_window.py 连接 signal
```
找 `_connect_signals()` 看看现有的 signal 连接模式，照葫芦画瓢。

---

> **文档版本：** v1.0  
> **生成时间：** 2026-06-08  
> **适用代码库：** [Nuke Asset Browser v2.0.0](https://github.com/your-repo/asset_browser)
