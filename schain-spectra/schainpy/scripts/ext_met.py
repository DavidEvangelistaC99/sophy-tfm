import numpy,os,h5py

def isNumber(str):
    try:
        float(str)
        return True
    except:
        return False

def getfirstFilefromPath(path,meta,ext):
      validFilelist = []
      #print("SEARH",path)
      try:
          fileList      = os.listdir(path)
      except:
          print("check path - fileList")
      if len(fileList)<1:
       return None
      # meta    1234 567 8-18 BCDE
      # H,D,PE  YYYY DDD EPOC .ext

      for thisFile in fileList:
          #print("HI",thisFile)
          if meta =="PE":
              try:
                  number= int(thisFile[len(meta)+7:len(meta)+17])
              except:
                   print("There is a file or folder with different format")
          if meta == "D":
              try:
                  number= int(thisFile[8:11])
              except:
                  print("There is a file or folder with different format")

          if not isNumber(str=number):
              continue
          if (os.path.splitext(thisFile)[-1].lower() != ext.lower()):
              continue
          validFilelist.sort()
          validFilelist.append(thisFile)
      if len(validFilelist)>0:
          validFilelist = sorted(validFilelist,key=str.lower)
          return validFilelist
      return None


def getDatavaluefromDirFilename(path,file,value):
    dir_file= path+"/"+file
    fp      = h5py.File(dir_file,'r')
    array    = fp['Data'].get(value)[()]
    fp.close()
    return array
