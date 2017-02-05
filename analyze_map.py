import time

import numpy as np
from scipy.ndimage.filters import gaussian_filter

from HaliteBotCode import *
import matplotlib.pyplot as plt
import glob

frame = 300

files = glob.glob("logs/maps/%d.txt" % frame)
print(files)

a = np.loadtxt(files[0])

plt.imshow(a, cmap='hot', interpolation='nearest')
plt.show()