import datetime
from time import sleep
a=datetime.datetime.now()
print str(a)
sleep(1)
b=datetime.datetime.now()
print b-datetime(str(a))
