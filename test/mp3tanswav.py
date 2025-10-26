from pydub import AudioSegment

# 加载MP3文件
mp3_file = "20Hz_20kHz.mp3"
audio = AudioSegment.from_mp3(mp3_file)

# 设置音频质量
# parameters = {"bitrate": "192k", "sample_rate": 44100}
# audio.export(wav_file, format="wav", parameters=parameters)

# 剪切音频片段
# audio_segment = audio[:10000] # 获取前10秒
# audio_segment.export(wav_file, format="wav")

# 保存为WAV文件
wav_file = "20Hz_20kHz.wav"
audio.export(wav_file, format="wav")