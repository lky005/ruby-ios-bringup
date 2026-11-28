# 15 — GPU：内核驱动与用户态研究线

[English](../en/15-gpu.md) · **中文**

> 状态：**实验性**。内核面（0352/0360）已合并并经 CI 验证；用户态栈
> （Mesa PanVK、Metal-on-Vulkan 垫片）属于实验线，此章仅作记录。0360 内核
> **没有启动记录**：它与其他线一样受 patchset/exec-data 门禁，但从未刷入设备。

## 1. 栈结构

```text
iOS app（Metal）                         GL/Vulkan 应用
  │ Metal.framework                        │ libGLESv2 / libvulkan
  │ （研究垫片：AIR→SPIR-V）                │ （Mesa Panfrost/PanVK 移植）
  ▼                                        ▼
RubyGPU 服务（XNU kext：设备、电源、MMU、BO、提交、上下文）
  │ INTID487 IRQ、SG BO、逐 task 表面属主
  ▼
Mali-G68（MT6877 MFG，2×EE / 1×JS，job slot，16 KiB 页）
```

内核侧有两层：

- **0352** —— 只读探针 + 门控上电。dump Mali 寄存器窗口（GPU_ID、
  AS/JS_PRESENT、READY 位）、mfgcfg 窗口（CG/ASYNC/QCHANNEL/DEBUG/I2M）、
  SPM 状态窗口、TOP/infra bus-protect、MFG PLL，以及 pwrap 读通道上的
  MT6359P VPROC2/VSRAM_MD。由 `rubygpuprobe=1` 门控（默认关、不写、一次）。
  MFG2-5 上电路径由 `rubygpupwr=2` 门控（默认关）。
- **0360** —— 从实验线回收的驱动面（见 §2）。

## 2. 内核面（0360）

| 领域 | 文件 | 说明 |
|---|---|---|
| 驱动核心 | `iokit/Kernel/arm/RubyGPU.cpp/.h` | 设备发现、电源时序、MMU、BO 管理、提交、上下文生命周期；不主动写硬件 |
| IRQ | `RubyGPUIRQ.cpp/.h` | INTID487，job/fault 完成 |
| Userclient | `RubyGPUUserClient.cpp/.h`、`RubyGPUUserAPI.h` | Panfrost kmod 面语义子集：BO 创建/释放、VM 创建/绑定/解绑、提交、同步 |
| 表面 | `SweetSurface.cpp/.h` | 逐 task 属主：只有创建者 task 可把表面导入 BO；内核发布的显示表面永不可导入 |
| Metal 钩子 | `RubyGPU.cpp`（`IOAcceleratorES`） | 空 IORegistry 服务，供原生 Metal 插件发现；`MetalPluginName`/`MetalPluginClassName` 仅在 `rubymetalu=1` 时可设（默认关） |
| 诊断 | `IOUserClient.cpp`、`RubyGPU.cpp` | `rubygpudiag=1` 的 selector-8 跟踪与驱动 dump，console ring 限流，默认关 |
| 显示 | `SweetFramebuffer.cpp` | 默认 60 Hz 刷屏（`sweetfb_hz=10` 恢复旧节流）+ 驱动 commit 钩子 |
| CPU B4a | `pexpert` `SWEET.h`/`board_config.h`、`sched_clutch.c`、`sweet_sample.c` | AMP 面：两簇、Edge 默认放置（P 桶落首个 P 簇，UT/BG 落 boot 簇）、只读时钟探针。需 2 簇 ADT 才生效；仓库不提供 ADT，A78 簇维持 650 MHz（未 DVFS） |

BO 记账有上限（`rubygpubomax`、`rubygpuvmpages`）并配合用户态释放；实验线
稳定在 `live_buf=5 live_tex=31 imports=4`。

## 3. Mesa / PanVK 线（独立仓库，计划中）

- Mesa 27.0.0-devel pin `49f13b7`，iOS arm64 交叉构建；x86_64 主机侧生成
  v9 shader pregen，iOS 侧消费。
- Panfrost GL（GLES 3.1）已上设备；PanVK v9 使用 JimVulkan 派生的 v9
  用户态，共用同一 XNU kmod 后端。
- Gate A（x86_64 clean 构建，1212/1212 目标）与 Gate B（iOS 交叉）均 PASS；
  设备 GL 测试经面板表面原生 1080×2400 渲染。
- 打包形态：补丁 + 构建脚本 + pregen，不 vendor Mesa 整树。计划开独立公开
  仓库，不并入本内核仓。

## 4. Metal-on-Vulkan 垫片（独立仓库，计划中）

- `RubyMetal.bundle` 以 PanVK 实现 `_MTLDevice`；QuartzCore 钩子与
  AIR→SPIR-V 翻译为研究内容。
- 里程碑：插件加载与 P37Device 就绪、渲染目标/拷贝 blit、纹理采样、alpha
  混合、红探针上屏、带 Y-flip 的表面回写（锁屏指示条可见）。
- 未成立：完整 SpringBoard 合成（白内容、滑动黑块）、10-bit 颜色（以
  BGRA8 近似）。实验线出现过两次用户态冻结，均以复位恢复，根因未明。
- 垫片依赖 Mesa 仓的 ICD；计划以独立公开仓发布，明确标注实验状态。

## 5. 已验证状态

| 阶段 | 结果 |
|---|---|
| P1 只读探针（0352） | PASS：GPU_ID/AS/JS_PRESENT/READY、mfgcfg、SPM、bus-protect、MFG PLL 设备上解码 |
| P2 门控上电 | PASS：`rubygpupwr=2` 下 MFG2-5 电源/时钟时序 |
| P3.1/P3.2 驱动 + userclient | 设备 PASS（UAPI 往返、submit `kr=0`） |
| P3.4 显示 | PASS：经面板表面原生 1080×2400 交换（SG BO 分配） |
| P3.5 PanVK | PASS：GL 测试渲染；~26 fps batch-sync 基线 |
| Metal 垫片（M0–M9b v12） | 研究态：插件可加载、红探针上屏、真实合成 WIP |
| 0360 内核 | 仅 CI 验证，从未上机 |

## 6. 启动参数

完整 0360 启动行与参数表见 [appendix-bootargs](appendix-bootargs.md)
（`rubygpuprobe`、`rubygpupwr`、`rubygpucommit`、`rubygpuuc`、
`rubygpumulti`、`rubygpubomax`、`rubygpuvmpages`、`rubymetalu`、
`rubygpudiag`、`sweetfb_hz`）。GPU 相关门控默认全关。

## 7. 构建内核面

```sh
# patchset: bd125daf（327 文件）；exec-data 4fef9a18
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>
python3 scripts/verify-local.py --ci-config config/0360.env
# CI：xnu-0360 workflow（macos-15、Xcode 16.0）；先 record 再 gated
```

0352 线为 `config/0352.env`（patchset `40f7cefa`，318 文件，exec-data
`90326b5e`）。record 与 gated 的 run id 见
[VERIFICATION](../records/VERIFICATION.md)。

## 8. 不担保

- 不担保帧率、合成正确性或 Mesa 打包完整性。
- 0360 内核未上机；B4a AMP 需要不随仓库提供的 2 簇 ADT。
- Metal 垫片为研究态：白内容合成与 10-bit 颜色是未解问题，实验线的两次
  用户态冻结未归因。
- GPU 工作基于单台设备与实验线镜像，不属于受支持配置。