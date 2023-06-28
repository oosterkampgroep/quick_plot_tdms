""" quick_plot_tdms.py
Plot the data from a chosen tdms file. This module opens a tkinter 
window in which the file can be chosen, then the group and after 
choosing the channel, the data can be plotted. The user can also choose 
to plot the FFT of the data which opens a new canvas for this plot.
Right-clicking on one of the axes will convert that axis to a 
logarithmic plot.
"""


import tkinter as tk
from tkinter import ttk

import numpy as np
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
from nptdms import TdmsFile


__author__ = "Jaimy Plugge"


FONT = (44)
FILENAMEFONT = (20)


class Mainwindow:
    def __init__(self):
        self.mainwindow = tk.Tk()
        self.mainwindow.title('Quick Plot TDMS')

        # Make sure the program stops as the window gets closed
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.quit_me)

        # UI Settings
        self.entrywidth = 10
        self.xpadding = (5, 5)
        self.ypadding = (2, 2)
        self.relief = tk.RIDGE

        self.file = tk.StringVar()
        self.group = tk.StringVar()
        self.channel = tk.StringVar()
        self.filelist = []
        self.grouplist = []
        self.channellist = []
        self.data_showing = False
        self.fft_showing = False

        self.chooseframe()
        self.plot_frame()

        self.mainwindow.mainloop()

    def chooseframe(self):
        # controls

        width_names = 50

        xpad = (5,5)
        ypad = (2,2)

        controlsframelabel = ttk.Label(text="Choose Data", font=FONT, 
                                       foreground="black")
        controlsframe = ttk.LabelFrame(self.mainwindow, 
                                       labelwidget=controlsframelabel, 
                                       relief=self.relief)
        controlsframe.grid(row=0, column=0, padx=self.xpadding, 
                           pady=self.ypadding, sticky="nsew")

        lbl_file = tk.Label(master=controlsframe, text="TDMS File", font=FONT)
        entry_file = tk.Entry(master=controlsframe, textvariable=self.file, 
                              width=width_names, font=FILENAMEFONT)
        btn_file = tk.Button(master=controlsframe, text="Open", font=FONT, 
                             command=self.openfile)

        lbl_group = tk.Label(master=controlsframe, text="TDMS Group", font=FONT)
        self.combo_group = ttk.Combobox(master=controlsframe, 
                                        values=self.grouplist, 
                                        textvariable=self.group, font=FONT)
        self.combo_group.set(self.file.get())
        self.combo_group['state'] = 'readonly'
        self.combo_group.config(state="disabled")
        self.btn_group = tk.Button(master=controlsframe, text="Open", font=FONT, 
                                   command=self.opengroup)
        self.btn_group.config(state="disabled")

        lbl_channel = tk.Label(master=controlsframe, text="TDMS Channel", 
                               font=FONT)
        self.combo_channel = ttk.Combobox(master=controlsframe, 
                                          values=self.channellist, 
                                          textvariable=self.channel, font=FONT)
        self.combo_channel.set(self.file.get())
        self.combo_channel['state'] = 'readonly'
        self.combo_channel.config(state="disabled")
        self.btn_channel = tk.Button(master=controlsframe, text="Plot", 
                                     font=FONT, command=self.openchannel)
        self.btn_channel.config(state="disabled")

        self.fftvar = tk.IntVar()
        check_fft = tk.Checkbutton(master=controlsframe, text='Plot FFT', 
                                   variable=self.fftvar, onvalue=1, offvalue=0, 
                                   command=self.check_fft)

        lbl_file.grid(row=0,column=0,sticky="nsew")
        entry_file.grid(row=0,column=1,sticky="nsew")
        btn_file.grid(row=0,column=2,sticky="nsew")
        lbl_group.grid(row=1,column=0,sticky="nsew")
        self.combo_group.grid(row=1,column=1,sticky="nsew")
        self.btn_group.grid(row=1,column=2,sticky="nsew")
        lbl_channel.grid(row=2,column=0,sticky="nsew")
        self.combo_channel.grid(row=2,column=1,sticky="nsew")
        self.btn_channel.grid(row=2,column=2,sticky="nsew")
        check_fft.grid(row=2,column=3,sticky="nsew", padx=10)

    def plot_frame(self):
        dataframelabel = ttk.Label(text="Data Plot", font=FONT, 
                                   foreground="black")
        dataframe = ttk.LabelFrame(self.mainwindow, labelwidget=dataframelabel, 
                                   relief=self.relief)
        dataframe.grid(row=1, column=0, padx=self.xpadding, pady=self.ypadding, 
                       sticky="nsew")

        self.fig = Figure(figsize=(12,3), tight_layout=True)
        self.axs = self.fig.add_subplot(111)
        self.axs.set_xlabel('Time [s]')
        self.axs.set_ylabel('Amplitude [V]')
        self.axs.grid()

        self.canvas = tkagg.FigureCanvasTkAgg(self.fig, master=dataframe)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        self.navtoolbar = tkagg.NavigationToolbar2Tk(self.canvas, dataframe)

    def plot_fft_frame(self):
        self.fft_showing = True

        fftframelabel = ttk.Label(text="FFT Plot", font=FONT, foreground="black")
        self.fftframe = ttk.LabelFrame(self.mainwindow, labelwidget=fftframelabel, 
                                       relief=self.relief)
        self.fftframe.grid(row=2, column=0, padx=self.xpadding, 
                           pady=self.ypadding, sticky="nsew")

        self.fftfig = Figure(figsize=(12,3), tight_layout=True)
        self.fftaxs = self.fftfig.add_subplot(111)
        self.fftaxs.set_xlabel('Frequency [Hz]')
        self.fftaxs.set_ylabel(r'Amplitude [V/$\sqrt{Hz}$]')

        self.fftaxs.grid()

        self.fftcanvas = tkagg.FigureCanvasTkAgg(self.fftfig, master=self.fftframe)
        self.fftcanvas.draw()
        self.fftcanvas.get_tk_widget().pack()

        self.fftnavtoolbar = tkagg.NavigationToolbar2Tk(self.fftcanvas, 
                                                        self.fftframe)

        self.fftcanvas.mpl_connect('button_press_event', self.rescale_callback)

    def update_fft(self):
        measure_freq = 1. / self.props["wf_increment"]
        freqs = np.fft.fftfreq(self.data.size, d=self.props["wf_increment"]) # x-as
        window = 2* np.pi*np.arange(len(self.data))/len(self.data)
        window = 0.5*(1-np.cos(window))
        windowdata = self.data * window
        freq_res = measure_freq/len(self.data)
        #factor 1.63 from hanning window correction, y-axis  
        fft = np.fft.fft(windowdata)[(freqs>=0)]*1.63 / (len(self.data)*np.sqrt(freq_res))
        freqs = freqs[(freqs>=0)]
        
        xscale = self.fftaxs.get_xscale()
        yscale = self.fftaxs.get_yscale()

        self.fftaxs.cla()
        self.fftaxs.plot(freqs, np.abs(fft))
        self.fftaxs.set_xlabel('Frequency [Hz]')
        self.fftaxs.set_ylabel(r'Amplitude [V/$\sqrt{Hz}$]')
        self.fftaxs.grid()
        self.fftaxs.set_xscale(xscale)
        self.fftaxs.set_yscale(yscale)
        self.fftcanvas.draw()
        self.fftnavtoolbar.update()

    def openfile(self):
        self.files = tk.filedialog.askopenfilenames(filetypes=[('TDMS File', '*.tdms')])
        
        files_string = ', '.join(self.files)

        self.file.set(files_string)
        
        if self.file.get() != "":
            self.tdms_file = TdmsFile(self.files[0])

            self.grouplist = [group.name for group in self.tdms_file.groups()]
            self.group.set(self.grouplist[0])
            self.combo_group.config(state="normal")
            self.combo_group["values"] = self.grouplist
            self.combo_group['state'] = 'readonly'
            self.btn_group.config(state="normal")

            self.combo_channel.config(state="disabled")
            self.btn_channel.config(state="disabled")

    def opengroup(self):
        self.channellist = [channel.name for channel in self.tdms_file[self.group.get()].channels()]
        self.channel.set(self.channellist[0])
        self.combo_channel.config(state="normal")
        self.combo_channel['state'] = 'readonly'
        self.combo_channel["values"] = self.channellist
        self.btn_channel.config(state="normal")

    def openchannel(self):
        for i, file in enumerate(self.files):
            tdms_file = TdmsFile(file)
            channel = tdms_file[self.group.get()][self.channel.get()]
            if i == 0:
                self.data = channel[:]
                self.props = channel.properties
                time = channel.time_track()
            else:
                time1 = channel.time_track()
                self.data = np.append(self.data, channel[:])
                time = np.append(time, time1 + time[-1] + time[1])

        self.axs.cla()
        self.axs.plot(time, self.data)
        self.axs.set_xlabel('Time [s]')
        self.axs.set_ylabel('Amplitude [V]')
        self.axs.grid()
        self.canvas.draw()
        self.navtoolbar.update()

        self.data_showing = True

        if self.fftvar.get():
            if not self.fft_showing:
                self.plot_fft_frame()
            self.update_fft()

    def rescale_callback(self, event):
        if event.button == 3 and event.inaxes == None:
            if event.x > event.y: 
                if self.fftaxs.get_xscale() == 'linear':
                    self.fftaxs.set_xscale('log')
                else: 
                    self.fftaxs.set_xscale('linear')
            else:
                if self.fftaxs.get_yscale() == 'linear':
                    self.fftaxs.set_yscale('log')
                else: 
                    self.fftaxs.set_yscale('linear') 
            self.fftaxs.autoscale()
            self.fftcanvas.draw()
            self.fftnavtoolbar.update()

    def check_fft(self):
        if self.data_showing and self.fftvar.get() and not self.fft_showing:
            self.plot_fft_frame()
            self.update_fft()
        elif self.fft_showing and not self.fftvar.get():
            self.fftframe.grid_forget()
            self.fft_showing = False

    def quit_me(self):
        #print('Closing the program')
        self.mainwindow.quit()
        self.mainwindow.destroy()


def main():
    Mainwindow()


if __name__ == "__main__":
    main()