import base64
import marshal
import zlib
import sys
import py_compile
import re
from shutil import move
from os import (system,rename,remove,path,getcwd)
from time import sleep

CLOSE = "\033[m"
CIAN = "\033[01;36m"
GRAY = "\033[01;90m"
WHITE = "\033[01;97m"


class Encode:
	def __init__(self,script,n):
		self.script = script
		self.n = n
	
	def B85(self):
		content = open(self.script,'r', encoding='utf-8').read()
		for i in range(1,self.n+1):
			print("\rENCODING:%d%%"%(i/self.n * 100),end="")
			code = compile(content, "_", 'exec')
			data = marshal.dumps(code)
			enc = base64.b85encode(zlib.compress(data)[::-1]).decode('utf-8')
			content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b85decode('%s')[::-1]));exec(_(_))"%enc
		
		with open("%sobfB85.py"%self.script.replace(".py",""),"w") as file:
			file.write(content)

		print("\r\033[KDONE!")
	
	def B64(self):
		content = open(self.script,'r', encoding='utf-8').read()
		for i in range(1,self.n+1):
			print("\rENCODING:%d%%"%(i/self.n * 100),end="")
			code = compile(content, "_", 'exec')
			data = marshal.dumps(code)
			enc = base64.b64encode(zlib.compress(data)[::-1]).decode()
			content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b64decode('%s')[::-1]));exec(_(_))"%enc
		
		with open("%sobfB64.py"%self.script.replace(".py",""),"w") as file:
			file.write(content)

		print("\r\033[KDONE!")
	
	def B32(self):
		content = open(self.script,'r', encoding='utf-8').read()
		for i in range(1,self.n+1):
			print("\rENCODING:%d%%"%(i/self.n * 100),end="")
			code = compile(content, "_", 'exec')
			data = marshal.dumps(code)
			enc = base64.b32encode(zlib.compress(data)[::-1]).decode()
			content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b32decode('%s')[::-1]));exec(_(_))"%enc

		with open("%sobfB32.py"%self.script.replace(".py",""),"w") as file:
			file.write(content)

		print("\r\033[KDONE!")
	
	def B16(self):
		content = open(self.script,'r', encoding='utf-8').read()
		for i in range(1,self.n+1):
			print("\rENCODING:%d%%"%(i/self.n * 100),end="")
			code = compile(content, "_", 'exec')
			data = marshal.dumps(code)
			enc = base64.b16encode(zlib.compress(data)[::-1]).decode()
			content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b16decode('%s')[::-1]));exec(_(_))"%enc
		
		with open("%sobfB16.py"%self.script.replace(".py",""),"w") as file:
			file.write(content)

		print("\r\033[KDONE!")
	
	def ALL(self):
		content = open(self.script,'r', encoding='utf-8').read()
		for i in range(1,self.n+1):
			print("\rENCODING:%d%%"%(i/self.n * 100),end="")
			code = compile(content, "_", 'exec')
			data = marshal.dumps(code)
			enc = base64.b85encode(base64.b64encode(base64.b32encode(base64.b16encode(zlib.compress(data)[::-1])[::-1])[::-1])[::-1]).decode()
			content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b16decode(__import__('base64').b32decode(__import__('base64').b64decode(__import__('base64').b85decode('%s')[::-1])[::-1])[::-1])[::-1]));exec(_(_))"%enc

		with open("%sobfALL.py"%self.script.replace(".py",""),"w") as file:
			file.write(content)
		
		print("\r\033[KDONE!")


def comp(name):
	file = open(name,'r', encoding='utf-8').read()
	to_char = [ord(i) for i in file]
	remove(name)
	open(name,'w').write("_ = lambda __:\"\".join(chr(___) for ___ in __)\nexec(_(%s))"%to_char)
	print("Compiling... %s"%name)
	py_compile.compile(name)
	remove(name)
	reg = re.search(r"([^.*?]+).py",name)
	filecomp = "%s.cpython-%s%s.pyc"%(reg.group(1),sys.version_info[0],sys.version_info[1])
	move("__pycache__/%s"%filecomp,getcwd())
	rename(filecomp,name)
	print("\r\033[KDONE!")

def help():
	print("%sARGUMENTS:%s"%(WHITE,GRAY))
	print("   -B85   Encode Base85")
	print("   -B64   Encode Base64")
	print("   -B32   Encode Base32")
	print("   -ALL   Encode Base85,64,32,16")
	print("   -C     Compile code with ord() function")
	print("   -V     Version")
	print("   -h     Help")
	print()
	print("%sUSAGE:%s"%(WHITE,GRAY))
	print("   obfuscator.py -B64 script.py 120")
	print("   obfuscator.py -C script.py")
	print()
	print("%sVERSION: 2.0.0%s"%(WHITE,CLOSE))
	print("%sCopyright (c) 2023-2025 %s@westsidedev%s"%(WHITE,CIAN,CLOSE))

if __name__ == "__main__":
	try:
		match sys.argv[1]:
			case "-h":
				help()
			case "-B85":
				Encode(sys.argv[2],int(sys.argv[3])).B85()
			case "-B64":
				Encode(sys.argv[2],int(sys.argv[3])).B64()
			case "-B32":
				Encode(sys.argv[2],int(sys.argv[3])).B32()
			case "-B16":
				Encode(sys.argv[2],int(sys.argv[3])).B16()
			case "-C":
				comp(sys.argv[2])
			case "-ALL":
				Encode(sys.argv[2],int(sys.argv[3])).ALL()
			case _:
				help()
	except IndexError:
		help()