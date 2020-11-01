from tokens import TokenTranslator, MemorySegment, Arithmetic

class HackTranslator(TokenTranslator):
    ptr_start = 3
    temp_start = 5
    static_start = 16
    stack_start = 256

    def __init__(self):
        super().__init__()
        self.lblcounter = 0
    
    def translate(self, token):
        return token.translate(self)
    
    def initialize_vm(self):
        return f'\n@{self.stack_start}\nD=A\n@0\nM=D\n@Sys.init\n0;JMP\n'

    def translate_arithmetic(self, cmdtype):
        func, op = self.arithmetic_translators[cmdtype]
        return func(self, op)
    
    def translate_push(self, memseg, value):
        return f'{self.tx_read_seg_to_D(memseg, value)}{push_D_to_stack}'
    
    def tx_read_seg_to_D(self, memseg, value):
        if memseg == MemorySegment.Constant:
            return f'@{value}\nD=A\n'

        if memseg == MemorySegment.Pointer:
            lookup = f'@{self.ptr_start + int(value)}\n'
        elif memseg == MemorySegment.Temp:
            lookup = f'@{self.temp_start + int(value)}\n'
        elif memseg == MemorySegment.Static:
            lookup = f'@{self.static_start + self._get_static_index(int(value))}\n'
        elif memseg in (MemorySegment.Local, MemorySegment.Argument, MemorySegment.This, MemorySegment.That):
            if value == "0":
                lookup = f'@{self.hack_mem_segs[memseg]}\nA=M\n'
            else:
                lookup = (f'@{value}\n' +
                        'D=A\n' +
                        f'@{self.hack_mem_segs[memseg]}\n' +
                        'A=M+D\n')
        else:
            raise ValueError('unknown memory segment', memseg, value)
        return lookup + 'D=M\n'
    
    def translate_pop(self, memseg, value):
        if memseg == MemorySegment.Constant:
            raise ValueError('Cannot POP a constant')
        if memseg == MemorySegment.Pointer:
            return f'{pop_to_D}@{self.ptr_start + int(value)}\nM=D\n'
        if memseg == MemorySegment.Temp:
            return f'{pop_to_D}@{self.temp_start + int(value)}\nM=D\n'
        if memseg == MemorySegment.Static:
            return f'{pop_to_D}@{self.static_start + self._get_static_index(int(value))}\nM=D\n'
        
        if memseg in (MemorySegment.Local, MemorySegment.Argument, MemorySegment.This, MemorySegment.That):
            if value == "0":
                lookup = f'{pop_to_D}@{self.hack_mem_segs[memseg]}\n'
            else:
                lookup = (f'@{value}\n' +
                        'D=A\n' +
                        f'@{self.hack_mem_segs[memseg]}\n' +
                        'D=M+D\n' +
                        '@13\n' + 
                        'M=D\n' +
                        pop_to_D +
                        '@13\n')
        else:
            raise ValueError('unknown memory segment', memseg, value)
        
        return lookup + 'A=M\nM=D\n'
    
    def translate_label(self, label):
        return f'({label})\n'

    def translate_goto(self, label):
        return f'@{label}\n0;JMP\n'

    def translate_if(self, label):
        return pop_to_D + f'@{label}\nD;JNE\n'

    def translate_function(self, name, lclcount):
        out = f'({name})\n'
        for _ in range(int(lclcount)):
            out += self.translate_push(MemorySegment.Constant, 0)
        return out
    
    def save_segment(self, memseg):
        return f'@{self.hack_mem_segs[memseg]} //save {memseg.value}\nD=M\n{push_D_to_stack}'

    def translate_call(self, name, argcount):
        cnt = self.lblcounter
        self.lblcounter += 1
        return (f'@RETURN{cnt} //return address\n' +
                'D=A\n' +
                push_D_to_stack +
                self.save_segment(MemorySegment.Local) +
                self.save_segment(MemorySegment.Argument) +
                self.save_segment(MemorySegment.This) + 
                self.save_segment(MemorySegment.That) +
                '@SP //save new LCL\n' +
                'D=M\n' +
                '@LCL\n' +
                'M=D //save new ARG\n' +
                f'@{int(argcount) + 5}\n' +
                'D=D-A\n' +
                '@ARG\n' +
                'M=D\n' +
                f'@{name}\n' +
                '0;JMP\n' +
                f'(RETURN{cnt})\n')

    def translate_return(self):
        return (self.ret_store_return_val(13) +
                self.ret_store_old_stack_top(14) +
                '@LCL\nD=M\n@SP\nM=D\n' +
                self.ret_restore(MemorySegment.That) +
                self.ret_restore(MemorySegment.This) +
                self.ret_restore(MemorySegment.Argument) +
                self.ret_restore(MemorySegment.Local) +
                self.ret_store_return_addr(15) +
                self.ret_reset_stack_top(14) +
                self.ret_push_return_value(13) +
                self.ret_jump_to_return_addr(15))
    
    def ret_store_return_val(self, tempaddr):
        return '//store return val\n' + self.ret_store_top(tempaddr)
    
    def ret_store_top(self, tempaddr):
        return pop_to_D + f'@{tempaddr}\nM=D\n'
    
    def ret_store_old_stack_top(self, tempaddr):
        return f'@ARG //store old stack ptr\nD=M\n@{tempaddr}\nM=D\n'
    
    def ret_store_return_addr(self, tempaddr):
        return '//store return address\n' + self.ret_store_top(tempaddr)
    
    def ret_restore(self, memseg):
        return f'//restore {memseg.value}\n' + pop_to_D + f'@{self.hack_mem_segs[memseg]}\nM=D\n'
    
    def ret_reset_stack_top(self, tempaddr):
        return f'@{tempaddr} //reset stack ptr\nD=M\n@SP\nM=D\n'
    
    def ret_push_return_value(self, tempaddr):
        return f'@{tempaddr} //push return value \nD=M\n' + push_D_to_stack
    
    def ret_jump_to_return_addr(self, tempaddr):
        return f'@{tempaddr} //jump to return addr\nA=M\n0;JMP\n'

    def tx_binary(self, operator):
        return f'{pop_to_D}A=A-1\nD=M{operator}D\n{move_D_to_stack}'

    def tx_comparison(self, operator):
        cnt = self.lblcounter
        self.lblcounter += 1
        return ('@SP\n' +
                'A=M-1\n'+
                'D=M\n' +
                'A=A-1\n' +
                'D=M-D\n' +
                f'@TRUE{cnt}\n' +
                f'D;{operator}\n' +
                'D=0\n' +
                f'@CONTINUE{cnt}\n' +
                f'0;JMP\n' +
                f'(TRUE{cnt})\n' +
                'D=-1\n' +
                f'(CONTINUE{cnt})\n' +
                '@SP\n' +
                'A=M-1\n' +
                'A=A-1\n' +
                'M=D\n' +
                'D=A+1\n' +
                '@SP\n' +
                'M=D\n')

    def tx_unary(self, operator):
        return (f'{point_to_stack_top}' +
                f'M={operator}M\n')
        
    arithmetic_translators = {
        Arithmetic.Types.Add: (tx_binary, '+'),
        Arithmetic.Types.Subtract: (tx_binary, '-'),
        Arithmetic.Types.Negative: (tx_unary, '-'),
        Arithmetic.Types.Equal: (tx_comparison, 'JEQ'),
        Arithmetic.Types.GreaterThan: (tx_comparison, 'JGT'),
        Arithmetic.Types.LessThan: (tx_comparison, 'JLT'),
        Arithmetic.Types.And: (tx_binary, '&'),
        Arithmetic.Types.Or: (tx_binary, '|'),
        Arithmetic.Types.Not: (tx_unary, '!')
    }

    hack_mem_segs = {
        MemorySegment.Argument: "ARG",
        MemorySegment.Local: "LCL",
        MemorySegment.This: "THIS",
        MemorySegment.That: "THAT",
    }

point_to_stack_top = '@SP\nA=M-1\n'
pop_to_D = '@SP\nD=M-1\nM=D\nA=D\nD=M\n'
move_D_to_stack = 'M=D\nD=A+1\n@SP\nM=D\n'
push_D_to_stack = f'@SP\nA=M\n{move_D_to_stack}'