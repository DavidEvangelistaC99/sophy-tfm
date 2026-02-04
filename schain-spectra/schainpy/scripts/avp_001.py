import numpy
a= numpy.array([0,1,2,3,4,5,10,11,12,18,19,20,21,22,23,24,25,26,27,28])
print(a)
list=[]
list2=[]
for i in reversed(range(1,len(a))):
    dif=int(a[i])-int(a[i-1])
    print(i,a[i],dif )
    if dif>1:
        list.append(i-1)
        list2.append(dif-1)
print("result")
print(list)
print(list2)
