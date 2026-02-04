# Importra librerías
import os
#import imageio
import imageio.v2 as imageio
# Ubicación de la base de datos
'''
#path = '/home/soporte/Downloads/plots_C0/S/6/6_evento0/'
path=  '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_PL_R60.0km/V_PPI_EL_8.0CH0/'
path=  '/home/soporte/Documents/EVENTO/HYO_PM@2022-05-31T12-00-17/plotsC0_PL_R60.0km_removeDC/V_PPI_EL_8.0CH0/'
path=  '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R15.0km_removeDC/Z_PPI_EL_2.0CH0/'
path=  '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R15.0km/Z_PPI_EL_8.0CH0/'
path= '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T18-00-00/W_E.2CH0/'
'''
#--------------------------------------------------------------------------------------------------------
#pulse pair
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_PL_R28.0km/Z_PPI_EL_2.0CH0/'
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_PL_R28.0km/W_PPI_WE_L8.0CH0/'
#---------------------------------------------------------------------------------------------------------
#pulse pair REMOVEDC
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_PL_R28.0km_removeDC/V_PPI_EL_2.0CH0/'
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_PL_R28.0km_removeDC/W_PPI_WE_L8.0CH0/'
#----------------------------------------------------------------------------------------------------------
#Spectro
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R28.0km/V_PPI_EL_2.0CH0/'
path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R28.0km/W_PPI_WE_L8.0CH0/'

#---------------------------------------------------------------------------------------------------------
#Spectro REMOVEDC
path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R28.0km_removeDC/V_PPI_EL_8.0CH0/'
#path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/plotsC0_FD_PL_R28.0km_removeDC/W_PPI_WE_L2.0CH0/'



archivos = sorted(os.listdir(path))
img_array = []

#Leer todos los archivos formato imagen desde path
for x in range(0, len(archivos)):
    nomArchivo = archivos[x]
    dirArchivo = path + str(nomArchivo)

    #Asignar a variable leer_imagen, el nombre de cada imagen
    leer_imagen = imageio.imread(dirArchivo)

    # añadir imágenes al arreglo img_array
    img_array.append(leer_imagen)

#Guardar Gif
#imageio.mimwrite('/home/soporte/Documents/giff_28km/evento_PL_PP_8_28KM_W', img_array, 'GIF', duration=0.5)
#imageio.mimwrite('/home/soporte/Documents/giff_28km/evento_PL_PP_8_28KM_W_reDC', img_array, 'GIF', duration=0.5)
imageio.mimwrite('/home/soporte/Documents/giff_28kmFD/evento_PL_FD_8_28KM_V_reDC', img_array, 'GIF', duration=0.5)
