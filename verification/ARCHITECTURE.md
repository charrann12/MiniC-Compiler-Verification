# Architecture and Data Flow

## Existing compiler pipeline

```text
Mini-C source (.mc)
        |
        v
Flex scanner (scanner.l)
  characters -> tokens
        |
        v
Bison parser (minic.y)
  tokens -> grammar reductions + AST-building actions
        |
        v
AST helpers (parser.c / parser.h)
        |
        v
Intermediate code generator (icg.c)
  AST -> U-code (.uco)
        |
        v
U-code interpreter (ucodei.cpp)
  U-code -> observable program output
```

## Verification extension

```text
Test fixture (.mc) + manifest (.json)
        |
        v
Python test runner
        |
        +--> invoke minic in isolated temporary directory
        |       `--> require generated case.uco
        |
        +--> invoke ucodei with test stdin
        |       `--> capture output and exit status
        |
        v
Normalize whitespace + compare expected output
        |
        v
PASS / FAIL / ERROR + optional JSON report
```

The test runner intentionally uses a black-box boundary. It does not need to know the AST layout or U-code instruction encoding to verify externally observable behavior. This makes it useful for regression testing when compiler internals change.

## Failure categories

- `compile`: compiler exited unsuccessfully, failed to emit U-code, or reported a syntax error.
- `wrong-output`: program ran but output differed from the expected output.
- `runtime`: interpreter exited unsuccessfully.
- `compiler-timeout` / `execution-timeout`: a phase exceeded its configured timeout.
- `setup`: an executable was missing or not executable.

Whitespace is normalized for comparison because the supplied interpreter prints numeric output with leading spaces. Output order and numeric values are still checked.
