# Spyktro
Simple GUI Software for viewing and analyzing Raman spectra based on Pyside6

**This project is currently put aside and not in active development. The GUI is only for viewing Raman Spectra only. However, the sPyktro_raman.py should work on its own**

## sPyktro_raman.py

1. quick_plot(self, show_peak = False, show_baseline = False, show_zeroline = False, output_dir = os.getcwd(), figure_size = (12, 8), y_lim_top = 0, spectra_color = 'k')
   Function to making a quick plot of the Raman spectra. This function is used to quickly check baseline correction and peak finding result.
   - show_peak: set to True to scatter Raman peaks and mark the corresponding wavenumber. Only work after using find_raman_peaks()
   - show_baseline: set to True to show baseline of Raman spectra. Only work after using a baseline_.*() function
   - show_zeroline: set to True to also plot y=0
   - output_dir: output file path
   - return fig, axs

2. find_raman_peaks(self, filter_window = None, filter_degree = None, lower_prominance = None, higher_prominance = None, lower_height = 0)
   Function to find Raman peaks basec on scipy.signal.find_peaks

3. baseline_modpoly(self, degree = 2, repitition=100, gradient=0.001)
   Automated Method for Subtraction of Fluorescence from Biological Raman Spectra, by Lieber & Mahadevan-Jansen (2003)/
   code is adapted from https://github.com/StatguyUser/BaselineRemoval/blob/master/src/BaselineRemoval.py
    

