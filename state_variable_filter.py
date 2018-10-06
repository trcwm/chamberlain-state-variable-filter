#!/usr/bin/python3
'''
A simple class to create a Chamberlain digital state variable filter.

The digital state variable has a cutoff slope of 12 dB/octave.

Originally from:
Hal Chamberlin’s Musical Applications of Microprocessors

Notes:
http://www.earlevel.com/main/2003/03/02/the-digital-state-variable-filter/

This implementation:
George Smart, M1GEO
6 Oct 2018
https://www.george-smart.co.uk/
https://github.com/m1geo/chamberlain-state-variable-filter

History:
* Added double zero at nyquist to get better HF response, PA1DSP
* Implemented averaging in frequency domain to get better frequency response plots, PA1DSP
* Changed y scale of frequency plots to dB, PA1DSP.
* Added windowing to FFT to remove spectral leakage issues, PA1DSP.
* Removed SVF _o variables as they are not needed, PA1DSP.

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
    self.S1 = 0
    self.S2 = 0
  
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
    
    # calculate double zero
    self.iir_in = (input_sample + 2.0*self.S1 + self.S2) / 4.0
    #self.iir_in = input_sample
    
    self.S2 = float(self.S1)
    self.S1 = float(input_sample)
    
    # Perform the filtering operation
    self.HP = self.iir_in - self.LP - (self.q * self.BP)
    self.BP = self.BP + (self.f * self.HP)
    self.LP = self.LP + (self.f * self.BP)
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
  N = 1024   # number of samples
  F_S = 48e3 # Sample Rate in Hz (48 kHz)
  F_c = 4e3  # Corner Freq in Hz (5 kHz)
  
  # Generate X scales for the graphs
  time_array = np.linspace(0, 1/F_S * N, N)
  freq_array = np.linspace(0, F_S, N)
  
  # Set the stability coefficient to square-root of 2.
  tqc = 1.0
  f.set_q(tqc)
  
  # Calculate the frequency coefficient from frequency inputs
  tfc = f.calc_freq_coeff(F_c, F_S)
  f.set_freq_coeff(tfc)

  frames = 1000
  filt_fft_avg  = np.zeros(N)
  noise_fft_avg = np.zeros(N)
  window        = np.blackman(N)
  
  # use several chunks so we can average
  for I in range(0,frames):
    # Generate a list of random noise.
    noise = [random.random() for a in range(N)]
  
    # Remove any DC offset from the noise - comment out if not required.
    noise = np.array(noise) - np.mean(noise)
  
    # Take and FFT of the noise and make it real
    noise_fft = np.abs(np.fft.fft(np.multiply(noise, window)))

    # Run the SVF filter - put each time value of noise into
    # the filter (as 'a') and assign returns into 'filt'
    filt = [f.update(a, "lowpass") for a in noise]
  
    # Take and FFT of the filtered noise and make it real
    filt_fft = np.abs(np.fft.fft(np.multiply(filt, window)))
    
    # add to average vector
    filt_fft_avg = filt_fft_avg + filt_fft
    noise_fft_avg = noise_fft_avg + noise_fft
  
  filt_fft_avg = filt_fft_avg / frames
  noise_fft_avg = noise_fft_avg / frames
  
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
  plt.ylabel("Signal Amplitude (dB)")
  plt.plot(freq_array[:N // 2], 20*np.log10(noise_fft_avg[:N // 2]))
  plt.ylim(-80,30)

  # Plot time domain filtered noise in top right
  plt.subplot(2,2,2)
  plt.title("Time domain plot of Filtered noise")
  plt.xlabel("Time / seconds")
  plt.ylabel("Signal Amplitude")
  plt.plot(time_array, filt)
  
  # Plot frequency domain filtered noise in bottom right
  plt.subplot(2,2,4)
  plt.title("Estimation of filter frequency response")
  plt.xlabel("Frequency / Hertz")
  plt.ylabel("Signal Amplitude (dB)")
  plt.plot(freq_array[:N // 2], 20*np.log10(filt_fft_avg[:N // 2]) - 20*np.log10(noise_fft_avg[:N // 2]))
  plt.ylim(-90,10)
  
  # Show the plot and wait
  plt.show()
