#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Analysis/ValueTracking.h"
#include "llvm/IR/Dominators.h"
#include "llvm/Analysis/PostDominators.h"

using namespace llvm;

namespace {

struct SkeletonPass : public PassInfoMixin<SkeletonPass> {

    void getLoopInvariants(Loop *L, std::set<Instruction*>& loopInvariants)
    {
        std::map<Value*, std::vector<Value*>> ptrWrittenBy;
        std::set<Value*> invariantPointers;
        for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
        {
            for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                instr != be; ++instr) {
                    Instruction *V = &(*instr);
                    StoreInst *op = dyn_cast<StoreInst>(V);
                    if (op) {
                        ptrWrittenBy[op->getPointerOperand()].push_back(op->getValueOperand());
                    }
                }
        }
        // pointer is invariant if it is not written to, or it's only written to by invariants
        int prevInvariantPointersSize = 0;
        do {
            prevInvariantPointersSize = invariantPointers.size();
            for (auto p : ptrWrittenBy) {
                Value* destPtr = p.first;
                std::vector<Value*> srcPtrArr = p.second;
                bool ptrIsInvariant = true;
                for (auto srcPtr : srcPtrArr) {
                    if (ptrWrittenBy.count(srcPtr) && !invariantPointers.count(srcPtr)) {
                        ptrIsInvariant = false;
                        break;
                    }
                }
                if (ptrIsInvariant) {
                    invariantPointers.insert(destPtr);
                }
            }
        } while (invariantPointers.size() > prevInvariantPointersSize);
        int loopInvariantsSize = 0;
        // handle pointers first
        for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
        {
            for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                    instr != be; ++instr)
            {
                Instruction *V = &(*instr);
                if (isa<LoadInst>(V)) {
                    LoadInst *op = dyn_cast<LoadInst>(V);
                    Value *loadPtr = op->getPointerOperand();
                    if (!ptrWrittenBy.count(loadPtr) || invariantPointers.count(loadPtr))
                    {
                        loopInvariants.insert(V);
                    }
                } else if (isa<StoreInst>(V)) {
                    StoreInst *inst = dyn_cast<StoreInst>(V);
                    Value *destPtr = inst->getPointerOperand();
                    Value *srcPtr = inst->getValueOperand();
                    if (!ptrWrittenBy.count(destPtr) || invariantPointers.count(destPtr))
                    {
                        loopInvariants.insert(V);
                    }
                }
            }
        }
        do {
            loopInvariantsSize = loopInvariants.size();
            for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
            {
                for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                        instr != be; ++instr)
                {
                    if (instr->isBinaryOp() || instr->isShift() || instr->isCast() || isa<GetElementPtrInst>(instr) 
                    || isa<InsertElementInst>(instr) || isa<ExtractElementInst>(instr) || isa<SelectInst>(instr) || isa<LoadInst>(instr))
                    {
                        Instruction *V = &(*instr);

                        bool isLoopInvariant = true;
                        if (isa<LoadInst>(V) || isa<StoreInst>(V)) {
                            // already handled by above code
                            continue;
                        } else {
                            for (Use& U: V->operands())
                            {
                                Value *operand = U.get();
                                Instruction *opi = dyn_cast<Instruction>(operand);
                                if (opi && opi->getParent() && (L->contains(opi) && !loopInvariants.count(opi)))
                                {
                                    errs() << "Instruction not LI: " << *V << "\n";
                                    isLoopInvariant = false;
                                    break;
                                }
                                
                            }
                        }
                        if (isLoopInvariant)
                        {
                            loopInvariants.insert(V);
                        }
                    }
                }
            }
        } while(loopInvariants.size() > loopInvariantsSize);
        return;
    }

    bool safeToHoist(Loop *L, Instruction *I, DominatorTree *DT)
    {
        // check side effects
        // if (!isSafeToSpeculativelyExecute(I))
        //     return false;
        
        for (auto U: I->users()) {
            if (auto* user = dyn_cast<Instruction>(U)) {
                if (!DT->dominates(I->getParent(), user->getParent())) {
                    // errs() << "not dominate use!\n";
                    return false;
                };
            }
        }
        // The basic block dominates all exit blocks for the loop.
        // Use dominator tree to check for dominance.
        SmallVector<BasicBlock *> ExitBlocks = SmallVector<BasicBlock *>();
        L->getExitingBlocks(ExitBlocks);
        for (unsigned i = 0, e = ExitBlocks.size(); i != e; ++i)
            if (!DT->dominates(I->getParent(), ExitBlocks[i]))
            {
                // for (BasicBlock::iterator instr = ExitBlocks[i]->begin(), be = ExitBlocks[i]->end(); instr != be; ++instr)
                // {
                    // Instruction *V = &(*instr);
                    // errs() << *V << "\n";
                // }
                // errs() << "not dominate exit!\n";
                return false;
            }
        return true;
    }

    bool LICM(Loop *L, DominatorTree *DT)
    {
        errs() << "enter LICM\n";
        bool Changed = false;
        BasicBlock *preheader = L->getLoopPreheader();
        if (!preheader)
            return false;
        auto InsertPt = preheader->getTerminator();
        std::vector<BasicBlock::iterator> ins_move;
        // Each Loop object has a preheader block for the loop .
        std::set<Instruction*> loopInvariants;
        std::set < Instruction *> instr_to_move;
        getLoopInvariants(L, loopInvariants);
        errs() << loopInvariants.size() << "\n";
        for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
        {
            for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                 instr != be; ++instr)
            {
                Instruction *V = &(*instr);
                errs() << "Instruction: " << *V << "\n";
                errs() << loopInvariants.count(V) << " " << safeToHoist(L, V, DT) << "\n";
                
                if (loopInvariants.count(V) && safeToHoist(L, V, DT))
                {
                    instr_to_move.insert(V);
                    errs() << "Should move instruction" << *V << "\n";
                    Changed = true;
                }
            }
        }
        for (auto i : instr_to_move) {
            i->moveBefore(InsertPt);
        }
        return Changed;
    }

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        auto &FAM = AM.getResult<FunctionAnalysisManagerModuleProxy>(M).getManager();
        for (auto &F : M) {
            errs() << "I saw a function called " << F.getName() << "!\n";
            auto &LI = FAM.getResult<LoopAnalysis>(F);
            DominatorTree* DT = new DominatorTree(F);
            // print the loops first
            for (auto &L : LI) {
                errs() << "Loop:\n";
                for (auto &BB : L->blocks()) {
                    for (auto &I : *BB) {
                        errs() << "Instruction: " << I << "\n";
                    }
                }
            }
            for (auto L : LI)
            {
                LICM(L, DT);
            }
        }
        return PreservedAnalyses::all();
    };
};

}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "Skeleton pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level) {
                    MPM.addPass(SkeletonPass());
                });
        }
    };
}