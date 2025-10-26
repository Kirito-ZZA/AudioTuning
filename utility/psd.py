# 功率谱密度计算
# 注意 这里所有的计算都是标准单位

import numpy as np
from scipy.fftpack import fft
import time
import re


prefixs = ('yzafpnum kMGTPEZY')
np_log_1000 = np.log(1000)
def unit_converter(number, unit):
	'''转换成标准单位输出
	'''
	if unit == '':
		return number, unit

	unit = unit.strip()

	match = re.search(r"^[a]", unit)
	if match:
		return number * 1E-18, unit[1:]

	match = re.search(r"^[f]", unit)
	if match:
		return number * 1E-15, unit[1:]

	match = re.search(r"^(?:ppm)", unit)
	if match:
		return number * 1E-4, '%'

	match = re.search(r"^[p]", unit)
	if match:
		return number * 1E-12, unit[1:]

	match = re.search(r"^[n]", unit)
	if match:
		return number * 1E-9, unit[1:]

	match = re.search(r"^[u]", unit)
	if match:
		return number * 1E-6, unit[1:]

	match = re.search(r"^[m]", unit)
	if match:
		return number * 1E-3, unit[1:]

	match = re.search(r"^[k]", unit)
	if match:
		return number * 1E3, unit[1:]

	match = re.search(r"^[M]", unit)
	if match:
		return number * 1E6, unit[1:]

	match = re.search(r"^[G]", unit)
	if match:
		return number * 1E9, unit[1:]
	
	match = re.search(r"^[T]", unit)
	if match:
		return number * 1E12, unit[1:]
	
	match = re.search(r"^[P]", unit)
	if match:
		return number * 1E15, unit[1:]

	match = re.search(r"^[E]", unit)
	if match:
		return number * 1E18, unit[1:]

	match = re.search(r"^[Z]", unit)
	if match:
		return number * 1E21, unit[1:]

	match = re.search(r"^[Y]", unit)
	if match:
		return number * 1E24, unit[1:]

	return number, unit


def unit_reconverter(number, unit):
	'''转换成任意量级单位输出
	args:
		number (float) : 标准单位下的数值
		unit (str) : 目标量级单位
	ret:
		number（转换后的数值）
	'''
	if unit == '':
		return number

	unit = unit.strip()

	match = re.search(r"^[a]", unit)
	if match:
		return number / 1E-18

	match = re.search(r"^[f]", unit)
	if match:
		return number / 1E-15

	match = re.search(r"^(?:ppm)", unit)
	if match:
		return number / 1E-4

	match = re.search(r"^[p]", unit)
	if match:
		return number / 1E-12

	match = re.search(r"^[n]", unit)
	if match:
		return number / 1E-9

	match = re.search(r"^[u]", unit)
	if match:
		return number / 1E-6

	match = re.search(r"^[m]", unit)
	if match:
		return number / 1E-3

	match = re.search(r"^[k]", unit)
	if match:
		return number / 1E3

	match = re.search(r"^[M]", unit)
	if match:
		return number / 1E6

	match = re.search(r"^[G]", unit)
	if match:
		return number / 1E9
	
	match = re.search(r"^[T]", unit)
	if match:
		return number / 1E12
	
	match = re.search(r"^[P]", unit)
	if match:
		return number / 1E15

	match = re.search(r"^[E]", unit)
	if match:
		return number / 1E18

	match = re.search(r"^[Z]", unit)
	if match:
		return number / 1E21

	match = re.search(r"^[Y]", unit)
	if match:
		return number / 1E24

	return number

def unit_split_raw(value):
	'''拆分成数值和原始单位
	'''
	if isinstance(value, str):
		value = value.strip()
		match = re.search(r"[0-9eE.\-\+]+", value, re.IGNORECASE)
		if match:
			number, unit = float(match.group(0)), value[len(match.group(0)):]
			return number, unit
	return None, None

def unit_split(value):
	'''拆分成数值和标准单位
	'''
	if isinstance(value, str):
		value = value.strip()
		match = re.search(r"[0-9eE.\-\+]+", value, re.IGNORECASE)
		if match:
			number, unit = float(match.group(0)), value[len(match.group(0)):]
			return unit_converter(number, unit)
	return None, None

def format_value(v, u, bits=12):
	'''格式化输出，不转变单位，设置小数位数
	'''
	if abs(v) < 0.1**bits:
		# print(f'bits {bits}')
		return f'{0.0} {u}'
	try:
		x = bits - int(np.floor( np.log10(abs(v)) ) ) - 1
	except:
		x = -1

	return f"{v:.{x}f} {u}" if x>=0 else f"{v:.{bits-1}e}{u}"

def unit_format(number, unit, bits=12):
	'''格式化成合适的单位输出
	如果在输入当前单位下，有效数字为0，则输出0
	'''
	if abs(number) < 0.1**bits:
		# print(f'bits {bits}')
		return 0.0, unit

	n, u = unit_converter(number, unit)
	# print(n,u)
	if abs(n) < 1E-15:
		return n, u
	x = int(np.floor( np.log(abs(n)) / np_log_1000 ))
	# print('x',x)
	x = x if (8+x)>=0 else -8
	x = x if (8+x)<len(prefixs) else len(prefixs)-8-1
	v, u = n * (0.001**x), "{}{}".format(prefixs[8+x], u)
	return v, u


def data_str_format(data_str):
	'''
	以最少的小数点格式化输出 60.000V -> 60.0V
	'''
	v,u=unit_split_raw(data_str)
	new_v,new_u=unit_format(v,u,bits=7)
	return f'{new_v}{new_u}'


class psd_tool_fft(object):
	"""docstring for psd_tool_fft
	"""
	log = print
	def __init__(self,data,unit,Fs=1000,cut_off_freq=10):
		'''
		data (np.array)
		要求数据是标准单位
		'''
		super(psd_tool_fft, self).__init__()
		if unit == None:
			unit = 'V'
		self.unit = unit
		self.dc_offset = np.mean(data)
		self.log(f"dc_offset {self.dc_offset}")
		self.data = (data - self.dc_offset)
		self._Vpp = np.max(self.data)-np.min(self.data)
		self._Vrms = np.sqrt(np.sum(self.data**2)/len(self.data))
		self._data_std = np.std(self.data)
		self.average_count = Fs//(cut_off_freq*2)
		self.real_Fs = Fs/self.average_count
		count = int(self.average_count)
		data = self.data
		self.average_data = np.nanmean(np.pad(data.astype(float),(0,0 if len(data)%count == 0 else count-len(data)%count),mode='constant',constant_values=np.NaN).reshape(-1,count),axis=1)
		self.data = self.average_data
		self.Fs = self.real_Fs
		self.N = len(self.data)
		start_time = time.time()
		self.data_fft = fft(self.data)
		self.log(f"fft fft time: {time.time() - start_time}")
		self.data_fft = self.data_fft[:int(self.N/2)+1]#取单边FFT
		self.data_psd = np.abs(self.data_fft)**2*(1/(self.Fs*self.N))
		self.data_psd = self.data_psd*2
		self.freq = np.linspace(0,self.Fs,self.N+1)
		self.freq = self.freq[:int(self.N/2)+1]
		self.delta_freq = self.Fs/self.N

	def update_data(self, data, unit, Fs=1000, cut_off_freq=10):
		if unit == None:
			unit = 'V'
		self.unit = unit
		self.dc_offset = np.mean(data)
		self.log(f"dc_offset {self.dc_offset}")
		self.data = (data - self.dc_offset)
		
		self.average_count = Fs//(cut_off_freq*2)
		self.real_Fs = Fs/self.average_count
		count = int(self.average_count)
		data = self.data
		self.average_data = np.nanmean(np.pad(data.astype(float),(0,0 if len(data)%count == 0 else count-len(data)%count),mode='constant',constant_values=np.NaN).reshape(-1,count),axis=1)
		self.data = self.average_data

		self._Vpp = np.max(self.data)-np.min(self.data)
		self._Vrms = np.sqrt(np.sum(self.data**2)/len(self.data))
		self._data_std = np.std(self.data)

		self.Fs = self.real_Fs
		self.N = len(self.data)
		start_time = time.time()
		self.data_fft = fft(self.data)
		self.log(f"fft fft time: {time.time() - start_time}")
		self.data_fft = self.data_fft[:int(self.N/2)+1]#取单边FFT
		self.data_psd = np.abs(self.data_fft)**2*(1/(self.Fs*self.N))
		self.data_psd = self.data_psd*2
		self.freq = np.linspace(0,self.Fs,self.N+1)
		self.freq = self.freq[:int(self.N/2)+1]
		self.delta_freq = self.Fs/self.N

	def _get_fft(self):
		return self.freq,np.abs(self.data_fft)*2/self.N

	def get_raw_data(self):
		return self.real_Fs, self.data

	def get_psd(self):
		'''
		噪声功率谱
		返回x,y,
			x 横轴坐标  频率
			y           噪声功率谱
		'''
		return self.freq,self.data_psd

	def get_noise(self):
		'''
		噪声电压密度谱
		y轴单位 V/sqrt(Hz)
		'''
		return self.freq,np.sqrt(self.data_psd)

	def integral_n(self,n):
		E = 0
		for i in range(0,n+1):
			E = E + self.data_psd[i]*self.delta_freq
		return E

	def get_origin(self):
		'''
		功率谱密度的原函数
			y轴单位  Vrms
		'''
		origin = []
		E = 0
		for i in range(0,int(self.N/2)+1):
			E = E+self.data_psd[i]*self.delta_freq
			origin.append(E)
		origin = np.array(origin)
		return self.freq,np.sqrt(origin)


	def integral_section(self,start_freq,end_freq):
		'''
		根据频率区间进行积分，返回等效噪声
		args:
			start_freq,end_freq一定是要求在采样频率内
		返回等效噪声，标准单位
		'''
		if start_freq > end_freq or start_freq > self.freq[-1]:
			return 0
		start_n = int(start_freq/self.delta_freq)
		end_n = int(end_freq/self.delta_freq)

		self.log(f"start_n {start_n} end_n {end_n}")
		E = 0
		for n in range(start_n,end_n+1):
			E = E+self.data_psd[n]*self.delta_freq
		self.log(f"积分能量为 {E}")
		return np.sqrt(E)

	@property
	def Vpp(self):
		v,u = unit_format(self._Vpp,self.unit)
		return f"{v}{u}"

	@property
	def Vrms(self):
		v,u = unit_format(self._Vrms,self.unit)
		return f"{v}{u}"

	@property
	def data_std(self):#标准差
		v,u = unit_format(self._data_std,self.unit)
		return f"{v}{u}"

	@property
	def e_n(self):#平均噪声
		# v,u = unit_format(np.mean(np.sqrt(self.data_psd)),self.unit)
		v,u =  unit_format(self._Vrms/np.sqrt(self.freq[-1]),self.unit)
		return f"{v}{u}/√Hz"
	
		
	
# import pylab 
# class psd_tool_plt(object):
# 	"""docstring for psd_tool_plt
# 	经过验证，pylab的psd结果与fft计算一致，时间上优化空间不大，所以选择上面的fft
# 	"""
# 	def __init__(self, data,unit,Fs=1000):
# 		super(psd_tool_plt, self).__init__()
# 		data = data - np.mean(data)
# 		self.data = data
# 		self.unit = unit
# 		self.Fs = Fs
# 		self.N = len(data)
# 		self._Vpp = np.max(self.data)-np.min(self.data)
# 		self._Vrms = np.sqrt(np.sum(self.data**2)/len(self.data))
# 		self._data_std = np.std(self.data)
# 		psd_r = pylab.psd(self.data,NFFT=self.N,Fs=self.Fs)
# 		self.data_psd = np.array(psd_r[0])
# 		self.freq = np.array(psd_r[1])

# 	def get_psd(self):
# 		return self.freq,self.data_psd

# 	def get_noise(self):
# 		return self.freq,np.sqrt(self.data_psd)

# 	@property
# 	def Vpp(self):
# 		return self._Vpp
	
# 	@property
# 	def Vrms(self):
# 		return self._Vrms

# 	@property
# 	def data_std(self):
# 		return self._data_std

if __name__ == '__main__':
	import h5py
	filename = "./测试数据3.h5"
	h5_file = h5py.File(filename,'r')
	data = h5_file['data'][:]
	Fs = h5_file['metadata/sample_rate'][()]
	data = data[:int(Fs)]
	with open('./test_data.txt','w') as f:
		f.write(str(list(data)))

	data = np.array(data)
	print(f"采样率{Fs} 数据长度 {len(data)}")
	start_time = time.time()
	test_psd_tool = psd_tool_fft(data,"V",Fs)
	print(f"fft cost time: {time.time()-start_time}")
	import matplotlib.pyplot as plt
	fig = plt.figure("fft",figsize=(16,9),dpi=100)
	ax1 = fig.add_subplot(2,2,1)
	ax2 = fig.add_subplot(2,2,2)
	ax3 = fig.add_subplot(2,2,3)
	ax4 = fig.add_subplot(2,2,4)

	t = np.linspace(0,len(data)/Fs,len(data)+1)

	ax3.plot(t[0:-1],data)
	# x,y=test_psd_tool._get_fft()
	# ax1.plot(x[1:],20*np.log10(y[1:]))
	x,y=test_psd_tool.get_psd()
	ax1.plot(x[1:],20*np.log10(y[1:]))
	ax1.set_title("fft psd")
	x,y=test_psd_tool.get_noise()
	# print(y[499],y[500],y[501])
	ax2.plot(x[1:],y[1:])
	ax2.set_title("fft noise")

	x,y = test_psd_tool.get_origin()
	ax4.plot(x,y,label="get_psd")


	print(f"get noise from 0_500hz Vrms= {test_psd_tool.integral_section(0,500)}")
	print(f"get Vpp: {test_psd_tool.Vpp}")
	print(f"get Vrms: {test_psd_tool.Vrms}")
	print(f"get std: {test_psd_tool.data_std}")
	print(f"get e_n: {test_psd_tool.e_n}")
	#psd
	# start_time = time.time()
	# test_psd_tool2 = psd_tool_plt(data,"V",Fs)
	# print(f"psd cost time: {time.time()-start_time}")
	# # fig2 = plt.figure("psd",figsize=(16,9),dpi=100)
	# # ax21 = fig2.add_subplot(1,2,1)
	# # # ax21.set_yscale('log')
	# # ax22 = fig2.add_subplot(1,2,2)
	# # # ax22.set_yscale('log')
	# x,y = test_psd_tool2.get_psd()
	# # ax4.plot(x,20*np.log10(y),label="get_psd")
	# ax4.set_title("pylab psd")
	# ax4.legend()
	# x,y=test_psd_tool2.get_noise()
	# ax3.plot(x,20*np.log10(y))
	# ax3.set_title("pylab noise")
	# ax22.plot(x,20*np.log10(y))


	
	plt.show()
	while True:
		pass
		
















