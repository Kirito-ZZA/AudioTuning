# AGENTS.md

## 1. 项目定位

AudioTuning 是一个基于 PyQt5 的桌面音频处理与调音软件，支持：

- 读取 WAV、原始 PCM、MP3、AAC 等音频格式，保留采样率和声道布局。
- 通过可动态挂载、可配置顺序和参数的算法链执行 GAIN、EQ、ACT 等音效算法。
- 在界面中调节算法参数，分别播放、保存原始音频和处理后音频。
- 使用 pyqtgraph 对比波形、FFT 频谱、平滑频谱及哈曼目标曲线。
- 保持界面、音频文档、算法和数据可视化之间的职责分离。

## 2. 当前实现与限制

- `audio_io.py` 支持 WAV、参数化原始 PCM 和 pydub 解码；原始 PCM 支持 8/16/24/32 位、声道、字节序、有符号/无符号及 32 位浮点配置。MP3/AAC 等非 WAV/PCM 格式仍需 ffmpeg。
- `conf/algorithms.json` 驱动 GAIN、16 段 Peaking EQ、ACT 动态压缩/限制插件。每个 EQ 频段可独立配置频率、增益和 Q；ACT 默认关闭，避免未经用户确认改变音源。
- `AudioDocument` 使用后台线程解码和执行算法链，合并连续参数修改，过期音源或参数结果不会覆盖最新数据。
- 原始与处理后音频均可独立播放和导出；当前导出格式统一为 16-bit PCM WAV。文件打开和保存操作统一从 Header 的文件菜单发起。
- 界面包含“音效调试、波形、频响、哈曼对比”四个页签；频响页显示 FFT，哈曼页显示 1/6 倍频程平滑及 1 kHz 归一化曲线，并可切换 Harman Over-Ear 2018 和 Harman In-Ear 2019 目标。
- 内置目标数据来自 AutoEq `targets/`，许可证见 `resource/targets/AutoEq-LICENSE.txt`。普通音频的内容频谱不等于耳机测量频响，界面和文档不得混淆二者。
- ACT 当前是离线整段处理，不是实时流式压缩器；真实声卡播放效果仍需在目标系统上人工验证。

## 3. 技术栈与常用命令

主要依赖：Python、PyQt5、NumPy、SciPy、pyqtgraph、pydub；设备功能使用 pyserial、pyvisa、pandas，打包使用 PyInstaller。

在项目根目录执行：

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pip install pytest
.venv/Scripts/python app.py
.venv/Scripts/python -m pytest test/test_*.py -q
```

打包命令：

```bash
.venv/Scripts/python -m PyInstaller AudioTuning.spec
```

`requirements.txt` 只保留直接依赖，不得重新加入会与 pyserial 冲突的 `serial` 包。`AudioTuning.spec` 使用 `SPECPATH` 定位工程并通过 `collect_submodules("filters")` 收集动态插件，禁止恢复历史绝对路径。

## 4. 目录与模块职责

- `app.py`：应用入口、主窗口、QSS、日志和关闭清理。
- `center.py`：四个中央页面的容器，持有共享 `AudioDocument` 并路由音频控制信号。
- `audio_io.py`：无 Qt 依赖的音频读写和 PCM 转换。
- `audio_engine.py`：文档状态、后台任务、算法链调度及兼容导出。
- `audio_analysis.py`：无 Qt 依赖的波形抽稀、频谱、平滑、归一化和目标曲线读取。
- `audio_widgets.py`：音效参数、独立波形、FFT 频响、哈曼对比页面及 PCM 格式对话框。
- `filters/base.py`：算法基类与标量、列表、表格参数规范。
- `filters/registry.py`：JSON 配置加载、动态 import、排序、启停、校验、执行和保存。
- `filters/EQFilters.py`、`filters/gain_filter.py`、`filters/act.py`：内置算法插件。
- `conf/setup.ini`：应用配置；`conf/algorithms.json`：算法链配置。
- `resource/targets/`：内置哈曼目标数据及许可证。
- `header.py`、`tabBar.py`、`appEvent.py`：文件菜单、四页签和跨组件 Qt 信号。
- `deviceWidget.py`：纯音频控制停靠窗口，通过跨组件信号控制播放和算法配置；`conn/` 为未接入当前音频界面的独立设备通信代码。
- `CustomQWidget/`、`utility/`：自定义控件和通用工具，不承载算法链业务。
- `test/`：核心自动化测试和独立实验脚本；核心测试为 `test_audio_*.py`。

改变上述职责、配置格式或公共接口时，同步更新本文档。

## 5. 音频数据与处理约定

- 单声道数据形状为 `(samples,)`，多声道为 `(samples, channels)`，采样点始终位于第 0 轴。
- 核心处理使用归一化 `float32`；算法内部可使用 `float64`，返回时保持原形状和数据有限性。
- `AudioDocument.original` 设为只读。任何启停、顺序或参数变化都从 `original` 重算，禁止在上一次 `processed` 上叠加。
- 算法不得意外修改采样率、采样数或声道布局。注册表会检查输出形状及 NaN/Inf，失败算法记录日志并跳过。
- 后台任务携带音源和参数版本；旧任务结果必须丢弃。UI 线程只通过文档信号接收结果。
- 原始 PCM 无文件头，必须由用户确认采样率、声道、位深、字节序和编码；文件大小不是完整帧整数倍时应报错。
- 导出前处理 NaN、Inf 和削波。新增导出格式时必须明确位深、字节序和量化规则。
- 文件和算法错误转成中文 `AudioError` 或文档信号，由界面展示；核心算法不得调用 `QMessageBox`。

## 6. 算法插件开发规则

每个算法条目在 `conf/algorithms.json` 中至少包含：

```json
{
  "module": "filters.gain_filter",
  "class": "GainAlgorithm",
  "order": 10,
  "enabled": true,
  "params": {"gain_db": 0.0}
}
```

新增算法必须遵守：

- 继承 `filters.base.AudioAlgorithm`，提供唯一 `algorithm_id`、中文 `display_name` 和 `parameters`。
- 使用 `ParameterSpec` 声明参数键、标签、默认值、范围、步长、单位和类型；多段参数使用 `float_list` 或带列定义的 `table`，EQ 使用 16 行 `bands` 表。
- `process(data, sample_rate, params)` 只依赖音频、采样率和参数，不引用 Qt 控件或全局文档。
- 不在 import 时读写文件、启动线程、播放音频或创建界面。
- 页面只通过 `AlgorithmChain` 和 `AudioDocument` 修改配置，不硬编码算法调用顺序。
- 新插件加入 PyInstaller hidden imports 的收集范围，并补充直通、典型值、边界值、多声道和非法参数测试。

## 7. 界面、播放与可视化规则

- 仅保留“音效调试、波形、频响、哈曼对比”四个有效页签，不恢复无实现的噪声空白页。
- 文件打开和原始/处理后保存只从 Header 文件菜单进入，不在音效调试页重复添加入口。
- 播放、停止、参数重置及算法配置操作集中在音频控制窗口，通过 `AppEvent` 信号槽控制，不得跨页面直接持有对方实例。
- 算法控件根据参数规范生成；EQ 使用 16 行 `QDoubleSpinBox` 表格，ACT 等标量参数使用紧凑双列网格；连续修改使用防抖，处理后播放/保存必须等待最新结果。
- 原始与处理后播放、保存入口必须明确分离。切换音源或处理结果变化时，不得继续播放旧的处理后临时文件。
- 停止、换源、重载和关闭应用时释放播放器、临时文件和后台任务。
- 波形绘图可以抽稀，但实际音频处理不得抽稀。耗时解码和完整算法链不得阻塞 GUI 线程。
- 原始波形和频谱使用 `#00ae00`，处理后使用 `#197ccc`；原始与处理后曲线使用一致窗口、频率范围、平滑和归一化规则，频率上限不超过 Nyquist。
- FFT 频响和哈曼对比使用独立页签，必须有明确标题及图例；哈曼对比统一标注 1/6 倍频程和 1 kHz 归一化。

## 8. 配置、依赖与代码风格

- 路径基于工程根目录或 `config.basepath` 构造，不写死本机绝对路径。
- 应用配置使用 `conf/setup.ini`，算法配置使用独立 JSON；界面临时参数最终写入算法链，不另建不一致的状态副本。
- 界面和错误信息使用中文，主流程使用 logger，不使用 `print` 代替日志。
- `resource/qss/app.qss` 全局及局部字体统一为 `Microsoft YaHei`；音频控制窗口按钮沿用统一蓝色样式。
- `audio_io.py`、`audio_analysis.py` 和算法插件保持无 Qt 依赖；Qt 信号集中在文档和界面层。
- 设备库只在使用设备功能时导入；缺少 VISA 后端或串口依赖时给出中文提示，不得导致音频应用启动失败。
- 修改公共数据形状、信号、算法接口、配置键或依赖时，同步更新所有调用方和本文档。

## 9. 修改后的验证

1. 运行第 3 节列出的核心 pytest，并对修改模块执行 compileall。
2. 使用真实 WAV 完成读取、GAIN/EQ/ACT、原始/处理后导出、重新读取和曲线计算。
3. 用 Qt offscreen smoke 测试检查四页签、16 行 EQ 表格、ACT 紧凑布局、曲线颜色、音频控制窗口跨页面控制、异步加载和完整主窗口；有条件时再进行真实 GUI 和声卡验证。
4. 检查原始 PCM 参数确认、非法帧报错、算法启停、配置保存/重载及处理后忙碌状态。
5. 若修改打包配置，运行 PyInstaller 并检查动态 filters、`conf/`、`resource/targets/` 是否进入产物。
6. 无法执行的验证必须在交付说明中明确列出，不得把 offscreen 测试描述为已试听或已人工验证。
