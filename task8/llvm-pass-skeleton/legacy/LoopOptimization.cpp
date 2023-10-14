#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Transforms/Utils/LoopUtils.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/LoopPass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"

using namespace llvm;

namespace {

struct MyLoopPass : public LoopPass {
    static char ID;
    MyLoopPass() : LoopPass(ID) {}

    bool isLoopInvariant(Loop *L, Instruction *I)
    {
        // if instructions are binary operator, shift, select, cast, getelementptr
        if (I->isBinaryOp() || I->isShift() || I->isCast() || isa<GetElementPtrInst>(I))
        {
            for (auto operand = I->operands().begin(); operand != I->operands().end(); ++operand)
            {
                if (Instruction *Ins = dyn_cast<Instruction>(operand))
                {
                    if (L->contains(Ins))
                        return false;
                }
            }
            return true;
        }
        return false;
    }

    bool runOnLoop(Loop *L, LPPassManager &LPM) override {
        // Your transformation code here
        for (BasicBlock *B: L->blocks()) {
            for (Instruction &I: *B) {
                errs() << "Instruction: " << I << "\n";
            }
        } 
        // Return true if the loop is modified, false otherwise
        return false;
    }
    void getAnalysisUsage(AnalysisUsage &AU) const override {
        AU.setPreservesCFG();
        AU.addRequired<LoopInfoWrapperPass>();
    }
};

}

char MyLoopPass::ID = 0;
static RegisterPass<MyLoopPass> X("mylooppass", "My Loop Pass", false, false);

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
return {
    .APIVersion = LLVM_PLUGIN_API_VERSION,
    .PluginName = "My Loop Pass",
    .PluginVersion = "v0.1",
    .RegisterPassBuilderCallbacks = [](PassBuilder &PB)
    {
        // PB.registerLoopOptimizerEndEPCallback
        PB.registerPipelineStartEPCallback(
            [](ModulePassManager &MPM, OptimizationLevel Level)
            {
                MPM.addPass(MyLoopPass());
            });
    }};
}


// extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo

// extern "C" void LLVM_ATTRIBUTE_WEAK initializeMyLoopPassPass(PassRegistry &);
// extern "C" void LLVM_ATTRIBUTE_WEAK initializeLoopInfoWrapperPassPass(PassRegistry &Registry);

// extern "C" void LLVM_ATTRIBUTE_WEAK initializePasses() {
//     initializeMyLoopPassPass(*PassRegistry::getPassRegistry());
//     initializeLoopInfoWrapperPassPass(*PassRegistry::getPassRegistry());
// }

// __attribute__((constructor))
// void initializePlugin() {
//    initializePasses();
// }

