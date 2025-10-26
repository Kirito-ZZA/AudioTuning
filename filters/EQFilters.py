"""
EQ滤波器设计模块
设计参考资料:
https://www.cnblogs.com/LXP-Never/p/17621793.html
https://gitee.com/LXP-Never/py-equalizer
"""
import numpy as np

def LowpassFilter(self, fc, Q=1 / np.sqrt(2.0)):
        """ 低通滤波器(Low Pass Filter) 
        LPF: H(s) = 1 / (s^2 + s/Q + 1)
        
        b0 = (1 - cos(w0))/2;
        b1 = 1 - cos(w0);
        b2 = (1 - cos(w0))/2;
        a0 = 1 + alpha;
        a1 = -2*cos(w0);
        a2 = 1 - alpha;
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = (1.0 - cos_w0) / 2.0
        b1 = 1.0 - cos_w0
        b2 = (1.0 - cos_w0) / 2.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def HighpassFilter(self, fc, Q=1 / np.sqrt(2)):
        """ 高通滤波器(High Pass Filter) 
        HPF: $H(s)=\frac{s^2}{s^2 + s/Q + 1}$
            b0 = (1 + cos(w0))/2
            b1 = -(1 + cos(w0))
            b2 = (1 + cos(w0))/2
            a0 = 1 + alpha
            a1 = -2*cos(w0)
            a2 = 1 - alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = (1.0 + cos_w0) / 2.0
        b1 = -(1.0 + cos_w0)
        b2 = (1.0 + cos_w0) / 2.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def BandpassFilter_Q(self, fc, Q):
        """带通 Band Pass Filter (增益 = Q)
        BPF: H(s) = s / (s^2 + s/Q + 1) (constant skirt gain, peak gain = Q)
            b0 =   sin(w0)/2  =   Q*alpha
            b1 =   0
            b2 =  -sin(w0)/2  =  -Q*alpha
            a0 =   1 + alpha
            a1 =  -2*cos(w0)
            a2 =   1 - alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = sin_w0 / 2.0  # Q*alpha
        b1 = 0.0
        b2 = -sin_w0 / 2.0  # -Q*alpha
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def BandpassFilter_0dB(self, fc, Q=1 / np.sqrt(2)):
        """带通 Band Pass Filter( 0 db增益）
        BPF: H(s) = (s/Q) / (s^2 + s/Q + 1) (constant 0 dB peak gain)
            b0 =   alpha
            b1 =   0
            b2 =  -alpha
            a0 =   1 + alpha
            a1 =  -2*cos(w0)
            a2 =   1 - alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = alpha
        b1 = 0.0
        b2 = -alpha
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def NotchFilter(self, fc, Q=1 / np.sqrt(2)):
        """Notch滤波器
        notch: H(s) = (s^2 + 1) / (s^2 + s/Q + 1)$
            b0 =   1
            b1 =  -2*cos(w0)
            b2 =   1
            a0 =   1 + alpha
            a1 =  -2*cos(w0)
            a2 =   1 - alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = 1.0
        b1 = -2.0 * cos_w0
        b2 = 1.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def AllpassFilter(self, fc, Q=1 / np.sqrt(2)):
        """全通 All Pass Filter
        APF: H(s) = (s^2 - s/Q + 1) / (s^2 + s/Q + 1)$
            b0 =   1 - alpha
            b1 =  -2*cos(w0)
            b2 =   1 + alpha
            a0 =   1 + alpha
            a1 =  -2*cos(w0)
            a2 =   1 - alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # ---------------------------------------------
        b0 = 1.0 - alpha
        b1 = -2.0 * cos_w0
        b2 = 1.0 + alpha
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def PeakingFilter(self, fc, dBgain, Q=1 / np.sqrt(2)):
        """峰值滤波器
        peakingEQ: H(s) = (s^2 + s*(A/Q) + 1) / (s^2 + s/(A*Q) + 1)
            b0 =   1 + alpha*A
            b1 =  -2*cos(w0)
            b2 =   1 - alpha*A
            a0 =   1 + alpha/A
            a1 =  -2*cos(w0)
            a2 =   1 - alpha/A
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        # cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # gain、A 仅用于峰值和shelf滤波器
        dBgain = round(float(dBgain), 3)
        A = 10 ** (dBgain / 40)
        # ---------------------------------------------
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def LowshelfFilter(self, fc, dBgain, Q=1 / np.sqrt(2)):
        """低切滤波器
        lowShelf: H(s) = A * (s^2 + (sqrt(A)/Q)*s + A)/(A*s^2 + (sqrt(A)/Q)*s + 1)
            b0 =    A*( (A+1) - (A-1)*cos(w0) + 2*sqrt(A)*alpha )
            b1 =  2*A*( (A-1) - (A+1)*cos(w0)                   )
            b2 =    A*( (A+1) - (A-1)*cos(w0) - 2*sqrt(A)*alpha )
            a0 =        (A+1) + (A-1)*cos(w0) + 2*sqrt(A)*alpha
            a1 =   -2*( (A-1) + (A+1)*cos(w0)                   )
            a2 =        (A+1) + (A-1)*cos(w0) - 2*sqrt(A)*alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # gain、A 仅用于峰值和shelf滤波器
        dBgain = round(float(dBgain), 3)
        A = 10.0 ** (dBgain / 40.0)
        # ---------------------------------------------
        b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
        b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
        b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
        a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
        a2 = (A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0

def HighshelfFilter(self, fc, dBgain, Q=1 / np.sqrt(2)):
        """高切滤波器
        highShelf: H(s) = A * (A*s^2 + (sqrt(A)/Q)*s + 1)/(s^2 + (sqrt(A)/Q)*s + A)
            b0 =    A*( (A+1) + (A-1)*cos(w0) + 2*sqrt(A)*alpha )
            b1 = -2*A*( (A-1) + (A+1)*cos(w0)                   )
            b2 =    A*( (A+1) + (A-1)*cos(w0) - 2*sqrt(A)*alpha )
            a0 =        (A+1) - (A-1)*cos(w0) + 2*sqrt(A)*alpha
            a1 =    2*( (A-1) - (A+1)*cos(w0)                   )
            a2 =        (A+1) - (A-1)*cos(w0) - 2*sqrt(A)*alpha
        """
        # 中间变量
        w0 = 2.0 * np.pi * fc / self.fs  # 角频率
        cos_w0 = np.cos(w0)  # cos(w0)
        sin_w0 = np.sin(w0)  # sin(w0)
        alpha = sin_w0 / (2.0 * Q)  # alpha
        # gain、A 仅用于峰值和shelf滤波器
        dBgain = round(float(dBgain), 3)
        A = 10.0 ** (dBgain / 40.0)
        # ---------------------------------------------
        b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
        b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
        a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
        a2 = (A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha
        numerator_B = np.array([b0, b1, b2], dtype=np.float32)
        denominator_A = np.array([a0, a1, a2], dtype=np.float32)
        return numerator_B / a0, denominator_A / a0