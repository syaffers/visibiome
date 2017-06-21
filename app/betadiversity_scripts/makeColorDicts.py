import MySQLdb
from matplotlib import colors as mcolors
import numpy as np

conn = MySQLdb.connect(host='localhost', db='EarthMicroBiome', user='root', passwd='qiime')
curs = conn.cursor()
try:
    colors = np.array(mcolors.CSS4_COLORS.values())
    colorDict = {}

    for rank in "phylum order class family genus species".split():
        np.random.shuffle(colors)
        curs.execute('SELECT DISTINCT `%s` FROM OTUS_unified' %rank)
        clades = curs.fetchall()
        colorDict[rank] = dict([(clades[i][0], colors[i%len(colors)]) for i in range(len(clades))])
finally:
    conn.close()
