from enum import Enum  # !!!!!!!!!!!!!!!!
from abc import ABC, abstractmethod
from typing import List, Callable

from vmparser import Token, Tokenizer


class MemorySegment(Enum):
    Argument = 'argument'
    Local = 'local'
    Static = 'static'
    Constant = 'constant'
    This = 'this'
    That = 'that'
    Pointer = 'pointer'
    Temp = 'temp'

class Command(Token, ABC):
    cmd = None

    def __init__(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2
    
    @classmethod
    def is_command(cls, cmd):
        return cmd == cls.cmd

    def __str__(self):
        return f'{self.__class__.__name__} {self.arg1} {self.arg2}'

class NewFile(Command):
    cmd = 'newfile'

    def __init__(self, *args):
        super().__init__(None, None)

    def __str__(self):
        return "New File"
    
    def translate(self, translator: 'TokenTranslator'):
        return translator.new_file()

class Arithmetic(Command):
    class Types(Enum):
        Add = 'add'
        Subtract = 'sub'
        Negative = 'neg'
        Equal = 'eq'
        GreaterThan = 'gt'
        LessThan = 'lt'
        And = 'and'
        Or = 'or'
        Not = 'not'
    
    def __init__(self, cmd, *ignore):
        super().__init__('', '')
        try:
            self.type = next(type for type in self.Types if type.value == cmd)
        except StopIteration:
            raise ValueError('Not a valid arithmetic command: ' + cmd)
    
    @classmethod
    def is_command(cls, cmd):
        return cmd in [ac.value for ac in Arithmetic.Types]

    def translate(self, translator: 'TokenTranslator'):
        return translator.translate_arithmetic(self.type)
    
    def __str__(self):
        return f'{self.__class__.__name__} {self.type.value}'

class Push(Command):
    cmd = 'push'

    def __init__(self, arg1, arg2, *ignore):
        super().__init__(arg1, arg2)
        self.memseg = next(seg for seg in MemorySegment if seg.value == self.arg1)

    def translate(self, translator: 'TokenTranslator'):
        return translator.translate_push(self.memseg, self.arg2)
        
class Pop(Command):
    cmd = 'pop'

    def __init__(self, arg1, arg2, *ignore):
        super().__init__(arg1, arg2)
        self.memseg = next(seg for seg in MemorySegment if seg.value == self.arg1)
        if self.memseg ==  MemorySegment.Constant:
            raise ValueError("Cannot POP a constant")

    def translate(self, translator: 'TokenTranslator'):
        return translator.translate_pop(self.memseg, self.arg2)

class Label(Command):
    cmd = 'label'

    def __init__(self, label, *ignore):
        super().__init__(label, "")
        self.label = label

    def translate(self, translator: 'TokenTranslator'):
        return translator.translate_label(self.label)

class Goto(Command):
    cmd = 'goto'

    def __init__(self, label, *ignore):
        super().__init__(label, "")
        self.label = label

    def translate(self, translator):
        return translator.translate_goto(self.label)

class If(Command):
    cmd = 'if-goto'

    def __init__(self, label, *ignore):
        super().__init__(label, "")
        self.label = label

    def translate(self, translator):
        return translator.translate_if(self.label)

class Function(Command):
    cmd = 'function'

    def __init__(self, name, argcount, *ignore):
        super().__init__(name, argcount)
        self.name = name
        self.argcount = argcount

    def translate(self, translator):
        return translator.translate_function(self.name, self.argcount)

class Return(Command):
    cmd = 'return'

    def __init__(self, *ignore):
        super().__init__('', '')

    def translate(self, translator):
        return translator.translate_return()

class Call(Command):
    cmd = 'call'

    def __init__(self, name, argcount, *ignore):
        super().__init__(name, argcount)
        self.name = name
        self.argcount = argcount

    def translate(self, translator):
        return translator.translate_call(self.name, self.argcount)

TokenMaker = Callable[..., Token]

tokens: List[TokenMaker] = [Arithmetic, Push, Pop, Label, Goto, If, Function, Return, Call, NewFile]


def tokenizer(vmline: str) -> Token:
    bits = vmline.split(' ')
    for token in tokens:
        if token.is_command(bits[0]):
            if Arithmetic.is_command(bits[0]):
                return token(bits[0])
            else:
                return token(*bits[1:3])
    else:
        raise AssertionError(vmline + ' could not be tokenized. Command not recognized')


class TokenTranslator(ABC):

    def __init__(self):
        self.curr_static_base = 0
        self.curr_max = None
    
    def _get_static_index(self, file_index):
        if self.curr_max is None or file_index > self.curr_max:
            self.curr_max = file_index
        return self.curr_static_base + file_index
    
    def new_file(self):
        if self.curr_max is not None:
            self.curr_static_base += self.curr_max + 1
            self.curr_max = None
        return ''

    @abstractmethod
    def translate_arithmetic(self, cmdtype):
        pass

    @abstractmethod
    def translate_push(self, memseg, value):
        pass

    @abstractmethod
    def translate_pop(self, memseg, value):
        pass

    @abstractmethod
    def translate_label(self, label):
        pass

    @abstractmethod
    def translate_goto(self, label):
        pass

    @abstractmethod
    def translate_if(self, label):
        pass

    @abstractmethod
    def translate_function(self, name, argcount):
        pass

    @abstractmethod
    def translate_call(self, name, argcount):
        pass

    @abstractmethod
    def translate_return(self):
        pass
