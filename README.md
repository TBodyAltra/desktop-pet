# 桌面宠物 (Desktop Pet)

一只住在 Windows 桌面上的**像素风小猫**，透明置顶、可拖动，会自己散步、打盹，双击还会冒出爱心。

![Desktop pet preview](docs/preview.svg)

## 功能

### 基础互动
- 透明无边框窗口，始终置顶
- 左键拖动移动位置
- 双击抚摸，触发开心动画
- 右键菜单：暂停/继续、重置位置、退出
- 系统托盘图标，关闭窗口后仍可从托盘唤回
- 自动行为：待机、散步、睡觉

### 程序员模式
- **前台窗口感知**：切换窗口时猫会立刻改变行为（打盹 / 踱步 / 溜达）
- **全局快捷键** `Ctrl+Alt+P`：显示/隐藏宠物

### 更多玩法
- **三种猫品种**：橘猫 Tabby / 黑白 Tuxedo / 暹罗 Siamese
- **随机掉落**：经验球和小鱼干会飘出来，点击收集
- **打网球**：右键菜单开启，和猫来回击球，看能连续打多少拍

## 环境要求

- Windows 10 / 11
- Python 3.10 或更高版本

## 快速开始

1. 克隆仓库：

```bash
git clone git@github.com:TBodyAltra/desktop-pet.git
cd desktop-pet
```

2. 双击 `run.bat`，或在 PowerShell 中执行：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

首次运行会自动创建虚拟环境并安装依赖。

### 直接下载 EXE

无需安装 Python，可在 [Releases](https://github.com/TBodyAltra/desktop-pet/releases) 页面下载打包好的 `DesktopPet.exe`，双击即可运行。

## 操作说明

| 操作 | 效果 |
|------|------|
| 左键拖动 | 移动宠物 |
| 左键双击 | 抚摸（开心动画 + 可能掉落物品） |
| 左键拖动后快速甩出 | 把猫甩飞，落地弹跳后开心 |
| 光标靠近猫 | 猫会转头小跑过来追你 |
| 左键点击掉落物 | 收集并冒爱心 |
| 右键 → 打网球 | 展开球场，和猫打网球 |
| 网球模式下左键 | 点击球附近把球击回 |
| 右键 → 结束网球 | 退出网球，恢复小窗 |
| 右键 | 打开菜单（换品种、暂停、重置） |
| `Ctrl+Alt+P` | 显示/隐藏宠物 |
| 托盘双击 | 显示宠物 |

## 项目结构

```
desktop-pet/
├── main.py              # 程序入口
├── pet/
│   ├── behavior.py      # 行为状态机
│   ├── dev_context.py   # 前台窗口检测
│   ├── drops.py         # 经验球 / 小鱼干掉落
│   ├── hotkeys.py       # 全局快捷键
│   ├── sprites.py       # MC 方块猫绘制
│   ├── tennis.py        # 网球互动
│   └── window.py        # 透明窗口与托盘
├── run.bat              # Windows 一键启动
└── requirements.txt
```

## 技术栈

- Python 3
- [PySide6](https://doc.qt.io/qtforpython/)（Qt for Python）

## 许可证

MIT License
