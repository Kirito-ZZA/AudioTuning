"""
使用Python绘制音频频响图的示例代码
"""

import numpy as np
import matplotlib.pyplot as plt
import librosa
import scipy.signal

# 1. 读取音频文件
audio_path = 'E:/Code/AudioTuning/resource/20Hz_20kHz.wav'  # 音频文件路径
y, sr = librosa.load(audio_path)  # y是音频信号，sr是采样率

# 2. 计算FFT
n = len(y)  # 信号长度
fft_result = np.fft.fft(y)  # 计算傅里叶变换
freq = np.fft.fftfreq(n, d=1/sr)  # 计算对应的频率

# 3. 只取正频率部分（单边谱）
n_half = n // 2
freq = freq[:n_half]
magnitude = np.abs(fft_result)[:n_half]  # 取幅度

# 4. 将幅度转换为分贝（dB）
# 避免log(0)问题，添加小值eps
eps = 1e-10
magnitude_db = 20 * np.log10(magnitude + eps)

# 5. 绘制频响图
plt.figure(figsize=(10, 6))
plt.plot(freq, magnitude_db)
plt.title('Frequency Response')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude (dB)')
plt.grid(True)
plt.xlim(20, sr/2)  # 限制频率范围（例如20Hz到奈奎斯特频率）
plt.xscale('log')  # 频率轴使用对数刻度（常见于音频分析）
plt.show()

# 代码说明读取音频：librosa.load读取音频文件，返回信号y和采样率sr。
# 如果音频是立体声，librosa会默认返回单声道信号（可以通过mono=False保留立体声）。

# 计算FFT：np.fft.fft计算信号的傅里叶变换，得到复数形式的频域表示。
# np.fft.fftfreq生成对应的频率点。

# 单边谱：由于FFT结果是对称的（正负频率），我们只取正频率部分（n//2）。

# 分贝转换：幅度转换为分贝使用公式：20 * log10(幅度)。
# 添加eps防止对零取对数导致错误。

# 绘制图形：使用matplotlib绘制频响图。
# 对数刻度（plt.xscale('log')）使低频部分更清晰，符合人耳对频率的感知。
# 限制x轴范围（例如20Hz到奈奎斯特频率sr/2）以聚焦于可听频率范围。

# 依赖安装确保安装以下库：bash

# pip install numpy matplotlib librosa scipy

# 注意事项音频文件格式：代码假设输入是WAV文件。如果是其他格式（如MP3），librosa也能处理，但需要确保文件路径正确。
# 频率范围：人耳可听范围通常为20Hz到20kHz，可根据需要调整plt.xlim。
# 平滑曲线（可选）：如果频响图过于嘈杂，可以使用scipy.signal.savgol_filter对magnitude_db进行平滑处理。
# 立体声处理：如果音频是立体声（多声道），可以分别计算每个声道的频响，或先将多声道平均为单声道。
# 窗口函数（可选）：在FFT前应用窗口函数（如Hann窗）可以减少频谱泄漏：python

window = scipy.signal.windows.hann(n)
y_windowed = y * window
fft_result = np.fft.fft(y_windowed)

# 扩展：动态分析如果想分析音频的时频特性（而非整个音频的静态频响），可以考虑绘制语谱图（Spectrogram）：python

plt.specgram(y, Fs=sr, cmap='viridis')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.colorbar(label='Amplitude (dB)')
plt.show()