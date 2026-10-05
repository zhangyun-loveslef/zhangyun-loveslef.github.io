# 个人主页 · 个人简介与生活随笔

一个纯静态的个人网站，已部署到 **GitHub Pages**（https://zhangyun-loveslef.github.io/）。深色书卷风，含个人简介、生活随笔（标签筛选 + 阅读弹层）、联系方式三个板块，桌面与移动端自适应。

**核心思路**：内容都放在「可编辑的源文件」里（随笔用 Markdown、个人信息用 JSON），改完运行一次 `build.bat`，`index.html` 就会自动重新生成。你不用碰 HTML。

## 文件结构

```
personal-website/
├── index.html          # 网站成品（构建后自动更新，无需手动改）
├── site-config.json    # 个人信息 / 联系方式 / 关于我（改这里）
├── images/             # 图片，随笔里用 ![说明](images/图片名) 引用
├── essays/             # 生活随笔，每个 .md 一篇（用 Typora 编辑）
│   ├── 慢下来的时光.md
│   ├── 深夜里的代码.md
│   ├── 城市与远山.md
│   └── 读书记.md
├── build.py            # 构建脚本（读取上面的源文件 → 生成 index.html）
├── build.bat           # 双击即可运行 build.py
├── .gitignore          # 已忽略 _shots/ 自检截图
└── README.md
```

## 日常更新流程（3 步）

1. **改内容**：用 Typora 打开 `essays/` 里的 `.md` 随笔；个人信息/联系方式改 `site-config.json`。
2. **构建**：双击 `build.bat`（或命令行 `python build.py`），会重新生成 `index.html`。
3. **推送**：用 TortoiseGit（右键 → Git Commit → Git Push）或命令行推送到 GitHub，约 1 分钟后线上更新。

## 怎么写一篇随笔

在 `essays/` 新建一个 `.md` 文件，格式如下（用 Typora 编辑即可，`---` 之间是标题信息）：

```
---
title: 文章的标题
date: 2026-10-01
tag: 生活
---

第一段文字……

第二段文字……（段落之间用空行隔开）

第三段文字……
```

- `tag` 可写：生活 / 工作 / 旅行 / 阅读 / 其它（网站会自动生成筛选标签）
- `excerpt`（摘要）不写会自动取第一段前 60 字；想自定义可在 front matter 里加 `excerpt: 你自己的摘要`
- 文件名就是文件名，不影响显示，显示标题以 `title` 为准

改完运行 `build.bat`，随笔会自动按日期从新到旧排列。

## 怎么插入图片

1. 把图片文件放进 **`images/`** 文件夹（支持 jpg / png / gif / webp / svg）。
2. 在随笔里**单独一行**写图片引用：`![说明文字](images/图片名.jpg)`。会居中显示，说明文字作为图注。
3. 运行 `build.bat` 重新生成即可。

> 便捷设置：Typora 里打开 **文件 → 偏好设置 → 图像**，把「插入图片时复制到指定路径」设为 `./images`、链接方式选「相对路径」。之后直接拖图进随笔，会自动存到 `images/` 并生成引用。

## 改个人信息 / 联系方式

编辑 `site-config.json`，各字段含义一目了然：`profile`（名字、头像字、一句话介绍）、`contact`（邮箱、GitHub、站点）、`about`（关于我的三段介绍 + 右侧几个快速信息）。改完运行 `build.bat`。

## 部署说明（仅首次）

仓库 `zhangyun-loveslef.github.io` 已开启 GitHub Pages，`main` 分支根目录即为网站，推送后自动发布，无需额外设置。
