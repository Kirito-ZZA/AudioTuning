"""
定义一个一阶低通滤波器，计算该系统在指定频率下的增益和相位，并绘制频率响应图/相位图
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# 定义系统的传递函数（例如一个一阶低通滤波器）
num = [1]       # 分子系数
den = [1, 1]    # 分母系数
system = signal.TransferFunction(num, den)

# 生成频率点
frequencies = np.logspace(0, 2, 1000)  # 从1~100Hz的对数频率点

# 计算频率响应
w, h = signal.freqresp(system, frequencies)

# 绘制频率响应图
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.semilogx(w, 20 * np.log10(abs(h)))  # 增益
plt.title('Frequency Response(Gain)')
plt.xlabel('Frequency [rad/s]')
plt.ylabel('Gain [dB]')
plt.grid(which='both', axis='both')

plt.subplot(1, 2, 2)
plt.semilogx(w, np.angle(h) * (180 / np.pi))  # 相位
plt.title('Frequency Response(Phase)')
plt.xlabel('Frequency [rad/s]')
plt.ylabel('Phase [degrees]')
plt.grid(which='both', axis='both')

plt.tight_layout()
plt.show()
