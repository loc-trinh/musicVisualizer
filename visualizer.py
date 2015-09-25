import pyaudio, wave, struct, sys, os, re
import numpy as np
import Tkinter as tk


# MUSIC PLAYER SETUP
# =========================================
if len(sys.argv) < 2:
	raise Exception("ERROR: No music files specified.")
if os.path.isdir(sys.argv[1]):
	playlist = [sys.argv[1]+f for f in os.listdir(sys.argv[1]) if not os.path.isdir(f) and re.findall(r'[\w-]+.', f)[-1] in ['mp3', 'wav']]
else:
	playlist = [sys.argv[1]] if re.findall(r'[\w-]+.', sys.argv[1])[-1] in ['mp3', 'wav'] else None
if not playlist:
	raise Exception("ERROR: Cannot find any mp3 or wav files.")

# VISUAL SETUP
# =========================================
WIDTH = 900
HEIGHT = 350
window = tk.Tk()
window.title("musicVisualizer")
canvas = tk.Canvas(window, width=WIDTH, height=HEIGHT)
canvas.pack()
w = tk.Label(window, text="Now playing: ...", font=("Helvetica", 22))
w.pack()

# AUDIO SETUP
# =========================================
p = pyaudio.PyAudio()
CHUNK = 2048
SAMPLE_RATE = 0
stream = None
fin = None

def setupNewSong(song):
	global SAMPLE_RATE, stream, fin

	if os.path.exists('/tmp/visualizer-temp.wav'):
		os.system('rm /tmp/visualizer-temp.wav')

	title = re.findall(r'.*\/(.*)',song)
	w['text'] = "Now playing: " + title[0] if title else "Now playing: " + song
	if re.findall(r'[\w-]+.', song)[-1] == 'mp3':
		os.system("ffmpeg -i '%s' -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav /tmp/visualizer-temp.wav"%song)
		song = '/tmp/visualizer-temp.wav'

	fin = wave.open(song)
  	SAMPLE_RATE = fin.getframerate()

  	if stream:
  		#stop stream  
		stream.stop_stream()  
		stream.close()

 	#start stream
	stream = p.open(format = p.get_format_from_width(fin.getsampwidth()),  
	                channels = fin.getnchannels(),  
	                rate = SAMPLE_RATE,  
	                output = True)

# HELPER FUNCTIONS
# =========================================
def freqToIndex(freq):
	bandWidth = float(SAMPLE_RATE)/CHUNK/2
	return int(round(freq/bandWidth))

def average_fft_bands(fft_array):
	# ~ 20 Hz to ~ 20 KHz into 32 bands         #
	# 1/6 octave with center freq ~ 1000 Hz     #
	bars = []

	num_bands = 32
	low = 15
	high = 18
	for band in range(0, num_bands):
		hiFreq = high
		lowFreq = low
		for i in range(band):
			lowFreq *= 2**(1./3)
			hiFreq *= 2**(1./3)

		lowIndex = freqToIndex(lowFreq)
		highIndex = freqToIndex(hiFreq)
		avg = sum(fft_array[lowIndex:highIndex])/(highIndex-lowIndex+1)
		bars.append(avg)
	
	return bars

#draw
def draw(myList):
	global count
	canvas.delete('all')
	myMax = max(myList)
	if myMax != 0:
		offset = 0
		for i in myList:
			canvas.create_rectangle(offset*WIDTH/32.0, HEIGHT, (offset+1)*WIDTH/32.0, (HEIGHT-15)-i/myMax*(HEIGHT-50), fill='#0795DB')
			offset += 1


#read data  
import random

random.shuffle(playlist)
setupNewSong(playlist.pop())

def run():
	data = fin.readframes(CHUNK) 
	if data == '':
		if len(playlist) != 0:
			setupNewSong(playlist.pop())
			data = fin.readframes(CHUNK) 
		else:
			return

	unpacked_data = struct.unpack('{}h'.format(len(data)/2), data)
	fft_data = abs(np.fft.rfft(unpacked_data))
	fft_data = np.delete(fft_data,len(fft_data)-1)
	bars = average_fft_bands(fft_data[0:len(fft_data)/2])

	import scipy.ndimage
	bars = scipy.ndimage.gaussian_filter(bars, .5)

	draw(bars) #visual
	stream.write(data) #audio

	window.after(int(CHUNK/float(SAMPLE_RATE)*100)-1,run)


run()
window.mainloop()
