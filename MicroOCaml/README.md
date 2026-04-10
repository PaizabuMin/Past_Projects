# MicroOCaml

MicroOCaml is a programming language implementation project that demonstrates the construction of a complete interpreter and compiler for a functional programming language similar to Ocaml.

## Project Goal

The primary goal of the MicroOCaml project is to implement a fully functional interpreter and compiler for the OCaml programming language using Racket as its construction, which includes the following key features:

- **Core Language Constructs**: Literals (integers, booleans, characters, strings), variables, and basic control flow (if expressions, begin blocks)
- **Arithmetic and Primitives**: Basic arithmetic operations (+, -), comparisons (=, <), and primitive functions (add1, sub1, zero?, etc.)
- **Data Structures**: Lists (cons, car, cdr, empty?), boxes (mutable references), vectors, and strings
- **Functions**: First-class functions with lambda expressions, function definitions, and rest parameters
- **Exception Handling**: Raise and with-handlers for error handling
- **I/O Operations**: Reading and writing bytes, characters, and handling EOF

The project is structured incrementally, with each "crime" (test suite) representing a milestone that adds new language features:

- **Abscond**: Basic literals and values
- **Blackmail**: Arithmetic operations
- **Con**: Conditional expressions
- **Dupe**: Boolean operations and zero?
- **Dodger**: Character operations
- **Evildoer**: Void and begin
- **Extort**: Error handling
- **Fraud**: Let bindings and arithmetic
- **Hustle**: Lists, boxes, and equality
- **Hoax**: Vectors and strings
- **Iniquity**: Function definitions
- **Loot**: Lambda expressions
- **Loot+**: Rest parameters and advanced function features

## Architecture

The implementation consists of several key components:

- **AST (ast.rkt)**: Defines the abstract syntax tree structures for all language constructs
- **Parser (parse.rkt)**: Converts source code into AST representations
- **Interpreter (interp.rkt)**: Executes programs directly by evaluating the AST
- **Compiler (compile.rkt)**: Translates AST into x86-64 assembly code
- **Runtime**: C code that provides low-level operations for the compiled code
- **Tests (test/)**: Comprehensive test suites validating each language feature

## Building and Running

The project uses Racket for the implementation and includes a Makefile for building the runtime components.

To run the interpreter on a Loot+ program:
```racket
(require "main.rkt")
(run-program some-loot-plus-expression)
```

To compile and run a program:
```racket
(require "compile.rkt")
(define asm (compile-program some-ast))
(run asm)
```