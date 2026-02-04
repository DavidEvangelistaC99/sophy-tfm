print("LECTURA DE ARCHIVOS DE CONFIGURACION")
class ReadfileWR():
    def __init__(self,filename):
        f = open(filename, "r")
        i=0
        self.dict={'paht_ped':None,'path_adq':None,'path_res':None,'resolution':None,'vel_ped_azi':None,'pos_ped_azi':None,'pos_ped_ele':None,'ipp':None,'n':None,'len_ped':None,\
                't_s_ped':None,'t_f_ped':None,'b_f_adq':None,'t_f_adq':None,'mode':None,'online':None}
        while(True):
            ##print(i)
            linea = f.readline()
            if i==4:
                resolution=float(linea)
                self.dict['resolution']=resolution
            if i==6:
                vel_pedestal_a=float(linea)
                self.dict['vel_ped_azi']=vel_pedestal_a
            if i==8:
                pos_pedestal_a=float(linea)
                self.dict['pos_ped_azi']=pos_pedestal_a
            if i==10:
                pos_pedestal_e=float(linea)
                self.dict['pos_ped_ele']=pos_pedestal_e
            if i==12:
                ipp = float(linea)
                self.dict['ipp']= round(ipp,5)
            if i==14:
                n = float(linea)
                self.dict['n']= n
            if i==16:
                len_pedestal= float(linea)
                self.dict['len_ped']= len_pedestal
            if i==18:
                time_x_sample_ped=float(linea)
                self.dict['t_s_ped']= time_x_sample_ped
            if i==20:
                time_x_file_ped = float(linea)
                self.dict['t_f_ped']= time_x_file_ped
            if i==22:
                bloques_x_file_adq= float(linea)
                self.dict['b_f_adq']=bloques_x_file_adq
            if i==24:
                time_x_file_adq = float(linea)
                self.dict['t_f_adq'] = time_x_file_adq
            if i==26:
                mode= int(linea)
                self.dict['mode'] = mode
            if i==28:
                path_p= str(linea)
                self.dict['path_ped'] = path_p
            if i==30:
                path_a= str(linea)
                self.dict['path_adq'] = path_a
            if i==32:
                online= int(linea)
                self.dict['online'] = online
            if i==34:
                path_r= str(linea)
                self.dict['path_res'] = path_r
            #print(linea)
            if not linea:
                break
            i+=1
        f.close()
    def getDict(self):
        return self.dict


#filename= "/home/developer/Downloads/config_WR.txt"
#dict=  ReadfileWR(filename).getDict()
#print(dict)
