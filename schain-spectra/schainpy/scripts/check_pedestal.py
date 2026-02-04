# Ing-AlexanderValdez
# Monitoreo de Pedestal

############## IMPORTA LIBRERIAS ###################
import os,numpy,h5py
import sys,time
import matplotlib.pyplot as plt
####################################################
#################################################################
# LA FECHA 21-10-20 CORRESPONDE A LAS PRUEBAS DEL DIA MIERCOLES
# 1:15:51 pm hasta 3:49:32 pm
#################################################################

#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211012-082745'
#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211020-131248'
#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211110-171003'
#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211111-173856'
#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211123-143826'
#path_ped = "/DATA_RM/TEST_PEDESTAL/P20220217-172216"
#path_ped = "/DATA_RM/TEST_PEDESTAL/P20220322-163824"
#path_ped = '/DATA_RM/TEST_PEDESTAL/P20211111-173409'


#--------------------------------

path_ped= "/DATA_RM/TEST_PEDESTAL/P20220401-172744"

# Metodo para verificar numero
def isNumber(str):
    try:
        float(str)
        return True
    except:
        return False
# Metodo para extraer el arreglo
def getDatavaluefromDirFilename(path,file,value):
    dir_file= path+"/"+file
    fp      = h5py.File(dir_file,'r')
    array    = fp['Data'].get(value)[()]
    fp.close()
    return array

# LISTA COMPLETA DE ARCHIVOS HDF5 Pedestal
LIST= sorted(os.listdir(path_ped))
m=len(LIST)
print("TOTAL DE ARCHIVOS DE PEDESTAL:",m)
# Contadores temporales
k=  0
l=  0
t=  0
# Marca de tiempo temporal
time_        = numpy.zeros([m])
# creacion de
for i in range(m):
    print("order:",i)
    tmp_azi_pos = getDatavaluefromDirFilename(path=path_ped,file=LIST[i],value="azi_pos")
    tmp_ele_pos = getDatavaluefromDirFilename(path=path_ped,file=LIST[i],value="ele_pos")
    tmp_azi_vel = getDatavaluefromDirFilename(path=path_ped,file=LIST[i],value="azi_vel")
    tmp_ele_vel = getDatavaluefromDirFilename(path=path_ped,file=LIST[i],value="ele_vel")# nuevo :D

    time_[i]    = getDatavaluefromDirFilename(path=path_ped,file=LIST[i],value="utc")

    k=k +tmp_azi_pos.shape[0]
    l=l +tmp_ele_pos.shape[0]
    t=t +tmp_azi_vel.shape[0]

print("TOTAL DE MUESTRAS, ARCHIVOS X100:",k)
time.sleep(5)
######CREACION DE ARREGLOS CANTIDAD DE VALORES POR MUESTRA#################
azi_pos     = numpy.zeros([k])
ele_pos     = numpy.zeros([l])
time_azi_pos= numpy.zeros([k])
# Contadores temporales
p=0
r=0
z=0
# VARIABLES TMP para almacenar azimuth, elevacion y tiempo

#for filename in sorted(os.listdir(path_ped)):
# CONDICION POR LEER EN TIEMPO REAL NO OFFLINE

for filename in LIST:
    #tmp_azi_pos   = getDatavaluefromDirFilename(path=path_ped,file=filename,value="azi_pos")
    tmp_ele_pos   = getDatavaluefromDirFilename(path=path_ped,file=filename,value="ele_pos")
    tmp_azi_pos   = getDatavaluefromDirFilename(path=path_ped,file=filename,value="ele_vel")
    #tmp_ele_pos   = getDatavaluefromDirFilename(path=path_ped,file=filename,value="azi_vel")
    # CONDICION POR LEER EN TIEMPO REAL NO OFFLINE

    if z==(m-1):
        tmp_azi_time=numpy.arange(time_[z],time_[z]+1,1/(tmp_azi_pos.shape[0]))
    else:
        tmp_azi_time=numpy.arange(time_[z],time_[z+1],(time_[z+1]-time_[z])/(tmp_azi_pos.shape[0]))

    print(filename,time_[z])
    print(z,tmp_azi_pos.shape[0])

    i=0
    for i in range(tmp_azi_pos.shape[0]):
        index=p+i
        azi_pos[index]=tmp_azi_pos[i]
        time_azi_pos[index]=tmp_azi_time[i]
    p=p+tmp_azi_pos.shape[0]
    i=0
    for i in range(tmp_ele_pos.shape[0]):
        index=r+i
        ele_pos[index]=tmp_ele_pos[i]
    r=r+tmp_ele_pos.shape[0]


    z+=1


######## GRAFIQUEMOS Y VEAMOS LOS DATOS DEL Pedestal
fig, ax = plt.subplots(figsize=(16,8))
print(time_azi_pos.shape)
print(azi_pos.shape)
t=numpy.arange(time_azi_pos.shape[0])*0.01/(60.0)
plt.plot(t,azi_pos,label='AZIMUTH_POS',color='blue')

# AQUI ESTOY ADICIONANDO LA POSICION EN elevaciont=numpy.arange(len(ele_pos))*0.01/60.0
t=numpy.arange(len(ele_pos))*0.01/60.0
plt.plot(t,ele_pos,label='ELEVATION_POS',color='red')#*10

ax.set_xlim(0, 4)
ax.set_ylim(-5, 360)
plt.ylabel("Azimuth Position")
plt.xlabel("Muestra")
plt.title('Azimuth Position vs Muestra ', fontsize=20)
axes = plt.gca()
axes.yaxis.grid()
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.show()
