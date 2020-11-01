from vmparser import Parser
from tokens import tokenizer
from tokentohack import HackTranslator

from sys import argv
from pathlib import Path


def main():
    if len(argv) != 2:
        if len(argv) == 3 and argv[2] == '-p':
            will_print = True
        else:
            raise Exception('must include the path to a file or directory and nothing else, other than maybe -p flag to print the output instead of writing to a file')
    else:
        will_print = False

    path = Path(argv[1])

    parser = Parser(
        stream_file(path) if path.is_file() else stream_dir(path), 
        tokenizer)
    
    if will_print:
        write_to_screen(parser, HackTranslator())
    else:
        write_to_file(parser, HackTranslator(), path)


def write_to_screen(parser, translator):
    print('//initialize the stack, ect')
    print(translator.initialize_vm())
    for token in parser:
        print('//', token)
        print(translator.translate(token))


def write_to_file(parser, translator, path):
    filename = path.name if path.is_dir() else path.name[:-3]
    filename += '.asm'
    with open(filename, 'w') as file:
        file.write('//initialize the stack, ect')
        file.write(translator.initialize_vm())
        for token in parser:
            file.write('//' + str(token) + '\n')
            file.write(translator.translate(token))


def stream_file(file):
    yield 'newfile'
    with open(file, 'r') as file:
        yield from file.readlines()


def stream_dir(dir: Path):
    for path in dir.iterdir():
        if path.is_file():
            if path.name.endswith('.vm'):
                yield from stream_file(path)
        elif path.is_dir():
            yield from stream_dir(path)


if __name__ == "__main__":
    main()