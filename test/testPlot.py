import os
import wave
import numpy as np
import matplotlib.pyplot as plt

f = wave.open('E:\\Code\\AudioTuning\\resource\\20Hz_20kHz.wav', 'rb')

#读取格式信息
params=f.getparams()
nchannnels,sampwidth,framerate,nframes = params[:4]
print(framerate)
#读取波形数据
# strData = f.readframes(nframes)
strData = f.readframes(int(nframes/2))
#将字符串转换为16位整数
waveData = np.frombuffer(strData,dtype=np.int16)
#幅值归一化
waveData = waveData*1.0/(max(abs(waveData)))
#计算音频的时间
time = np.arange(0,nframes)*(1.0/framerate)
#绘图
plt.plot(time, waveData)
plt.xlabel("Time(s)")
plt.ylabel("Amplitude")
plt.title("Single channel waveData")
plt.show()