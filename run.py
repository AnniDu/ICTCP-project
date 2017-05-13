import os
for i in range(1,16):
	s = "./waf --run 'scratch/mydc2-16-2 --packetSize=5000000 --paraServer=%s'"%i
	os.system(s)
