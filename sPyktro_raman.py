import os
import numpy as np
from inspect import signature
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.sparse import csc_matrix, eye, diags
from scipy.optimize import curve_fit


project_directory = "/Users/bochen/TAMU/glass_transition_temp/Glassy SOA Raman Spectra/Spectra text files/"

class Raman_Spectra:

    def __init__(self, file_path, sample_name, start = 0, end = None):

        # Read a raman spectra in a text file and initialize the .
        # The text file just have two columns dseparated by white space. One column is the wavenumber and the other is the intensity.

        self.file_path = file_path
        self.spectra_data = self.load_file(self.file_path)
        self.start = start
        self.end = end

        start_index = np.argmin(np.abs(self.spectra_data[:,0] - start))
        if end:
            end_index = np.argmin(np.abs(self.spectra_data[:,0] - end))

        if not end:
            spectra_data = self.spectra_data[start_index:]
        else:
            spectra_data = self.spectra_data[start_index:end_index]
        
        self.wavenumber = spectra_data[:, 0]
        self.intensity = spectra_data[:, 1]

        self.sample_name = sample_name

        self.raman_peaks = None # initialize raman peaks as None. find_raman_peaks will give it a value
        self.baseline = None # initialize baseline as None. baseline correction functions will give it a value once called
        self.baseline_method = None
    
    def __str__(self):
        return self.sample_name
    
    def __repr__(self):
        return self.__str__()

    def copy(self):
        return Raman_Spectra(self.file_path, self.sample_name, start=self.start, end=self.end)

    def cut(self, start = 0, end = None):
        start_index = np.argmin(np.abs(self.spectra_data[:,0] - start))
        if end:
            end_index = np.argmin(np.abs(self.wavenumber - end))

        if not end:
            new_wavenumber = self.wavenumber[start_index:]
            new_intensity = self.intensity[start_index:]
        else:
            new_wavenumber = self.wavenumber[start_index:end_index]
            new_intensity = self.intensity[start_index:end_index]
        
        return_spectra = Raman_Spectra(np.stack((new_wavenumber, new_intensity), axis = 1), self.sample_name)

        return return_spectra

    def load_file(self, file_path):
        spectra_data = np.loadtxt(file_path, encoding='cp1252')
        return spectra_data
    
    def get_spectra(self):
        return np.copy(self.wavenumber), np.copy(self.intensity)

    def quick_plot(self, show_peak = False, show_baseline = False, show_zeroline = False, output_dir = os.getcwd(), figure_size = (12, 8), y_lim_top = 0, spectra_color = 'k'):

        fig, axs = plt.subplots(1, 1, figsize=figure_size)
        axs.plot(self.wavenumber, self.intensity, color = spectra_color, linewidth = 1)
        
        if show_peak and self.raman_peaks is not None:
            peaks_index = self.raman_peaks[0]
            axs.scatter(self.wavenumber[peaks_index], self.intensity[peaks_index], marker = 'o', color = "deepskyblue")

            for i, w_n in enumerate(self.wavenumber[peaks_index]):
                axs.annotate(round(w_n), xy = (w_n, self.intensity[peaks_index][i]), xycoords='data', xytext = (-2, 10), textcoords = 'offset points', rotation = 90, size = "x-small")
        
        if show_baseline and self.baseline is not None:
            axs.plot(self.wavenumber, self.baseline, color = 'g')

        if show_zeroline:
            axs.hlines(0, self.wavenumber[0], self.wavenumber[-1], colors = 'k', linewidths = 0.5)

        axs.set_title(self.sample_name+ " Raman spectra quick plot")
        if y_lim_top:
            axs.set_ylim(top = y_lim_top)
        
        axs.set_xlabel("Raman shift 1/cm")
        axs.set_ylabel("Intensity")
        plt.show()
        fig.savefig(self.sample_name + " Raman Spectra quick plot", dpi = 300)

        return fig, axs

    #def quick_plot_multiple()

    # Automated Method for Subtraction of Fluorescence from Biological Raman Spectra, by Lieber & Mahadevan-Jansen (2003)
    # code is adapted from https://github.com/StatguyUser/BaselineRemoval/blob/master/src/BaselineRemoval.py
    def baseline_modpoly(self, degree = 2, repitition=100, gradient=0.001):
        '''
        input
            degree: Polynomial degree, default is 2        
            repitition: How many iterations to run. Default is 100
            gradient: Gradient for polynomial loss, default is 0.001. It measures incremental gain over each iteration. If gain in any iteration is less than this, further improvement will stop
        '''
        criteria=np.inf
        y = np.copy(self.intensity)
        x = np.arange(y.shape[0])

        nrep = 0
        y_old = y
        while (criteria>=gradient) and (nrep<=repitition):
            p = np.polyfit(x, y_old, degree)
            y_fit = np.polyval(p, x)
            y_work = np.array(np.minimum(y_fit,y))
            criteria = sum(np.abs((y_work-y)/y))

            y_old = y_work
            nrep = nrep + 1
        
        return_spectra = Raman_Spectra(np.stack((self.wavenumber, self.intensity-y_fit), axis = 1), "modpoly baseline corrected "+self.sample_name)
        self.baseline = y_fit
        self.baseline_method = 'Modified polyfit'

        return return_spectra


    # baseline_als method is adapted from https://stackoverflow.com/questions/29156532/python-baseline-correction-library
    def baseline_als(self, lam = 100, p = 0.01, niter=10):
        # lam is for smoothness and p is for assymmetry
        # return a new spectra

        y = np.copy(self.intensity)
        L = len(y)
        D = sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
        w = np.ones(L)
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = spsolve(Z, w*y)
            w = p * (y > z) + (1-p) * (y < z)
        
        return_spectra = Raman_Spectra(np.stack((self.wavenumber, self.intensity-z), axis = 1), "als baseline corrected "+self.sample_name)
        self.baseline = z
        self.baseline_method = 'Asymmetric least square'
        return return_spectra

    def interpolate(self, start, end, num):
        '''
        input
            start: The starting value of the ramanshift sequence.
            end: The end value of the ramanshift sequence
            num: Number of samples ramanshift to generate.
            xp: The ramanshift coordinate.
            fp: The y-coordinates of the data points, same length as xp.
        
        output
            return_spectra: a new spectra class with interpolated intensities
        '''
        x = np.linspace(start, end, num)
        xp = self.wavenumber
        fp = self.intensity
        y = np.interp(x, xp, fp, left=None, right=None)
        return_spectra = Raman_Spectra(np.stack((x, y), axis = 1), "interpolated "+ self.sample_name)
        return return_spectra

    @classmethod
    def spectra_subtraction(cls, rs_a, rs_b):
        '''
        input
            rs_a: first raman spectra
            rs_b: second raman spectra

        output
            return spectra: a new spectra class with the intensity as the rs_a.intensity - rs_b.intensity
        '''
        if not np.array_equal(rs_a.wavenumber, rs_b.wavenumber):
            raise Exception("Wavenumbers have to be same for two raman spectra")

        new_intensity = rs_a.intensity - rs_b.intensity
        return_spectra = cls(np.stack((rs_a.wavenumber, new_intensity), axis = 1), rs_a.sample_name+' MINUS '+rs_b.sample_name)
        return return_spectra

    def spectra_scaling(self, scale_factor):
        """
        input
            scale_factor: a factor for scaling the intensity
        
        output
            return spectra: a new spectra class with its intensity as intensity * scale_factor
        """
        new_intensity = self.intensity * scale_factor
        return_spectra = Raman_Spectra(np.stack((self.wavenumber, new_intensity), axis = 1), self.sample_name + ' scaled by '+ str(round(scale_factor)))
        return return_spectra
    
    def spectra_smoothing(self, filter_window, filter_degree):

        new_intensity = savgol_filter(self.intensity, filter_window, filter_degree)
        return_spectra = Raman_Spectra(np.stack((self.wavenumber, new_intensity), axis = 1), self.sample_name + 'savgol smoothed ')

        return return_spectra


    def find_raman_peaks(self, filter_window = None, filter_degree = None, lower_prominance = None, higher_prominance = None, lower_height = 0):

        if filter_window is not None and filter_degree is not None:
            intensity = savgol_filter(self.intensity, filter_window, filter_degree)
        else:
            intensity = self.intensity
        raman_peaks = find_peaks(intensity, prominence=(lower_prominance, higher_prominance), height = lower_height)
        self.raman_peaks = raman_peaks

        return raman_peaks

    @staticmethod
    def gaussian(x, mu, FWHM, amp):
        return amp*np.exp(-4*np.log(2)*((x-mu)/FWHM)**2)

    @classmethod
    def multi_gaussian(cls, x, *params):
        if (len( np.array(params)) % 3 ):
            raise Exception("parameters have to be divisible by 3")

        return sum([cls.gaussian(x, *params[ i : i+3 ]) for i in range( 0, len(params),3)])

    @staticmethod
    def lorentzian(x, mu, FWHM, amp):
        return amp/(1+4*((x-mu)/FWHM)**2)

    @classmethod
    def multi_lorentzian(cls, x, *params):
        if (len( np.array(params)) % 3 ):
            raise Exception("parameters have to be divisible by 3")
        return sum([cls.lorentzian(x, *params[ i : i+3 ] ) for i in range( 0, len(params),3)])

    @classmethod
    def glsum(cls, x, mu, FWHM, amp, l_weight):
        return cls.gaussian(x, mu, FWHM, amp) * (1-l_weight) + cls.lorentzian(x, mu, FWHM, amp) * l_weight

    @classmethod
    def multi_glsum(cls, x, *params):
        if (len( np.array(params)) % 4 ):
            raise Exception("parameters have to be divisible by 4")
        return sum([cls.glsum(x, *params[ i : i+4 ] ) for i in range( 0, len(params),4)])

    #@classmethod
    #def voigt(cls, x, )

    def peak_fitting(self, func, start, end, parameters = None, bounds = None, figure_size = (12, 8), peak_function = None):
        '''
        Raman peak fitting
        
        input
            func: the fitting model function used for peak fitting
            start: start raman shift for peak fitting
            end: end raman shift for peak fitting
            parameters: guess parameters for curve fitting
            bounds: bounds for curve fitting
            figure_size: plot the fit result figure
            peak_function: choose the peak function used for plotting each fitted peak

        
        output
            popt and pcov. the return value of scipy curve_fit
        '''

        start_index = np.argmin(np.abs(self.spectra_data[:,0] - start))
        end_index = np.argmin(np.abs(self.spectra_data[:,0] - end))

        x = np.copy(self.wavenumber[start_index:end_index])
        y = np.copy(self.intensity[start_index:end_index])

        if bounds is None:
            popt, pcov = curve_fit(func, x, y, p0=parameters, maxfev = 10000)
        else:
            popt, pcov = curve_fit(func, x, y, p0=parameters, bounds=bounds, maxfev = 10000)

        fig, axs = plt.subplots(1, 1, figsize=figure_size)
        axs.plot(x, y, color = 'k', linewidth = 1)


        # plot individual peaks
        if peak_function is not None:
            sig = signature(peak_function)
            func_para_num = len(sig.parameters)-1
            print(len(sig.parameters)-1)
            camp_i = 0
            cmap = plt.cm.get_cmap('rainbow', popt.shape[0]/func_para_num)
            for i in range( 0, popt.shape[0], func_para_num):
                peak_y = peak_function(x, *popt[i:i+func_para_num])
                axs.plot(x, peak_y, linewidth = 1, color=cmap(camp_i), label = "Mu: " + str("{:.2f}".format(popt[i])) + " FWHM: " + str("{:.2f}".format(popt[i+1])))
                camp_i += 1

        # sum plot
        fitted_y = func(x, *popt)
        axs.plot(x, fitted_y, color = 'b', linewidth = 1)
        axs.legend()


        axs.set_xlabel("Raman shift 1/cm")
        axs.set_ylabel("Intensity")
        axs.hlines(0, x[0], x[-1], colors = 'k', linewidths = 0.5)

        plt.show()
        
            
        return popt, pcov

