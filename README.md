# Juci

a x86-64 fantasy computer.

|Region Start|Region Size|Description                           |
|------------|-----------|--------------------------------------|
|0x0         |20K        |Video Memory (raw paletted image)     |
|0x5000      |2MB        |Program Memory                        |
|0x300000    |267MB      |User Memory                           |

Interrupt 0 is the Juci interrupt.

|RAX    |Purpose                                             |
|-------|----------------------------------------------------|
|1      |Print null terminated string from register RBX > tty|
|2      |Print character in register CX                      |
|3      |Set video mode from register CX                     |
|4      |Get memory total (outdated)                         |
|5      |FUN! Set location of where GraphicsThread loads VRAM|
|6      |Put random number in register CX                    |
|7      |DOESNT WORK! "Buffer display"                       |
|8      |Fast memcpy, dest is RBX, src is RCX, srclen is R9  |
|9      |Print the words debug into stdio                    |