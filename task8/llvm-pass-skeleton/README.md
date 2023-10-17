# llvm-pass-skeleton

A completely useless LLVM pass.
It's for LLVM 17.

Build:

    $ cd llvm-pass-skeleton
    $ mkdir build
    $ cd build
    $ cmake ..
    $ make
    $ cd ..

Run:

    $ /opt/homebrew/opt/llvm/bin/clang -fpass-plugin=`ls build/skeleton/SkeletonPass.*` loop.c

/opt/homebrew/opt/llvm/bin/clang -fpass-plugin=`ls build/skeleton/SkeletonPass.*` tsc.c

Try to test on tsc.c, it seems to be interesting
