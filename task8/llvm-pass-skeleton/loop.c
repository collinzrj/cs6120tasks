int main() {
    int x = 8;
    int i = 0;
    do {
        i += 1;
        int y = 6;
        x *= (i + y);
    } while (i < 10);

    for (int i = 10; i < 20; i++) {
        x += i;
    }
    return x;
}