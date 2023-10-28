## Summary
Implementation of Garbage Collection using reference pointer [gc-brili.ts](https://github.com/collinzrj/bril/blob/main/gc-brili.ts)
@collinzrj and I worked together for this task.

We choose reference counting for bril typescript interpreter because it most straightforward. For Bril there are few cases to consider as what type of instructions would constitute as necessary to update the reference counter. After discussion we think these are the cases
- Id, if we assign a pointer to another value
- Array, in which we would be allocating a continuous block of memory, and each of the entry might be referencing another pointer
- Load/Store, since the pointers may themselves store reference to pointers, so any load or store operation would possibly increase the reference count of the base address
- If we are overwriting an existing pointer with another pointer value, then we would possibly loose that reference, so whenever reassigning pointer values, we should check if the destination already points to a pointer and decrement its reference count.

Another concept we spent some time to figure out is what happens when sth goes out of scope, e.g. exit from function call, and how to deal with those variables. We used a pretty brute-force approach by keeping a pointer_stack that keeps track of the pointers before entering and after finishing the function call. Then we go through the stack and decrease the reference count of pointers. An edge case we encountered here is that for functions that return pointers, the pointer value should still remain and its reference count shouldn't be decreased to zero and removed. To do this the sequence of updating the reference count matters (we need to first increment the RC of the returned ptr and then iterate through the stack and decrement the rc of ptrs on the stack)

## Test
we mainly take advantage of the existing benchmark bril test, and also added a few small test cases for the corner cases and debug purposes. Main tools we use are 'turnt' to compare the experimental outcomes with the manual free brili.
- We add test case to test an example of overriting pointers like this: 
```
ptr = alloc ...;
# do stuff with ptr
free ptr;
ptr = alloc ...;
# do other stuff with ptr
free ptr;
```
- we remove all the free instructions from the benchmark folder, and see if the function still produce the same results. This proves that our algorithm works well with handling functions, 

## Hardest Part
we encountered some problem with typescript first since it has some weird behavior when trying to access a map using the bracket '[]' operator, causing the values we read become undefined.

In addition, it is quite hard to figure out the corner cases. For instance, while developing we also find out that the main function call procedure is different from normal function calls, and should be dealt quite differently.


