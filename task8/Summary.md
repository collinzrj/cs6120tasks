## Summary
LICM implementation under lesson8 folder
@collinzrj and I worked together on implementing LICM using LLVM.

We uses a ModuleAnalysisManager for our pass. Then we iterate through the functions inside the module and obtain the natural loops for each function. While this is really easy to use this has posed certain constraint to our optimizer: during testing we find out that our algorithm has problem doing optimization if a function A is called within a loop in function B
our loop pass mainly has 2 functions. One to identify the loop invariants and one to make sure it is safe to move the instructions to the preheader.
To identify loop invariant instructions, we first tried the "isLoopVariant" library function but it turns out to be too conservative and marks nearly all instructions not invariant. Hence we tried to implement the algorithm taught in class, but implementing the reaching definition is really complicated in llvm, for instance there is so many types of instructions in llvm and llvm uses pointer type instructions extensively.
In the safeToHoist function, we use the isSafeToSpeculativelyExecute library function to test whether the instruction has side effects. Then we use the dominator tree to check whether the instruction dominates all loop exit or the definition dominates all of its uses

## Test
we have 3 simple tests to test the capability (loop.c, foo.c, and test.c) In loop.c our function successfully identifies the only loop invariant (we assign variable to constant in a loop repetitively). In test.c we tests whether our algorithm could identify common nonvariant instructions like an instruction doesn't dominate loop exit or load from memory. In foo.c exposes the limitation of only obtaining loop information inside function call

## Hardest Part
we encountered a lot of problems due to the recent upgrade of the llvm library, making a lot of the manager classes legacy and hard to use. Meanwhile, we also face problem using the latest library functions. Also many documentations are for the legacy library functions so pretty hard to learn.

we first tried to use the latest loopmanager to obtain the natural loops, but didn't succeed, so we have to take a step back and use the legacy one, which works in a constraint way.
we also manually writes helper functions to deal with edge cases with pointer instructions that could be treated as invariants.
Some llvm functions doesn't do the same thing as its name indicates (e.g. isLoopInvariant) so we have to read through the original code to understand what it does

### Handle Load And Store Instruction
We found that load and store instructions can't be simply handled by the algorithm given in the course notes. However, llvm heavily relies on load and store. As a result, we extended the algorithm to handle load and store cases. We copied the pseudocode from the course notes, and prefix our changes with ">", our [code](link) also has comments explain the algo. 
```
iterate to convergence:
    > for every pointer in the loop:
        > mark it as InvariantPointer iff, for all values written to the pointer, either:
            > the value is never written to or only wirtten by an InvariantPointer
            > the value is never written to or only written by an InvariantInstruction
    for every instruction in the loop:
        mark it as LI iff, for all arguments x:
            > if x is a LoadInst:
                > it only loads from value outside the loop or invariant pointer/value
            > if x is a StoreInst:
                > it is only stored by value outside the loop or invariant pointer/value
            else:
                all reaching defintions of x are outside of the loop, or
                there is exactly one definition, and it is already marked as
                    loop invariant
```