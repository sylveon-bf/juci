from unicorn import *
from unicorn.x86_const import *
from PIL import Image, ImageTk, ImagePalette
import numpy as np
import tkinter as tk
import random
import struct
import threading
import getch

fcode = b""

file = open("asm/out.bin", "rb")
byte = file.read(1)

while byte:
	print(byte)
	fcode += byte
	byte = file.read(1)

print(fcode)

ADDRESS_BEGIN = 0x5000
ADDRESS_END = 2*1024*1024
VIDEOMODE = 0
INTERRUPT_DESCRIPTOR = 0x0
MEMORYCOUNT = 624*1024
VRAM_START = 0x0 # displayed vram takes 20000B, leaving 480B left over
VRAM_WIDTH = 200
VRAM_HEIGHT = 100
VRAM_COUNT = VRAM_WIDTH*VRAM_HEIGHT # resolution
DISPLAY = False
hWnd = tk.Tk()

class GraphicsThread(threading.Thread):
	def __init__(self, tk_root, proc):
		self.root = tk_root
		self.proc = proc
		self.canvas = tk.Canvas(tk_root, width = 1600, height = 800) 
		self.canvas.pack()  
		self.canvasimg = self.canvas.create_image(0,0)
		threading.Thread.__init__(self)
		self.start()
	def upd_gfx(self):
		if DISPLAY==1:
			vram = self.proc.mem_read(VRAM_START,VRAM_WIDTH*VRAM_HEIGHT)
			na = np.array(vram)
			pal = Image.open("palette.png")
			palc = pal.convert(mode="P",palette=Image.ADAPTIVE)
			im = Image.fromarray(na.reshape(VRAM_HEIGHT,VRAM_WIDTH),"P")
			im.putpalette(palc.getpalette())
			imz = im.resize((1600,800))
			self.image = ImageTk.PhotoImage(imz)
			self.canvas.itemconfig(self.canvasimg, image = self.image)
		self.canvas.after(16,self.upd_gfx)
	def run(self):
		self.canvas.after(16,self.upd_gfx)

class ProcessorThread(threading.Thread):
	def __init__(self, proc):
		self.proc = proc
		threading.Thread.__init__(self)
		self.start()
	def run(self):
		self.proc.emu_start(ADDRESS_BEGIN,ADDRESS_END)

def hook_in(uc, port, size, user_data):
	eip = uc.reg_read(UC_X86_REG_RIP)
	print("--- reading from port 0x%x, size: %u, address: 0x%x" %(port, size, eip))
	if port == 0x3df:
		print("machine stalling for input")
		return getch.getch()
	return 0

def hook_out(uc, port, size, value, user_data):
	eip = uc.reg_read(UC_X86_REG_RIP)
	print("--- writing to port 0x%x, size: %u, value: 0x%x, address: 0x%x" %(port, size, value, eip))

def hook_code(mu, address, size, user_data):
	if VIDEOMODE == 1:	
		global DISPLAY
		if DISPLAY == True:
			pass

def hook_intr(mu,intno,user_data):
	# system reserved interrupt
	if intno == 0:
		reg_ax = mu.reg_read(UC_X86_REG_RAX)
		# <TTYMODE> print string thats null terminated
		if reg_ax == 1:
			addrToRead = mu.reg_read(UC_X86_REG_RBX)
			while mu.mem_read(addrToRead,1)[0] != 0:
				print("%c" % mu.mem_read(addrToRead,1)[0],end='')
				addrToRead += 1
		# <TTYMODE> print character from cx
		elif reg_ax == 2:
			print("%c" % mu.reg_read(UC_X86_REG_CX), end='')
		# swap video mode
		elif reg_ax == 3:
			global VIDEOMODE
			VIDEOMODE = mu.reg_read(UC_X86_REG_CX)
			# tty
			if VIDEOMODE == 0:
				pass
			# vga
			elif VIDEOMODE == 1:
				pass
			print("VIDEO MODE SET TO %x" % VIDEOMODE)
		# get current memory total
		elif reg_ax == 4:
			mu.reg_write(UC_X86_REG_EBX,MEMORYCOUNT)
		# FUN! set vram location
		elif reg_ax == 5:
			global VRAM_START
			VRAM_START = mu.reg_read(UC_X86_REG_EBX)
		# get random number
		elif reg_ax == 6:
			mu.reg_write(UC_X86_REG_CX,random.randint(mu.reg_read(UC_X86_REG_DH),mu.reg_read(UC_X86_REG_DL)))
		# buffer display
		elif reg_ax == 7:
			global DISPLAY
			DISPLAY = True
		# fast memcpy
		elif reg_ax == 8:
			dest = mu.reg_read(UC_X86_REG_RBX)
			src = mu.reg_read(UC_X86_REG_RCX)
			srclen = mu.reg_read(UC_X86_REG_R9)

			cpd = mu.mem_read(src,srclen)
			mu.mem_write(dest,bytes(cpd))
		# print debug
		elif reg_ax == 9:
			print("debug")
	else:
		idtr = mu.reg_read(UC_X86_REG_IDTR)
		infoD = mu.mem_read(idtr)
		info = struct.unpack("IQ",infoD)
		idtP = info[1] 
		irq_size = 0
		irqdata = mu.mem_read(idtP+(irq_size*(intno-1)),irq_size)
		# IRQ in Juci Machine
		# char - Magic (should be 0xDE)
		# long long - Pointer to code
		# int - Context (0 is global, 1 is kernel)
		irq = struct.unpack("cQIc",irqdata)
		if irq[0] == 0xDE and irq[3] == 0x00:
			jmpc = irq[1]
			ip = mu.reg_read(UC_X86_REG_RIP)
			mu.emu_stop()
			mu.emu_start(jmpc,0xFFFFFFFFFFFFFFFF)
			mu.emu_start(ip,  0xFFFFFFFFFFFFFFFF)
		else:
			print("irq fault")
			mu.emu_stop()

def main():
	try:
		mu = Uc(UC_ARCH_X86, UC_MODE_64)
		print("alloc program mem (2MB)")
		mu.mem_map(ADDRESS_BEGIN,2*1024*1024, UC_PROT_EXEC | UC_PROT_READ | UC_PROT_WRITE)
		print("alloc video mem (20K)")
		mu.mem_map(0,20*1024, UC_PROT_READ | UC_PROT_WRITE)
		print("alloc user mem (267MB)")
		mu.mem_map(3*1024*1024, 255*1024*1024, UC_PROT_EXEC | UC_PROT_WRITE | UC_PROT_READ)
		mu.reg_write(UC_X86_REG_RSP,9*1024*1024)
		mu.mem_write(ADDRESS_BEGIN,fcode)
		mu.mem_write(0xdada,b"Running on Juciv1\x0a\x00")
		mu.reg_write(UC_X86_REG_BX,0xdada)
		mu.hook_add(UC_HOOK_INTR,hook_intr)
		mu.hook_add(UC_HOOK_CODE,hook_code)
		mu.hook_add(UC_HOOK_INSN, hook_in, None, 1, 0, UC_X86_INS_IN)
		mu.hook_add(UC_HOOK_INSN, hook_out, None, 1, 0, UC_X86_INS_OUT)
		
		proc = ProcessorThread(mu)
		gfx = GraphicsThread(hWnd,mu)
		hWnd.mainloop()
		gfx.join()
		mu.emu_stop()
	except UcError as e:
		print("ERROR:%s" % e)

main()

