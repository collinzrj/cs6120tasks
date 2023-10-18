int g;
int func_in_loop(int c)
{
    g += c;
    return g;
}
int loop(int a, int b, int c)
{
    int i;
    int ret = 0;
    for (i = a; i < b; i++)
    {
        func_in_loop(c);
    }
    return ret + g;
}