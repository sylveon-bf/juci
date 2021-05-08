[bits 64]
[global _start]
_start:
extern sysmain
	mov dx,0x3df
	in al,dx
	mov ax,3
	mov cx,1
	int 0
	inc r10
	mov ax,8
	mov rbx,0
	mov rcx,0x5000
	mov r9,0x2000
	int 0
	call renderframe
	call sysmain
	hlt

global renderframe
renderframe:
	push ax
	mov ax,7
	int 0
	pop ax
	ret

global getrandom:
getrandom:
	push ax
	push cx
	push dx
	mov dh,0x00
	mov dl,0xff
	mov ax,6
	int 0
	pop ax
	mov ax,cx
	pop cx
	pop dx
	ret

global vrammess
vrammess:
	push ax
	push rbx
	push rcx
	push rdx
	mov ax,6
	mov bx,0x0
.loop:
	inc r10
	cmp rbx,0x4e20
	je .end
	mov r9,r8
	add r9,r10
	mov [rbx],r9
	inc rbx
	jmp .loop
.end:
	inc r8
	pop rdx
	pop rcx
	pop rbx
	pop ax
	ret

example_isr:
	iret

global idtr_asm:
idt_begin:
irq1:
	dw 0xDE
	dq example_isr
	dd 0
	dw 0x0
idt_end:
idt_info:
	dw idt_end - idt_begin - 1
	dq idt_begin