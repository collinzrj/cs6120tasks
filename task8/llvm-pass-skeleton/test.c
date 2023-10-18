#include "stdio.h"
#include "stdlib.h"

typedef struct
{
    int e;
    int f;
} twoInt;

twoInt i2;

int main()
{

    int a = 1;
    int b = 2;
    int c = 3;
    int d = 4;
    int x;

    int i, j;
    j = 2;
    i2.e = a;
    i2.f = b;

    for (j = 0; j < b; j++)
    {
        for (i = 0; i < c; i++)
        {
            a = b * j; /* b*j out of one loop; */
            x = b * j + i2.e;    /* don't move because of load for i2.e */
            if (j == i)
                d = a * c; /* d does not dominate loop exit */
        }
        i2.f = b + c; /* don't move store for i2.f */
    }
    return x;

}