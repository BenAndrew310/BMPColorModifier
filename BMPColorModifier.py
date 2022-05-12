"""
Modify the color of bitmap images 
Currently support images with color depth of:
	- 4 bpp
	- 24 bpp
---------------------------------------------
author: Benchley André
"""

import os,sys

class BMPByteTools:
	def byte2bits(self, byte:str) -> str :  # turn a byte written in hex into a 8-bit bin number 
		_dec = eval(byte)
		_bin = bin(_dec)
		_bin = _bin[:2] + (8-len(_bin[2:]))*'0' + _bin[2:]  # extend to 8 bits
		
		return _bin

	def bits2byte(self, bits:str) -> str : # turn a 8-bit bin number into a byte in hex
		_dec = eval(bits)
		_hex = hex(_dec)

		_hex = _hex[:2] + '0'+_hex[-1] if len(_hex) == 3 else _hex

		return _hex

	def to_High(self, bits, *indices):  # turn bit at a certain index to 1
		start = 2
		if '0b' not in bits:
			start = 0
		for index in indices:
			bits = "".join((bits[:start+index], "1", bits[start+index+1:]))
		
		bits = "0b" + bits if "0b" not in bits else bits
		
		return bits

	def to_Low(self, bits, *indices):   # turn bit at a certain index to 0
		start = 2
		if '0b' not in bits:
			start = 0
		for index in indices:
			bits = "".join((bits[:start+index], "0", bits[start+index+1:]))
		
		bits = "0b" + bits if "0b" not in bits else bits
		
		return bits


class BMPColorModifier(BMPByteTools):
	supported_bpp=[4, 24]

	OPERATIONS={
		4:["filtering", "darkening"],
		8:["filtering", "darkening"],
		16:["filtering"],
		24:["filtering", "darkening", "put in gray", "all white", "all black"],
		32:[]
	}

	def __init__(self, file_dir="", verbose=False):
		"""
		:param `file_dir`: Directory of the source file
		:param `verbose` : If True, outputs info messages to the console
		"""
		self.file_dir = file_dir  
		self.verbose  = verbose

	def __dstDir(self):  # private method returning a destination directory if (1) no destination directory was specified (2) destination directory is erroneous
		name, ext = os.path.splitext(self.file_dir)
		count = 1
		new_dir = name + f"_{count}" + ext
		while os.path.exists(new_dir):
			count += 1
			new_dir = name + f"_{count}" + ext

		return new_dir

	def __show_feedback(self, text, type_="info"): # output info messages to the console
		if self.verbose:
			print(f"[{type_}] " + text)

	def get_size_offset(self, data):  # -> size of the bitmap, offset address of the pixel array 
		return data[2], data[10]

	def get_bpp(self, data): # get color depth of the bitmap
		return data[28]

	def get_width_height(self, data):
		return data[18], data[22]

	def setFile(self, file_dir):
		self.file_dir = file_dir
		return self.file_dir

	def read(self):
		try:
			filer = open(self.file_dir, "rb")
			data = bytearray(filer.read())
			filer.close()
			size, offset = self.get_size_offset(data)
			self.__show_feedback(f"The size of this BMP file is {size}")
			return data
		except FileNotFoundError as e:
			sys.stderr.write("[ERROR] File not found\n")
			sys.stderr.flush()
			exit(e.errno)
		except IOError as e:
			sys.stderr.write(f"[ERROR] Could not open file {self.file_dir}: "+\
				os.strerr(e.errno) + "\n")
			sys.stderr.flush()
			exit(e.errno)

	def write(self, data, dst=None):
		if dst is None:
			write_dir = self.__dstDir()
		elif not dst.endswith(".bmp"):
			self.__show_feedback("Destination file does not correspond to a BMP file"+\
				"\nNew destination file will be created", "warning")
			write_dir = self.__dstDir()
		else:
			write_dir = dst

		try:
			filew = open(write_dir, "wb")
			filew.write(data)
			filew.close()
			self.__show_feedback(f"Data has been written in {write_dir}")
		except Exception as e:
			print(e)
		except IOError as e:
			sys.stderr.write(os.strerr(e.errno) + "\n")
			sys.stderr.flush()
			exit(e.errno)

	def modify(self, data, operation="filter", color="blue"):
		bpp = self.get_bpp(data)
		self.__show_feedback(f"Bitmap color depth: {bpp} bpp")

		if bpp==24:
			return self.__modify_24bpp(data, operation, color)
		elif bpp==4:
			return self.__modify_4bpp(data, operation, color)
		elif bpp==8:
			return self.__modify_8bpp(data, operation, color)  # is erroneous
		elif bpp==16:
			return self.__modify_16bpp(data, operation, color) # is erroneous
		elif bpp==32:
			pass
		self.__show_feedback("Unsupported color depth", "warning")
		return data

	def __modify_4bpp(self, data, operation, color): # EGA
		colors=["blue", "green", "red", "gray"]
		if color not in colors:
			self.__show_feedback("Color must be either blue, green, red or gray","warning")
			return data

		size, offset = self.get_size_offset(data)
		color_index = colors.index(color)

		if operation == "filter":
			for i in range(offset, len(data[offset:])):
				byte = hex(data[i])
				_bin = self.byte2bits(byte)
				_bin = self.to_Low(_bin, color_index, color_index+4)
				data[i] = eval(_bin)

		elif operation == "darken":
			for i in range(offset, len(data[offset:])):
				byte = hex(data[i])
				_bin = self.byte2bits(byte)
				_bin = self.to_High(_bin, color_index, color_index+4)
				data[i] = eval(_bin)
		return data

	def __modify_8bpp(self, data, operation, color):  # VGA
		colors=["red", "blue", "green", "gray"]
		if color not in colors:
			self.__show_feedback("Color must be either blue, green, red or gray","warning")
			return data

		size, offset = self.get_size_offset(data)
		color_index = colors.index(color)

		if operation == "filter":
			for i in range(offset, len(data[offset:])):
				byte = hex(data[i])
				_bin = self.byte2bits(byte)
				_bin = self.to_Low(_bin,2*color_index,2*color_index+1)
				data[i] = eval(_bin)

		elif operation == "darken":
			for i in range(offset, len(data[offset:])):
				byte = hex(data[i])
				_bin = self.byte2bits(byte)
				_bin = self.to_High(_bin, 2*color_index, 2*color_index+1)
				data[i] = eval(_bin)

		return data

	def __modify_16bpp(self, data, operation, color): # XGA, High color
		colors=["gray", "red", "green", "blue"]
		if color not in colors:
			self.__show_feedback("Color must be either blue, green, red or gray", "warning")
			return data

		size, offset = self.get_size_offset(data)
		color_index = colors.index(color)
		start_index = 0 if color_index in [0, 1] else 1
		jump = 2

		if operation == "filter":
			for i in range(offset+start_index, len(data[offset:]), jump):
				byte = hex(data[i])
				_bin = self.byte2bits(byte)
				if color == "gray" or color == "green":
					_bin = self.to_Low(_bin, 0, 1, 2, 3)
				elif color == "red" or color == "blue":
					_bin = self.to_Low(_bin, 4, 5, 6, 7)
				data[i] = eval(_bin)

			return data

	def __modify_24bpp(self, data, operation, color): # SVGA, True color
		colors=["blue", "green", "red"]
		if color not in colors:
			self.__show_feedback("Color must be either blue, green or red", "warning")
			return data

		size, offset = self.get_size_offset(data)

		value = 0 # new value for the selected byte
		jump = 3  # relative offset from one byte to the next in the pixel array

		start = colors.index(color) # either 0, 1 or 2 => blue, green or red

		if operation == "filter":
			value = 0
			self.__show_feedback(f"Filtering the {color} color from the bitmap")

		elif operation == "darken":
			self.__show_feedback(f"Making the {color} color look darker in the bitmap")
			for i in range(offset+start, len(data[offset:]), jump):
				data[i+1] = data[i+2] = 0
			return data
		
		elif operation == "gray":
			self.__show_feedback(f"Putting the bitmap in gray")
			for i in range(offset, len(data[offset:]), jump):
				data[i] = data[i+1] = data[i+2] = sum(data[i:i+3])//3
			return data

		elif operation == "white":
			self.__show_feedback(f"Turning everything to white")
			value = 255
			jump = 1

		elif operation=="black":
			self.__show_feedback(f"Turning everything to black")
			value = 0
			jump = 1

		for i in range(offset+start, len(data[offset:]), jump):
			data[i] = value
		
		return data

	def __modify_32bpp(self, data, operation, color):
		pass


operations={
	"1":"filter",
	"2":"darken",
	"3":"gray",
	"4":"white",
	"5":"black"
}

def show_operations(bpp):
	print("\nWhich operation would you like to perform (Enter the number):")
	for index, op in enumerate(BMPColorModifier.OPERATIONS[bpp]):
		print(f"({index+1}) {op}")
	print()
	return len(BMPColorModifier.OPERATIONS[bpp])

def clear_console():
	if os.name == "nt":
		os.system("cls")
	else:
		os.system("clear")

if __name__=="__main__":
	try:
		bcm = BMPColorModifier()
		bcm.verbose = True

		while True:
			src = input("BMP source directory: ")
			bcm.setFile(src)
			data = bcm.read()

			bpp = bcm.get_bpp(data)

			if bpp not in BMPColorModifier.supported_bpp:
				print("[info] such image depth is not supported")
				print("[info] supported image depth: ", end="")
				for BPP in BMPColorModifier.supported_bpp:
					print(BPP, end=" ")
				print()
				os.system("pause")
				clear_console()
				continue

			dst=input("\nBMP destination directory (press ENTER to skip): ")

			number_of_operations = show_operations(bpp)

			op = input("operation: ")
			while not op.isdigit() or int(op) < 1 or int(op) > number_of_operations:
				print("[ERROR] Please provide the number corresponding to the operation")
				op = input("operation: ")

			color = "blue"
			if op in ["1", "2"]:
				color = input("Please specify a color\nblue/green/red: ")

			print()
			data = bcm.modify(data, operations[op], color)
			bcm.write(data, dst)
			print()
			os.system("pause")
			clear_console()

	except Exception as e:
		sys.stderr.write(e + "\n")
		sys.stderr.flush()

	finally:
		print("\nGoodbye...")
		os.system("pause")
