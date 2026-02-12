# Contributing Guide (perception_stack)

本仓库用于 L4 自动驾驶相机感知能力开发，当前重点任务：
- Traffic Light（交通灯）
- Traffic Sign（交通标志）

目标原则：**主线永远可运行、可回放、可复现；功能通过短生命周期分支开发，PR 合入。**

---

## 1. 分支模型（Branching Model）

### 1.1 长期分支（长期存在）
- `main`：主线，**永远可运行 / 可回放 / 可发布**。只允许 PR 合入，禁止直接 push。
- `release/vX.Y`：里程碑版本，保证可复现（模型 + 配置 + 指标）。
- `hotfix/*`：紧急修复（从 `release/*` 或 `main` 拉出）。

> 可选：不建议使用 `develop`。若团队人数较多且合入频繁，可增设，但默认不启用。

### 1.2 短生命周期分支（开发完成后删除）
- `feat/tl-*`：交通灯功能（TL）
- `feat/ts-*`：交通标志功能（TS）
- `feat/core-*`：公共能力（sync/projector/stabilizer/publisher/common/schema）
- `fix/*`：问题修复
- `exp/*`：实验分支（不保证质量，原则上不合入 main；只 cherry-pick 可交付提交）

### 1.3 命名示例
- `feat/tl-detector-yolo`
- `feat/tl-stabilizer-hysteresis`
- `feat/ts-detector-smallobj`
- `feat/ts-parser-speedlimit`
- `feat/core-roi`
- `fix/tl-night-fp`

---

## 2. 代码目录与责任边界

### 2.1 任务代码（优先在任务目录内改动）
- `src/perception_stack/infer/detectors/traffic_light.py`
- `src/perception_stack/infer/detectors/traffic_sign.py`
- `src/perception_stack/stabilizer/*`
- `src/perception_stack/visualizer/*`

### 2.2 公共协议与框架（修改需更严格评审）
- `src/perception_stack/common/*`：数据结构与协议（FrameBundle / RawDetections / StableTrafficLight / StableTrafficSign）
- `src/perception_stack/sync/*`：同步与取数
- `src/perception_stack/projector/*`：ROI 与投影
- `src/perception_stack/publisher/*`：对外发布/落盘
- `configs/*`：运行开关、标定、模型配置、topic 定义

> 原则：任务分支尽量只改任务相关文件。  
> 如需修改输出 schema / topic / FrameBundle，请走 `feat/core-*` 分支，并更新回放与评测脚本。

---

## 3. 开发流程（Workflow）

### 3.1 拉分支
从 `main` 拉出功能分支：
```bash
git checkout main
git pull
git checkout -b feat/tl-detector-yolo
