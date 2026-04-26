import numpy

def weightfit(w,year,doy,index,ht,beam):
  if len(w) <= 0 : return w

  if year == 2020 and doy == 265 :
   if beam == 0 :
    if index >= 120 and index <= 183 and ht >=30:  w[0,100:120] =0
 
   if beam == 1 :
    if index >= 132 and index <= 180 and ht ==11:
                       w[0,90:120] = 0
    if index >= 120 and index <= 183 and ht >=30:
                       w[0,100:120] = 0
    if index >= 176 and index <= 176 and ht ==20: w[0,60:100] = 0.0
    if index >= 177 and index <= 177 and ht >=24 and ht <=29: w[0,70:80] = 0.0
    if index >= 177 and index <= 177 and ht >=30: w[0,70:80] = 0.0
    if index >= 178 and index <= 178 and ht>=18: w[0,100:120] = 0.0
    print('entra a la funcion w')
   # If index eq 96 then stop  ;stop 96

  return w

def Vrfit(p0,year,doy,index,h,beam):
    if year == 2020 and doy == 265 :
     if beam == 0 :
       if index == 177 and h==30 : p0[3]=20
       if index == 184 and h>=27 : p0[3]=30
       if index == 186 and h>=11 : p0[3]=30
       if index == 190 and h==27 : p0[3]=27  
       if index == 191 and h==26 : p0[3]=28
       if index == 191 and h>=35 : p0[3]=24
       if index == 131 and h==29 : p0[3]=24
       if index == 138 and h==11 : p0[3]=30
       if index == 138 and h==14 : p0[3]=30
       if index == 139 and h>=34 and h<=36 : p0[3]=20                
       if index == 142 and h>=34 : p0[3]=35         
       if index == 155 and h>=27 and h<=40: p0[3]=36                   
       if index == 167 and h>=13 and h<=13: p0[3]=33               
       if index == 168 and h>=13 and h<=13: p0[3]=37                
       if index == 172 and h>=13 and h<=13: p0[3]=37  
       if index == 173 and h>=28 and h<=29: p0[3]=37
       print('entra a la funcion vr')
 
     if beam == 1 :
       if index == 177 and h>=31 and h<=32: p0[3]=30
       if index == 179 and h==27 : p0[3]=38
       if index == 180 and h==23 : p0[3]=33
       if index == 180 and h==26 : p0[3]=30
       if index == 180 and h==29 : p0[3]=35
       if index == 184 and h>=23 : p0[3]=30
       if index == 185 and h==11 : p0[3]=20
       if index == 185 and h>=29 : p0[3]=30
       if index == 186 and h>=11 : p0[3]=30
       if index == 190 and h==11 : p0[3]=28
       if index == 191 and h>=33 : p0[3]=20
       if index == 131 and h==11 : p0[3]=17
       if index == 131 and h>=29 and h<=38 : p0[3]=18
       if index == 138 and h>=31 : p0[3]=15
       if index == 139 and h>=11 and h<=16 : p0[3]=25
       if index == 140 and h==33 : p0[3]=26
       if index == 142 and h==34 : p0[3]=20
       if index == 149 and h>=28 and h<=32: p0[3]=28
       if index == 163 and h>=11 and h<=11: p0[3]=30
       if index == 167 and h>=11 and h<=16: p0[3]=33
       if index == 167 and h>=34 and h<=40: p0[3]=36
       if index == 169 and h>=26 and h<=49: p0[3]=33
       if index == 172 and h>=28 and h<=28: p0[3]=37
       if index == 173 and h>=20 and h<=38: p0[3]=37
       if index == 174 and h>=25 and h<=25: p0[3]=34
       if index == 175 and h>=27 and h<=35: p0[3]=30
       #if h == 11: print('entra ',p0[3])
    return p0
