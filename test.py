import pyttsx3
e = pyttsx3.init()
for v in e.getProperty('voices'):
    print(v.id, getattr(v,'name',None))
