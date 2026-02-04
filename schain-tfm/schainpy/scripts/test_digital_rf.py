
import digital_rf as drf
import datetime
path= "/DATA_RM/DRONE2"
do = drf.DigitalRFReader(path)

ch = do.get_channels()
print("ch:",ch)
s,e = do.get_bounds('ch0')
samp_rate = 10e6
startDatetime=datetime.datetime.utcfromtimestamp(s/(samp_rate))
endDatetime=datetime.datetime.utcfromtimestamp(e/(samp_rate))
print('s:',s)
print('e:',e)
print((e-s)/60.0)
print(startDatetime)
print(endDatetime)


print("---------------------")
data = do.read_vector_c81d(s,10*20,'ch0')
print("Data Shape",data.shape)
nProfiles = 10
nHeights  = 20
data = data.reshape(nProfiles, nHeights)
print("SHAPE",data.shape)
print("",data)
