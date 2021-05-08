out.bin: main.o sysmain.o
	x86_64-elf-ld --oformat binary -o out.bin $^ 

main.o: main.asm 
	nasm -felf64 main.asm

sysmain.o: sysmain.c
	x86_64-elf-gcc -Ttext 0x5000 -c sysmain.c -o sysmain.o 