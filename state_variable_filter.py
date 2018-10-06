#!/usr/bin/python3
'''
A simple class to create a Chamberlain digital state variable filter.

The digital state variable has a cutoff slope of 12 dB/octave.

Originally from:
Hal Chamberlin’s Musical Applications of Microprocessors

Notes:
http://www.earlevel.com/main/2003/03/02/the-digital-state-variable-filter/

This implimentation:
George Smart, M1GEO
6 Oct 2018
https://www.george-smart.co.uk/
https://github.com/m1geo/chamberlain-state-variable-filter
'''

# Numpy needed for sin function in calc_freq_coeff
import numpy as np

class SVF():
	def __init__(self, f_coefficient=0.2, q_coefficient=1.4142):
		'''Default constructor. Assign all values used in the filter'''
		self.f = f_coefficient
		self.q = q_coefficient
		self.HP = 0
		self.LP = 0
		self.BP = 0
		self.NP = 0
	
	def set_freq_coeff(self, f_coefficient):
		'''This function allows you to set the frequency coefficient of the filter'''
		self.f = f_coefficient

	def set_q(self, q_coefficient):
		'''This function allows you to set the Q coefficient of the filter'''
		self.q = q_coefficient

	def calc_freq_coeff(self, corner_frequency, sample_frequency):
		'''This function allows you to calculate the frequency coefficient from actual frequency values'''
		fc = 2 * np.sin(((np.pi * corner_frequency)/(sample_frequency)))
		return fc

	def update(self, input_sample, filter_type="lowpass"):
		'''This function takes an input sample and returns one of the selected outputs.
			
			Call this function with time domain samples as input_sample.
			
			filter_type:
				"lowpass"  : low-pass filter response
				"highpass" : high-pass filter response
				"bandpass" : band-pass filter response
				"bandstop" : band-stop (notch) filter response
		'''
		
		# Update the timeshift (old values, z^{-1})
		self.LP_o = self.LP
		self.BP_o = self.BP
		
		# Perform the filtering operation
		self.HP = input_sample - self.LP_o - (self.q * self.BP_o)
		self.BP = self.BP_o + (self.f * self.HP)
		self.LP = self.LP_o + (self.f * self.BP_o)
		self.NP = self.LP + self.HP
		
		if filter_type.lower() == "lowpass":
			selected_filter_output = self.LP
		elif filter_type.lower() == "highpass":
			selected_filter_output = self.HP
		elif filter_type.lower() == "bandpass":
			selected_filter_output = self.BP
		elif filter_type.lower() == "bandstop" or filter_type.lower() == "notch":
			selected_filter_output = self.NP
		else:
			raise ValueError("Filter type '%s' not recognised" % (filter_type))
		return selected_filter_output
		

# The below code only runs if you execute this file.
# If you import the class elsewhere, the below won't run.
if __name__ == "__main__":
	import matplotlib.pyplot as plt
	import random

	# Create an instance of the filter with the default settings
	f = SVF()
	
	# Some example parameters
	N = 10240 # number of samples
	F_S = 48e3 # Sample Rate in Hz (48 kHz)
	F_c = 4e3 # Corner Freq in Hz (5 kHz)
	
	# Generate X scales for the graphs
	time_array = np.linspace(0, 1/F_S * N, N)
	freq_array = np.linspace(0, F_S, N)
	
	# Set the stability coefficient to square-root of 2.
	tqc = np.sqrt(2)
	f.set_q(tqc)
	
	# Calculate the frequency coefficient from frequency inputs
	tfc = f.calc_freq_coeff(F_c, F_S)
	f.set_freq_coeff(tfc)

	# Generate a list of random noise.
	noise = [random.random() for a in range(N)]
	
	# Remove any DC offset from the noise - comment out if not required.
	noise = np.array(noise) - np.mean(noise)
	
	# Take and FFT of the noise and make it real
	noise_fft = np.abs(np.fft.fft(noise))

	# Run the SVF filter - put each time value of noise into
	# the filter (as 'a') and assign returns into 'filt'
	filt = [f.update(a, "lowpass") for a in noise]
	
	# Take and FFT of the filtered noise and make it real
	filt_fft = np.abs(np.fft.fft(filt))

	# New figure with a large title
	plt.figure(1)
	plt.suptitle("Chamberlain Digital State Variable Filter Example: Low Pass\nGeorge Smart, M1GEO", fontsize=18)
	
	# Plot time domain noise in top left
	plt.subplot(2,2,1)	
	plt.title("Time domain plot of random noise")
	plt.xlabel("Time / seconds")
	plt.ylabel("Signal Amplitude")
	plt.plot(time_array, noise)
	
	# Plot frequency domain noise in bottom left
	plt.subplot(2,2,3)
	plt.title("FFT plot of random noise")
	plt.xlabel("Frequency / Hertz")
	plt.ylabel("Signal Amplitude")
	plt.plot(freq_array[:N // 2], noise_fft[:N // 2])

	# Plot time domain filtered noise in top right
	plt.subplot(2,2,2)
	plt.title("Time domain plot of Filtered noise")
	plt.xlabel("Time / seconds")
	plt.ylabel("Signal Amplitude")
	plt.plot(time_array, filt)
	
	# Plot frequency domain filtered noise in bottom right
	plt.subplot(2,2,4)
	plt.title("FFT plot of Filtered noise")
	plt.xlabel("Frequency / Hertz")
	plt.ylabel("Signal Amplitude")
	plt.plot(freq_array[:N // 2], filt_fft[:N // 2])

	# Show the plot and wait
	plt.show()
