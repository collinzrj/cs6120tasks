	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 12, 0
	.globl	_mul                            ; -- Begin function mul
	.p2align	2
_mul:                                   ; @mul
	.cfi_startproc
; %bb.0:
	sub	sp, sp, #16
	.cfi_def_cfa_offset 16
	str	w0, [sp, #12]
	str	w1, [sp, #8]
	ldr	w8, [sp, #12]
	ldr	w9, [sp, #8]
	mul	w0, w8, w9
	add	sp, sp, #16
	ret
	.cfi_endproc
                                        ; -- End function
.subsections_via_symbols
