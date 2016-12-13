import matplotlib.pyplot as plt
import numpy as np

# def mode1(Alt,Vs):
#     if VS <= 370:s
#         return 0
#     else:
#         if Alt <= 1750:
#             return "Pull Up"
#         else:


def enveloppePullUp(x):
    if x <= 1750:
        return 0
    elif x <= 3000:
        return(370+(x-1750)*(1000-370)/(3000-1750))
    elif x <= 6225:
        return(1000+(x-3000)*(2075-1000)/(6225-3000))
    else:
        return 2075

def enveloppeSinkRate(x):
    if x <= 1750:
        return 0
    elif x <= 2610:
        return(370+ (x-1750)*(1180-370)/(2610-1750))
    elif x <= 5150:
        return(1180+(x-2610)*(2450-1180)/(5150-2610))
    else:
        return 2450

def enveloppe2(x):
    if x <= 2277:
        return 0
    elif x <= 3000:
        return(220+ (x-2277)*(790-220)/(3000-2277))
    elif x <= 3900:
        return(790+(x-3000)*(1500-790)/(3900-3000))
    elif x <= 6000:
        return(1500+(x-3900)*(1800-1500)/(6000-3900))
    else:
        return 1800


L = np.linspace(1,10000,100)
M = []
for e in L:
    M.append(enveloppe2(e))
plt.plot(L,M)
plt.show()
