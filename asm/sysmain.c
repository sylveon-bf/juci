extern int getrandom();
extern void renderframe();
extern void vrammess();

int sysmain() {
    renderframe();
    while(1==1) {
        vrammess();
        renderframe(); 
    }
}