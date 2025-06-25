// runtime.c
#include <stdio.h>

void print(int x) {
    printf("%d\n", x);  // Must include "\n"
}

int read() {
    int x;
    scanf("%d", &x);
    return x;
}