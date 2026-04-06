# Logs 目录说明

本目录用于存放相机感知 Pipeline 的运行输出结果。

输出分为两类：

---

## 1️⃣ overlay/

用途：人工可视化验证

内容：
- 叠加检测框的图像
- track_id
- 原始分类结果（raw）
- 稳定后结果（stable）
- 置信度信息

作用：
- 快速验证主线是否跑通
- 调试检测 / 跟踪 / 稳定器逻辑
- PR 提交时截图展示效果

说明：
overlay 仅用于人工查看，不作为系统输入。

---

## 2️⃣ metrics/

用途：结构化语义输出（机器可读）

内容：
- header（时间戳、相机ID）
- status（fps 等运行状态）
- results（traffic_light / traffic_sign 等任务输出）

作用：
- CI 冒烟测试验证
- 离线评估
- 下游模块（如规划）读取
- 回归对比分析

说明：
metrics 输出格式属于系统对外协议，修改必须评审。

---

## 冒烟测试规则

运行：

    bash scripts/run_replay.sh

必须满足：
- 至少生成 1 张 overlay 图像
- 至少生成 1 个 metrics JSON 文件

否则视为主线功能异常。

---

## 清理说明

- `.gitkeep` 用于保持目录结构
- 可删除旧运行结果
- 不得随意修改目录结构

---

本目录是感知系统的稳定输出边界。
overlay 用于人工验证，metrics 用于系统验证。