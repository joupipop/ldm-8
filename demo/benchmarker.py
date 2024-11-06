import numpy as np
from matplotlib import pyplot as plt

with open("repo/demo/cos.txt", mode='r') as file:
    data = file.read()
    file.close()

# Preprocessing:
data = data.split("\n")[:-3]
y_values_all = [] 
for i in range(len(data)): # compute function for entire float range
    val = data[i]
    if i % 2 == 1:
        y_values_all.append(val.split(" ")[1])
    else:
        pass

x_values = []
y_values = []
for i in range(0 , 17993): # 31743
    x_values.append(float(np.asarray(i, dtype=np.int16).view(np.float16).item()))
    y_values.append(float(np.asarray(y_values_all[i], dtype=np.int16).view(np.float16).item()))

x_values = np.array(x_values)
y_values = np.array(y_values)
ref_y_values = np.cos(x_values)

rel_error = 100*(np.abs((ref_y_values-y_values)/ref_y_values))
abs_error = np.abs(ref_y_values-y_values)

# calculate mean of abs_error function
sum = 0
for i in range(len(x_values)-1):
    sum += (abs_error[i]+abs_error[i+1])*(x_values[i+1]-x_values[i])/2

mean = sum/(x_values[-1]- x_values[0])

font = {'fontname':'a'}
#plt.xscale('log')
plt.xlabel("x")
plt.ylabel("Erreur absolue")
#plt.plot(x_values, ref_y_values, 'bo')
#plt.plot(x_values, y_values, 'ro')
plt.plot(x_values, abs_error, 'k')
#plt.title("Erreur absolue en fonction du log(x)", **font)

plt.show()


