from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt

path = Path(r"logs/[15.2]HC-20250912103013.dat")
data = pd.read_csv(path, sep="\t", comment="#")


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.set_xlabel("time [s]")
ax1.set_ylabel("power [W]")
ax2.set_ylabel("temp [deg.C]")
ax1.set_ylim(top=20, bottom=-1)
ax2.set_ylim(top=1000)
ax1.plot(data["Time[s]"], data["Power[W]"], "C0", label="HC Power")
ax1.plot(data["Time[s]"], data["Power(AMD)[W]"], "C1", label="AMD Power")
ax2.plot(data["Time[s]"], data["Temp(TC)[deg.C]"], "C2", label="Temp")

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper right")

plt.show()
