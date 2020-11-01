import vmparser
from tokens import tokenizer, TokenTranslator
from tokentohack import HackTranslator

test_stream = """add
sub
neg
eq
gt
lt
and
or
not
push argument 0
pop argument 0
push local 1
pop local 1
push static 1
pop static 1
push this 2
pop this 2
push that 1
pop that 1
push pointer 0
pop pointer 0
push temp 0
pop temp 0
label loop
goto loop
if-goto loop
function funcname 2
return
call funcname 2""".splitlines()

class PseudoTranslator(TokenTranslator):
    def translate_arithmetic(self, cmdtype):
        return f'TODO - Arithmetic Command {cmdtype}'
    
    def translate_push(self, memseg, value):
        return f'TODO - Push Command {memseg} {value}'
    
    def translate_pop(self, memseg, value):
        return f'TODO - Pop Command {memseg} {value}'

    def translate_label(self, label):
        return f'TODO - Label Command {label}'

    def translate_goto(self, label):
        return f'TODO - Goto Command {label}'

    def translate_if(self, label):
        return f'TODO - If Command {label}'

    def translate_function(self, name, argcount):
        return f'TODO - Function Command {name} {argcount}'

    def translate_call(self, name, argcount):
        return f'TODO - Call Command {name} {argcount}'

    def translate_return(self):
        return 'TODO - Return Command'

test_stream = """// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/07/StackArithmetic/SimpleAdd/SimpleAdd.vm

// Pushes and adds two constants.
push constant 7
push constant 8
add""".splitlines()

parser = vmparser.Parser(test_stream, tokenizer)
translator = HackTranslator('test')

for token in parser:
    print(token.translate(translator))