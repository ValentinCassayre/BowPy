from __future__ import absolute_import, print_function

import numpy as np

import matplotlib

# If using a Mac Machine, otherwitse comment the next line out:
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import scipy as sp
import scipy.signal as signal

import obspy
from obspy.geodetics.base import gps2dist_azimuth, kilometer2degrees, locations2degrees
from obspy.taup import TauPyModel
from obspy import read_inventory as read_inv
from obspy import read_events as read_cat

# import sipy
import bowpy.util.fkutil as fku
import bowpy.util.base as base

from bowpy.misc.read import read_st
from bowpy.filter.fk import fk_filter, fk_reconstruct
from bowpy.util.fkutil import fktrafo
from bowpy.util.array_util import attach_network_to_traces, attach_coordinates_to_traces,\
stream2array, array2stream, attach_network_to_traces, attach_coordinates_to_traces, epidist2nparray, \
alignon

##########
st = read_st('../data/workfiles/UT_24_10_09/FKFIL_PREP.pickle')

##########

###################################
noise = np.fromfile('../data/test_datasets/randnumbers/PCnoise.dat')
noise = noise.reshape(20,300)
peaks = np.array([[-13.95      ,   6.06      ,  20.07      ],[  8.46648822,   8.42680793,   8.23354933]])
stri = read_st("../data/test_datasets/ricker/original/SR.QHD")
stri.normalize(global_max=True)
data = stream2array(stri) 
dn = data + 0.3 * noise
stn = array2stream(dn, stri)
stn.normalize(global_max=True)

#### TEST ROUTINE FOR MAINPHASE AND PRECURSOR WITH DIFFERENT DELTA U ###
def test(x, case, nf=True):
    from obspy import Stream, Trace
    from bowpy.util.array_util import stack
    import sys
    n_of_samples        = 2000
    n_of_traces         = 20
    delta_traces        = 100
    n_of_ricker_samples = int(n_of_samples/10.)
    width_of_ricker     = int(n_of_samples/100.)
    shift_of_ricker     = 1000
    
    rslope=0
    MR = base.create_ricker(n_of_samples, n_of_traces, delta_traces, rslope, n_of_ricker_samples, width_of_ricker, shift_of_ricker)

    PC_u = [30] #np.linspace(0,100,101)
    PC = base.create_ricker(n_of_samples, n_of_traces, delta_traces, 0, n_of_ricker_samples, width_of_ricker, shift_of_ricker- 3*n_of_ricker_samples )
    data_org = MR + PC
    

    data_fk_org = stack(data_org) #fk_filter(st_org, ftype='extract', fshape=['butterworth', 4, 2])
    data_fk_org = data_fk_org / data_fk_org.max()
    st_org = Trace(data_fk_org)
    

    bw_length = np.linspace(1, n_of_traces/2., n_of_traces/2.).astype('int')#[::2]
    bw_slope = np.linspace(1, 100., 100).astype('int')
    allt = Stream()
    allt += st_org
    allsynths = []
    Qall=[]
    for length in bw_length:
        for slope in bw_slope:

            for u in PC_u:
                u = int(u)
                PC      = base.create_ricker(n_of_samples, n_of_traces, delta_traces, u, n_of_ricker_samples, width_of_ricker, shift_of_ricker- 3*n_of_ricker_samples )
                data    = MR + PC

                allsynths.append(data)

                st_tmp  = array2stream(data)
                if length == 0:
                    st_fk   = fk_filter(st_tmp, ftype='extract', fshape=['spike'])[0]
                else:
                    if case == 1:
                        st_fk   = fk_filter(st_tmp, ftype='extract', fshape=['boxcar', None, length])[0]
                    elif case == 2:
                        st_fk   = fk_filter(st_tmp, ftype='extract', fshape=['butterworth', slope, length])[0]
                    elif case == 3:
                        st_fk   = fk_filter(st_tmp, ftype='extract', fshape=['taper', slope, length])[0]
                data_fk = st_fk.data/st_fk.data.max()   
                allt += st_fk

                Q = np.linalg.norm(data_fk_org,2)**2. / np.linalg.norm(data_fk_org - data_fk,2)**2.
                Q = 10.*np.log(Q)
                Qall.append([length, slope, Q])
                print('Q = %f, length = %f, slope = %f' % (Q,length, slope),  end="\r")
                sys.stdout.flush()

    
    np.savetxt('../Qtlist.dat', Qall)

    fs = 22
    if nf:
        fig, ax = plt.subplots()
    else:
        fig = plt.gcf()
        ax = plt.gca()

    ax.set_xlabel(r'Windolength ($k$)', fontsize=fs)
    ax.set_ylabel('Q', fontsize=fs)
    ax.set_xlim(0,n_of_traces/2.)
    ax.tick_params(axis='both', which='major', labelsize=fs)
    ax.set_title(r'FK-Filter dependency on $k$ windowlength', fontsize=fs)
    #ax.plot(np.linspace(1,0, len(Qall))[::-1],Qall, 'ro')
    ax.plot(bw_length, Qall, 'ro')
    plt.show()

fig = plt.gcf()
ax = plt.gca()
fig.set_size_inches(10,12)
#ofile = '../bwl_' + str(length) + '_corner' + str(slope) + '.png'
ofile = '../Q_k-window_compare_bw4.png' 
fig.savefig(ofile, dpi=200)

#fku.plot(allt, zoom=5, savefig=ofile_stream)
with open('../Qtlist.dat') as fh:
    D = np.array(fh.read().split()).astype('float')

Qtemp= D.reshape(1000,3)
Qtt = Qtemp.transpose()
Qtt[1] -= 1
Qtt[0] -= 1
Qtemp = Qtt.transpose()
xrange = np.linspace(0,99, 100)
yrange = np.linspace(0,9,10)
Qmat = np.zeros((100,10))
for x in xrange:
    for y in yrange:
        for i, item in enumerate(Qtemp):
            if item[1] == x and item[0]==y:
                print('%i, %i, %f, %i' % (x, y, item[2], i))
                Qmat[x,y] = item[2]

#plt.imshow(Qmat, aspect='auto', origin='lower', interpolation='none')
import matplotlib as mpl
from matplotlib import ticker
fig, ax = plt.subplots(frameon=False)

Qplot = np.zeros((100, 9))
Qplot = Qmat[:,1:]
#Qplot=Qmat
maxindex = Qplot.argmax()
Qmax=np.zeros(Qplot.shape)
#Qmax[:,:]= np.float64('nan')
Qmax[np.unravel_index(maxindex, (100,9))] = 10000

extent =(1,10, 1,100)
im1 = ax.imshow(Qplot, aspect='auto', origin='lower', interpolation='none',cmap='Blues', extent=extent)
ax.set_ylabel('Slope a', fontsize=fs)
ax.set_xlabel('Windowlength(k)', fontsize=fs)
ax.tick_params(axis='both', which='both', labelsize=fs)
ax.xaxis.labelpad = 0.5
cbar = fig.colorbar(im)
cbar.ax.set_ylabel('Q', fontsize=fs)
cbar.ax.tick_params(labelsize=fs)

#ax.xaxis.set_minor_formatter(ticker.NullFormatter())

# Customize minor tick labels
ax.xaxis.set_major_locator(ticker.FixedLocator(np.linspace(1.5,9.5,9)))
ax.xaxis.set_major_formatter(ticker.FixedFormatter(np.linspace(1,9,9).astype('int')))

#ax.yaxis.set_major_formatter(ticker.NullFormatter())
#ax.yaxis.set_major_locator(ticker.NullLocator())
# Customize minor tick labels
ax.yaxis.set_major_locator(ticker.FixedLocator([1.5, 10.5, 20.5, 30.5, 40.5, 50.5, 60.5, 70.5, 80.5, 90.5]))#np.linspace(1.5,99.5,9)))
ax.yaxis.set_major_formatter(ticker.FixedFormatter([ 1, 10, 20, 30, 40, 50, 60, 70, 80, 90]))



plt.hold(True)

im2 = ax.imshow(Qmax, aspect='auto', alpha = .5, origin='lower', interpolation='none', extent=extent, cmap='Reds')



################ testsetup
#read noise
noise = np.fromfile('../data/test_datasets/randnumbers/noisearr.txt')
noise = noise.reshape(20,300)

with open("../data/test_datasets/ricker/rickerlist.dat", 'r') as fh:
    rickerlist = np.array(fh.read().split()).astype('str')

noisefoldlist = ["no_noise","10pct_noise", "20pct_noise", "50pct_noise", "60pct_noise", "80pct_noise"]
noiselevellist = np.array([0., 0.1, 0.2, 0.5, 0.6, 0.8]) 

for i, noisefolder in enumerate(noisefoldlist):
    for filein in rickerlist:
        PICPATH = "../data/test_datasets/ricker/" + noisefolder + "/"
        PATH = "../data/test_datasets/ricker/" + filein + "/"
        srs = read_st(PATH)
        if i != 0:
            data = stream2array(srs) * noiselevellist[i] * noise
            srs = array2stream(data)

        name = 'boxcar_auto' + '.png'
        picpath = PICPATH + name
        st_rec = fk_reconstruct(srs, slopes=[-2,2], deltaslope=0.001, maskshape=['boxcar', None], solver='ilsmr',method='interpolate', mu=2.5e-2, tol=1e-12)
        st_rec.normalize()
        fku.plot_data(stream2array(st_rec), savefig=picpath)

        taperrange = [0.25, 0.5, 1, 1.5]
        for ts in taperrange:
            st_rec = fk_reconstruct(srs, slopes=[-2,2], deltaslope=0.001, maskshape=['taper', tr], solver='ilsmr',method='interpolate', mu=2.5e-2, tol=1e-12)


        bwrange = [1,2,4,8]







#########3 L-curve
global Binv
global madj
murange = np.logspace(-40, 40, 100)
L = np.zeros((3, murange.size))
print("Initiating matrices... \n \n")
A = Ts.dot(FH.dot(Ys))
#Ah = A.conjugate().transpose()
#madj = Ah.dot(dv)

for i,muval in enumerate(murange):
    print(muval)
    stw = stn.copy()
    #E = muval * sparse.eye(A.shape[0])
    #B = A + E
    #Binv = sparse.linalg.inv(B)
    #def getmnorm(x):
    #   return print(np.linalg.norm(A.dot(x) - madj))

    #x = sparse.linalg.cg(Binv, madj, maxiter=100)#, callback=getmnorm)
    #dfk = x[0].reshape(20,300)
    #d = np.fft.ifft2(dfk).real
    #d = d/d.max()

    #rnorm = np.linalg.norm(x[0],2)
    #snorm = np.linalg.norm(A.dot(x[0]) - madj,2)

    st_rec, rnorm, snorm = fk_reconstruct(stw, slopes=[-2,2], deltaslope=0.001, maskshape=['butterworth', 4], fulloutput=False, solver='lsqr',method=20, mu=muval, tol=0, peakinput=peaks)

    L[0][i]= muval
    L[1][i]= rnorm
    L[2][i]= snorm


#stuni = read_st("/Users/Simon/dev/FK-Filter/data/synthetics_uniform/SUNEW.QHD")
sts = read_st("../data/synthetics_uniform/SUNEW.QHD")
sts.normalize()
#invuni = read_inv("/Users/Simon/dev/FK-Filter/data/synthetics_uniform/SUNEW_inv.xml")
inv = read_inv("../data/synthetics_uniform/SUNEW_inv.xml")
#cat = read_cat("/Users/Simon/dev/FK-Filter/data/synthetics_random/SRNEW_cat.xml")
cat = read_cat("../data/synthetics_random/SRNEW_cat.xml")
attach_network_to_traces(sts, inv[0])
attach_coordinates_to_traces(sts, inv, cat[0])

stri = read_st("../data/test_datasets/ricker/original/SR.QHD")
stri.normalize()
attach_network_to_traces(stri, inv)
attach_coordinates_to_traces(stri, inv, cat[0])

st = read_st("../data/synthetics_uniform/SUGAP.QHD")
#stgap = read_st("/Users/Simon/dev/FK-Filter/data/synthetics_uniform/SUGAPTRUNC.QHD")
stgap = read_st("../data/synthetics_uniform/SUGAPTRUNC.QHD")


stuni_al = alignon(stuni.copy(), invuni, cat[0], phase='PP', maxtimewindow=350)
stuni_al=stuni.copy()
st = stuni_al.copy()

fkdata = fktrafo(stuni_al, invuni, cat[0])

fkr = fk_reconstruct(ns, invuni, cat[0], mu=5e-2)
M = stream2array(stuni_al)
t_axis = np.linspace(0,stuni_al[0].stats.delta * stuni_al[0].stats.npts, stuni_al[0].stats.npts)


stran = read_st("../data/synthetics_random/SRNEW.QHD")
stran.normalize()
invran= read_inv("../data/synthetics_random/SRNEW_inv.xml")
attach_network_to_traces(stran, invran)
attach_coordinates_to_traces(stran, invran, cat[0])
epiran = epidist2nparray(epidist(invran, cat[0]))

###############
with open("../data/test_datasets/randnumbers/rand10.txt", 'r') as fh:
    rand10 = np.array(fh.read().split()).astype('int')
with open("../data/test_datasets/randnumbers/rand20.txt", 'r') as fh:
    rand20 = np.array(fh.read().split()).astype('int')
with open("../data/test_datasets/randnumbers/rand50.txt", 'r') as fh:
    rand50 = np.array(fh.read().split()).astype('int')
with open("../data/test_datasets/randnumbers/rand80.txt", 'r') as fh:
    rand80 = np.array(fh.read().split()).astype('int')


randlist = [rand10, rand20, rand50, rand80 ] 
stlist = [[stri, 'ricker']] #, [sts, 'instaseis']]
for streams in (stlist):
    for values in randlist:
        stemp =  streams[0].copy()
        attach_network_to_traces(stemp, inv)
        attach_coordinates_to_traces(stemp, inv, cat[0])
        for no in values:
            name = 'SR' + str(int( 100. - len(values)/20.*100.)) +'.QHD'
            stemp[no].data = np.zeros(300)
            stemp[no].stats.zerotrace = "True"
            stemp.write("../data/test_datasets/%s/%s" % (streams[1],name), format='Q')


#############



epid = fku.epidist2nparray(fku.epidist_stream(st, inv, cat))
fkspectra, periods = fk_filter(st, ftype='LS', inv=inv, cat=cat, fktype="eliminate")
fkfft = abs(np.fft.fftn(ad))
samplingrate = 0.025

#Example data flow 20.01.2016
trace = ad[0]
xrange = np.linspace(0, trace.size*0.025, trace.size)




tracefft = np.fft.rfft(trace)
freq = np.fft.rfftfreq(trace.size, samplingrate)
freq = freq * 2. * np.pi
fftnorm=tracefft/max(tracefft)

frange_new = np.linspace(freq[1], max(freq), trace.size/2 + 1)
epidist = np.linspace(0, trace.size, trace.size) * 0.025
tracels_new = signal.lombscargle(epidist, trace.astype('float'), frange_new)


tracels = fku.ls2ifft_prep(tracels_new, trace)
fls = fku.convert_lsindex(frange_new, 0.025)



plt.plot(freq, abs((tracefft/max(tracefft)).real))
plt.plot(frange_new,tracels_new/max(tracels_new))
plt.plot(fls, tracels_new/max(tracels_new))
plt.plot(abs((tracefft/max(tracefft)).real))
plt.show()



plt.plot(tracels/max(tracels))
plt.plot(abs((tracefft/max(tracefft)).real))
plt.show()

plt.plot(np.fft.irfft(tracels))
plt.show()



# Test Sinus
A = 2.
w = 1.
phi = 0.5 * np.pi

nin = 1000
nout = 100000
x = np.linspace(0.01, 10*np.pi, nin)
y = A * np.sin(w*x+phi)

yfft = np.fft.rfft(y)
yfft = yfft/max(yfft)

steps= max(x)/y.size

f_fft = np.fft.rfftfreq(y.size, steps) * 2. * np.pi

#frange = np.linspace(0.01, 10, nin/2)
frange = np.linspace(f_fft[1], max(f_fft), nin/2)
yls = signal.lombscargle(x, y, frange)
yls = yls/max(yls)
yls2ifft = fku.ls2ifft_prep(yls)



"""

#Example data flow
"""

#fk_filter(stream, inventory, catalog, phase)
#data=create_signal(no_of_traces=1,len_of_traces=12,multiple=False)
#datatest=fku.create_sine(no_of_traces=1, no_of_periods=2)

"""
##################INSTASEIS###############################
Instaseis Source: Honshu
    origin time      : 2011-03-11T05:47:32.760000Z
    Longitude        :  143.1 deg
    Latitude         :   37.5 deg
    Depth            : 2.0e+01 km
    Moment Magnitude :   13.82
    Scalar Moment    :   5.31e+29 Nm
    Mrr              :   1.73e+29 Nm
    Mtt              :  -2.81e+28 Nm
    Mpp              :  -1.45e+29 Nm
    Mrt              :   2.12e+29 Nm
    Mrp              :   4.55e+29 Nm
    Mtp              :  -6.57e+28 Nm
"""
#get data with instaseis
import obspy
from obspy.geodetics.base import gps2dist_azimuth, kilometer2degrees, locations2degrees
from obspy import read as read_st
from obspy import read_inventory as read_inv
from obspy import read_events as read_cat
from obspy.taup import TauPyModel

import numpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import scipy as sp
import scipy.signal as signal
from numpy import genfromtxt

from bowpy.util.array_util import get_coords

import os
import datetime

import bowpy.filter.fk as fk
from bowpy.filter.fk import fk_filter
import bowpy.util.fkutil as fku
import instaseis as ins

uniform=False
real=True
db = ins.open_db("/Users/Simon/dev/instaseis/10s_PREM_ANI_FORCES")
#db = ins.open_db("/local/s_schn42/instaseis/10s_PREM_ANI_FORCES")
tofe = obspy.UTCDateTime(2009, 10, 24, 14, 40, 44, 770000)
lat = -6.1165
lon = 130.429
depth = 140300
aperture=20
no_of_stations=20
# in degrees
distance_to_source=100
# magnitude of randomness 
magn=1.

#output

streamfile = "synth1.pickle"

qstfile = None #"SYNTH_OUT.QST"
invfile = "synth1_inv.xml"
catfile = "synth1_cat.xml"

source = ins.Source(
latitude=lat, longitude=lon, depth_in_m=depth,
m_rr = 0.526e26 / 1E7,
m_tt = -2.1e26 / 1E7,
m_pp = -1.58e26 / 1E7,
m_rt = 1.08e+26 / 1E7,
m_rp = 2.05e+26 / 1E7,
m_tp = 0.607e+26 / 1E7,
origin_time=tofe
)

x = []
station_range = np.linspace(0,aperture-1,no_of_stations) + 100.
#r = np.random.randn(no_of_stations)
#randrange = station_range + magn * r  
#randrange[0] = station_range[0]
#randrange[no_of_stations-1] = station_range[no_of_stations-1]
# while randrange.max() > randrange[19]:
#   i = randrange.argmax()
#   randrange[i] = randrange[i]-0.1

# randrange.sort()


randrange = np.array([ 100.        ,  101.74222711,  102.8608334 ,  104.13732881,
        105.28349288,  106.78556465,  107.488736  ,  108.34593815,
        109.6161234 ,  110.27633321,  111.35174204,  112.90012348,
        113.63875348,  114.34439107,  115.29740496,  116.96181391,
        117.24875298,  117.77155468,  118.14675172,  119.        ])




with open( qstfile, "w") as fh:
    if uniform:
        k=0
        for i in station_range:
            slon = i
            name="X"+str(int(k))
            print(name)
            x.append(ins.Receiver(latitude="54", longitude=str(slon), network="LA", station=name ))
            latdiff = gps2dist_azimuth(54,0,54,slon)[0]/1000.
            fh.write("%s    lat:     54.0 lon:     %f elevation:   0.0000 array:LA  xrel:      %f yrel:      0.00 name:ADDED BY SIMON \n" % (name, slon, latdiff))
            k+=1
    elif real:

        for station in network:
            x.append(ins.Receiver(latitude=str(station.latitude), longitude=str(station.latitude), network=str(network.code), station=str(station.code) ))
    else:
        for i, slon in enumerate(randrange):
            name="X"+str(int(i))
            x.append(ins.Receiver(latitude="54", longitude=slon, network="RA", station=name ))
            latdiff = gps2dist_azimuth(54,0,54,slon)[0]/1000.
            fh.write("%s    lat:     54.0 lon:     %f elevation:   0.0000 array:RA  xrel:      %f yrel:      0.00 name:ADDED BY SIMON \n" % (name, slon, latdiff))      

st_synth = []    
for i in range(len(x)):
    st_synth.append(db.get_seismograms(source=source, receiver=x[i]))



stream=st_synth[0]
for i in range(len(st_synth))[1:]:
    stream.append(st_synth[i][0])


#stream.write("../data/synth.sac", format="SAC")
#stream.write("../data/SYNTH.QHD", format="Q")


"""
Write quakeml file
"""


with open( catfile, "w") as fh:
    fh.write("<?xml version=\'1.0\' encoding=\'utf-8\'?> \n")
    fh.write("<q:quakeml xmlns:q=\"http://quakeml.org/xmlns/quakeml/1.2\" xmlns:ns0=\"http://service.iris.edu/fdsnws/event/1/\" xmlns=\"http://quakeml.org/xmlns/bed/1.2\"> \n")
    fh.write("  <eventParameters publicID=\"smi:local/6b269cbf-6b00-4643-8c2c-cbe6274083ae\"> \n")
    fh.write("    <event publicID=\"smi:service.iris.edu/fdsnws/event/1/query?eventid=3279407\"> \n")
    fh.write("      <preferredOriginID>smi:service.iris.edu/fdsnws/event/1/query?originid=9933375</preferredOriginID> \n")
    fh.write("      <preferredMagnitudeID>smi:service.iris.edu/fdsnws/event/1/query?magnitudeid=16642444</preferredMagnitudeID> \n")
    fh.write("      <type>earthquake</type> \n")
    fh.write("      <description ns0:FEcode=\"228\"> \n")
    fh.write("        <text>NEAR EAST COAST OF HONSHU, JAPAN</text> \n ")
    fh.write("        <type>Flinn-Engdahl region</type> \n")
    fh.write("      </description> \n")
    fh.write("      <origin publicID=\"smi:service.iris.edu/fdsnws/event/1/query?originid=9933375\" ns0:contributor=\"ISC\" ns0:contributorOriginId=\"02227159\" ns0:catalog=\"ISC\" ns0:contributorEventId=\"16461282\"> \n")
    fh.write("        <time> \n")
    fh.write("          <value>%s</value> \n" % tofe)
    fh.write("        </time> \n")
    fh.write("        <latitude> \n")
    fh.write("          <value>%f</value> \n" %lat)
    fh.write("        </latitude>\n")
    fh.write("        <longitude> \n")
    fh.write("          <value>%f</value> \n" %lon)
    fh.write("        </longitude>\n")
    fh.write("        <depth> \n")
    fh.write("          <value>%f</value> \n" %depth)
    fh.write("        </depth>\n")
    fh.write("        <creationInfo> \n")
    fh.write("          <author>Simon</author> \n")
    fh.write("        </creationInfo> \n")
    fh.write("      </origin> \n")
    fh.write("      <magnitude publicID=\"smi:service.iris.edu/fdsnws/event/1/query?magnitudeid=16642444\"> \n")
    fh.write("        <mag> \n")
    fh.write("          <value>9.1</value> \n")
    fh.write("        </mag> \n")
    fh.write("        <type>MW</type> \n")
    fh.write("        <originID>smi:service.iris.edu/fdsnws/event/1/query?originid=9933383</originID> \n")
    fh.write("        <creationInfo> \n")
    fh.write("          <author>Simon</author> \n")
    fh.write("        </creationInfo> \n")
    fh.write("      </magnitude> \n")
    fh.write("    </event> \n")
    fh.write("  </eventParameters> \n")
    fh.write("</q:quakeml>")



"""
Write station-files for synthetics
"""

with open( invfile, "w") as fh:
    fh.write("<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n")
    fh.write("<FDSNStationXML schemaVersion=\"1.0\" xmlns=\"http://www.fdsn.org/xml/station/1\">\n")
    fh.write("  <Source>IRIS-DMC</Source>\n")
    fh.write("  <Sender>IRIS-DMC</Sender>\n")
    fh.write("  <Created>2015-11-05T18:22:28+00:00</Created>\n")
    fh.write("  <Network code=\"LA\" endDate=\"2500-12-31T23:59:59+00:00\" restrictedStatus=\"open\" startDate=\"2003-01-01T00:00:00+00:00\">\n")
    fh.write("    <Description>Synthetic Array - Linear Array</Description>\n")
    fh.write("    <TotalNumberStations>20</TotalNumberStations>\n")
    fh.write("    <SelectedNumberStations>20</SelectedNumberStations>\n")

    if not uniform:
        station_range = randrange
    j=0
    for i in station_range:
        slon=i
        lat=54.0
        name="X"+str(int(j))
        fh.write("    <Station code=\"%s\" endDate=\"2011-11-17T23:59:59+00:00\" restrictedStatus=\"open\" startDate=\"2010-01-08T00:00:00+00:00\">\n" % name)
        fh.write("      <Latitude unit=\"DEGREES\">%f</Latitude>\n" % lat)
        fh.write("      <Longitude unit=\"DEGREES\">%f</Longitude>\n" % slon)
        fh.write("      <Elevation>0.0</Elevation>\n")
        fh.write("      <Site>\n")
        fh.write("        <Name> %s </Name>\n" % name)
        fh.write("      </Site>\n")
        fh.write("    <CreationDate>2010-01-08T00:00:00+00:00</CreationDate>\n")
        fh.write("    </Station>\n")
        j += 1
    fh.write("  </Network>\n")
    fh.write("</FDSNStationXML>")

inv=read_inv(invfile)
cat=read_cat(catfile)

st = stream.select(component="Z")
st.write( streamfile, format="Q")

##########################################################################################
#create Q station-file
with open("SYNTH.QST", "w") as fh:
    for i in station_range:
        slon=i
        latdiff = gps2dist_azimuth(0.1,0,0.1,lon)[0]/1000.
        #print "X%s    lat:     0.0 slon:     %f elevation:   0.0000 array:LA  xrel:      %f yrel:      0.00 name:ADDED BY SIMON" % (i, lon, latdiff)
        fh.write("X%s    lat:     0.0 lon:     %f elevation:   0.0000 array:LA  xrel:      %f yrel:      0.00 name:ADDED BY SIMON \n" % (i, slon, latdiff))



#Calculate Arrivals

#inv=read_inv("../data/synth_inv.xml")

latitude = 0.0
longitude = 0.0
m = TauPyModel(model="ak135")
Plist = ["P", "Pdiff", "PP"]
epidist = []
arrivaltime = []

for i in range(len(stream)):
    elat = latitude
    elon = longitude
    slat =  inv[0][i].latitude
    slon =  inv[0][i].longitude
    epidist.append(locations2degrees(slat,slon,elat,elon))
    arrivaltime.append(m.get_travel_times(source_depth_in_km=100.0, distance_in_degree=epidist[i]))

tofe

"""
Plotting
"""
pexuni = fku.stream2array(read_st("../data/synthetics_uniform/SYNTH_UNIFORM_PP_FK_EX.QHD").normalize())
pexuni = np.roll(pexuni, -35)
pexran = fku.stream2array(read_st("../data/synthetics_random/SYNTH_RAND_PP_FK_EX.QHD").normalize())
pexran = np.roll(pexran, -35)

pdiffuni = fku.stream2array(read_st("../data/synthetics_uniform/SYNTH_UNIFORM_PP_FK.QHD").normalize())
pdiffuni = np.roll(pdiffuni, -47)
pdiffran = fku.stream2array(read_st("../data/synthetics_random/SYNTH_RAND_PP_FK.QHD").normalize())

uni = fku.stream2array(read_st("../data/synthetics_uniform/SYNTH_UNIFORM_PP.QHD").normalize())
uni = np.roll(uni, -35)
ran = fku.stream2array(read_st("../data/synthetics_random/SYNTH_RAND_PP.QHD").normalize())
ran = np.roll(ran, -35)




plt.ylim([-1,1])
plt.xlim([200,550])
#plt.plot(uni[0],label=("uniform, no filter"))
plt.plot(ran[0],label=("random, no filter"))
#plt.plot(pdiffuni[0],label=("uniform, Pdiff eliminated"))
plt.plot(pdiffran[0],label=("random, Pdiff eliminated"))
#plt.plot(pexuni[0],label=("uniform, PP extractet"))
plt.plot(pexran[0],label=("random, PP extractet"))
plt.legend()
plt.show()


############################################################3
# TEST FOR find_equi_sets
from obspy.geodetics.base import degrees2kilometers

#shift to zero
epidist = epidist - epidist.min()

signal = np.ones(len(epidist))
nout = 1000

#lam = np.linspace(0.1 * degrees2kilometers(1)*1000., (epidist.max()-epidist.min())*degrees2kilometers(1)*1000.)

lam= np.linspace(0.1, (epidist.max()-epidist.min()))

waveno = 1./lam

angular_k = waveno * 2. * np.pi
pgram = sp.signal.lombscargle(epidist, signal, angular_k)
norm_pgram = np.sqrt( 4.*(pgram / signal.shape[0])  )


plt.figure(figsize=(14,4))
plt.plot(lam, norm_pgram)
plt.xlabel(r"Wavelength $/lamda$ (deg)")
deg_ticks, deg_labels = np.arange(10)*degrees2kilometers(1)*1000, ['{:2.1f}'.format for d in np.arange(10)]
plt.xticks(deg_ticks, deg_labels)
plt.tight_layout()

# test with fft
nout = 1000.
T = 3
d = T/nout

x = np.linspace(0,T*2.0*np.pi, nout)
y=np.sin(x)
f = np.fft.fft(y)
freq = np.fft.fftfreq(len(y), d)

# will produce fft and its frequencies



#### PLOTTING ROUTINE FOR REFRESHING ###

fig = plt.figure()

for i in range(1):
    plt.clf()
    plt.plot()
    fig.canvas.draw()

plt.draw()
plt.show()


from bowpy.util.fkutil import create_filter
fs = 22

fig, ax = plt.subplots()
fig.set_size_inches(8,7)
fil1 = np.zeros(30)
fil2 = np.ones(40)
fil3 = np.zeros(30)
ax.plot(np.linspace(-0.5,-0.2,30), fil1, color='b')
ax.plot(np.linspace(-0.2,0.2,40), fil2, color='b')
ax.set_xlim(-0.5,0.5)
ax.set_ylim(-0.1, 1.5)
ax.plot(np.linspace(0.2,0.5,30), fil3, color='b')
ax.plot((-0.2,-0.2),(0,1), color='b')
ax.plot((0.2,0.2),(0,1), color='b')
ax.grid()
ax.set_ylabel('Amplitude', fontsize=fs)
ax.set_xlabel('Normalized Wavenumber', fontsize=fs)
ax.tick_params(axis='both', which='major', labelsize=fs)
fig.savefig('../../../ScieBo/Master/Thesis/Thesis/inputs/methods/images/boxcarfilter.png', dpi=300)

ax.clear()
ax.set_ylabel('Amplitude', fontsize=fs)
ax.set_xlabel('Normalized Wavenumber', fontsize=fs)
fil = create_filter('taper', 50, 20, 1.3)
ax.plot(np.linspace(0,0.5,50), fil, color='b', label='m=1.3')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='b')
fil = create_filter('taper', 50, 20, 2)
ax.plot(np.linspace(0,0.5,50), fil, color='r', label='m=2')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='r')
fil = create_filter('taper', 50, 20, 4)
ax.plot(np.linspace(0,0.5,50), fil, color='g', label='m=4')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='g')
ax.grid()
ax.set_xlim(-0.5,0.5)
ax.set_ylim(-0.1, 1.5)
ax.legend()
fig.savefig('../../../ScieBo/Master/Thesis/Thesis/inputs/methods/images/taperfilter.png', dpi=300)

ax.clear()
ax.set_ylabel('Amplitude', fontsize=fs)
ax.set_xlabel('Normalized Wavenumber', fontsize=fs)
fil = create_filter('butterworth', 50, 20, 2)
ax.plot(np.linspace(0,0.5,50), fil, color='b', label='a=2')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='b')
fil = create_filter('butterworth', 50, 20, 4)
ax.plot(np.linspace(0,0.5,50), fil, color='r', label='a=4')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='r')
fil = create_filter('butterworth', 50, 20, 8)
ax.plot(np.linspace(0,0.5,50), fil, color='g', label='a=8')
ax.plot(np.linspace(-0.5,0,50), fil[::-1], color='g')
ax.grid()
ax.set_xlim(-0.5,0.5)
ax.set_ylim(-0.1, 1.5)
ax.legend()
fig.savefig('../../../ScieBo/Master/Thesis/Thesis/inputs/methods/images/bwfilter.png', dpi=300)


