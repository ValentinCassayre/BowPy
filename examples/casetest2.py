"""
Testscript for all cases
"""
from __future__ import absolute_import, print_function

import numpy as np

import matplotlib

# If using a Mac Machine, otherwitse comment the next line out:
matplotlib.use('TkAgg')


import os

from obspy import read as read_st
import bowpy.misc.Muenster_Array_Seismology_Vespagram as MAS
from bowpy.filter.fk import pocs_recon
from bowpy.util.array_util import stream2array, array2stream

import os
import sys

noise = np.fromfile('../data/test_datasets/randnumbers/noisearr.txt')
noise = noise.reshape(20,300)

with open("../data/test_datasets/ricker/rickerlist.dat", 'r') as fh:
        rickerlist = np.array(fh.read().split()).astype('str')

noisefoldlist = ["no_noise"] #,"10pct_noise", "20pct_noise", "50pct_noise", "60pct_noise", "80pct_noise"]
noiselevellist = np.array([0.]) #, 0.1, 0.2, 0.5, 0.6, 0.8]) 
alphalist = np.linspace(0.01, 0.9, 10)
maxiterlist = np.arange(11)[1:]
bwlist = [1,2,4]
taperlist = [2,4,5,8,200]

stream_org = read_st('/home/s_schn42/dev/FK-Toolbox/data/test_datasets/ricker/original/SR.QHD')
d0 = stream2array(stream_org.copy(), normalize=True)
peaks = np.array([[-13.95      ,   6.06      ,  20.07      ],[  8.46648822,   8.42680793,   8.23354933]])
errors = []
FPATH = '/home/s_schn42/dev/FK-Toolbox/data/test_datasets/ricker/'
for i, noisefolder in enumerate(noisefoldlist):
    print("##################### NOISELVL %i %% #####################\n" % int(noiselevellist[i] * 100.) )
    for filein in rickerlist:
        print("##################### CURRENT FILE %s  #####################\n" % filein )
        PICPATH = filein[:filein.rfind("/"):] + "/" + noisefolder + "/"
        FNAME   = filein[filein.rfind("/"):].split('/')[1].split('.')[0]
        plotname = FPATH + FNAME + 'pocs_' + 'nlvl' + str(noiselevellist[i]) + '_linear''.png'
        plotname2 = FPATH + FNAME + 'pocs_' + 'nlvl' + str(noiselevellist[i]) + '_mask' '.png'
        if not os.path.isdir(PICPATH):
                os.mkdir(PICPATH)
        PATH = filein
        stream = read_st(PATH)
        data = stream2array(stream.copy(), normalize=True) + noiselevellist[i] * noise
        srs = array2stream(data)
        Qlinall = []
        Qbwmaskall = []
        Qtapermaskall = []
        QSSAall = []
        
        if 'original' in PICPATH:
                DOMETHOD = 'denoise'
        else:
                DOMETHOD = 'recon'

        for alpha in alphalist:

            name1 = 'pocs_' + str(noiselevellist[i]) + '-noise_' + '{:01.2}'.format(alpha) + '-alpha_' + 'linear' + '.png'
            name2 = 'pocs_' + str(noiselevellist[i]) + '-noise_' + '{:01.2}'.format(alpha) + '-alpha_' + 'exp' + '.png'             
            picpath1 = PICPATH + name1
            picpath2 = PICPATH + name2
            plotnameQall = PICPATH + 'pocs_' + str(noiselevellist[i]) + '{:01.2}'.format(alpha) + '-alpha' + DOMETHOD + 'lin'
            plotnameQmbwall = PICPATH + 'pocs_' + str(noiselevellist[i]) + '{:01.2}'.format(alpha) + '-alpha' + DOMETHOD + 'mask_bw'
            plotnameQmtaperall = PICPATH + 'pocs_' + str(noiselevellist[i]) + '{:01.2}'.format(alpha) + '-alpha' + DOMETHOD + 'mask_taper'
            plotnameQSSAall = PICPATH + 'pocs_' + str(noiselevellist[i]) + '{:01.2}'.format(alpha) + '-alpha' + DOMETHOD + 'SSA'

            
            print("##################### CURRENT ALPHA %f  #####################\n" % alpha )
            for maxiter in maxiterlist:

                print('POCS RECON WITH %i ITERATIONS' % maxiter, end="\r")
                sys.stdout.flush()
                data_org = d0.copy()
                srs = array2stream(data.copy())
                st_rec = pocs_recon(srs, maxiter, dmethod='recon', method='linear', alpha=alpha)
                drec = stream2array(st_rec, normalize=True)
                Q = np.linalg.norm(data_org,2)**2. / np.linalg.norm(data_org - drec,2)**2.                  
                Qlinall.append([alpha, maxiter, 10.*np.log(Q)])


                savepath = plotnameQall + '.dat'
                np.savetxt(savepath, Qlinall)

