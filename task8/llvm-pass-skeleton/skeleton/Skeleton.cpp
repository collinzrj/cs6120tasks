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
    
    std::set<Value> getLoopInvariants(Loop *L)
    {
        std::set<Value> loopInvariants;
        int loopInvariantsSize = 0;
        do {
            loopInvariantsSize = loopInvariants.count();
            for (auto &BB : L->blocks()) {
                for (auto &I : *BB) {
                    bool isLoopInvariant = true;
                    for (int i = 0; i < I.getNumOperands(); i++) {
                        llvm::Value *operand = I.getOperand(i);
                        if (L->contains(operand) && loopInvariants.find(operand) == loopInvariants.end()) {
                            isLoopInvariant = false;
                            break;
                        }
                    }
                    if (isLoopInvariant) {
                        loopInvariants.insert(I);
                    }
                }
            }
        } while(loopInvariants.count() > loopInvariantsSize);
        return loopInvariants;
    }

    bool safeToHoist(Loop *L, Instruction *I, DominatorTree *DT)
    {
        // check side effects
        // if (!isSafeToSpeculativelyExecute(I))
        //     return false;
        
        for (auto U: I->users()) {
            if (auto user = dyn_cast<Instruction>(U)) {
                if (!DT->dominates(I->getParent(), user->getParent())) {
                    errs() << "not dominate use!\n";
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
                for (BasicBlock::iterator instr = ExitBlocks[i]->begin(), be = ExitBlocks[i]->end(); instr != be; ++instr)
                {
                    Instruction *V = &(*instr);
                    errs() << *V << "\n";
                }
                errs() << "not dominate exit!\n";
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
        std::set<Value> loopInvariants = getLoopInvariants(L);
        for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
        {
            for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                 instr != be; ++instr)
            {
                Instruction *V = &(*instr);
                errs() << "Instruction: " << *V << "\n";
                errs() << L->isLoopInvariant(V) << " " << safeToHoist(L, V, DT) << "\n";
                if (loopInvariants.find(L) != loopInvariants.end() && safeToHoist(L, V, DT))
                {
                    V->moveBefore(InsertPt);
                    errs() << "Should move instruction" << V << "\n";
                    Changed = true;
                }
            }
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
            // for (auto &L : LI) {
            //     errs() << "Loop:\n";
            //     for (auto &BB : L->blocks()) {
            //         for (auto &I : *BB) {
            //             errs() << "Instruction: " << I << "\n";
            //         }
            //     }
            // }
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