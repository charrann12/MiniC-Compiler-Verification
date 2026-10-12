# Mini-C Compiler Verification Suite

A black-box test harness that extends the supplied MiniC-Compiler educational project. It compiles small Mini-C programs using the existing `minic` executable, executes the emitted U-code with `ucodei`, and compares observed output with expected output.

## What it verifies

- Arithmetic precedence and parentheses
- Integer division
- Conditional control flow
- Loop behavior
- Recursive function calls
- Standard input and output
- Ordered output across multiple `write` calls

The suite is intentionally external to the compiler implementation. It does not modify the compiler's semantics; it checks the behavior visible to a program author.

## Requirements

- Python 3.9+
- GCC/G++
- Flex and Bison

## Build

From the repository root on Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y build-essential flex bison
./build.sh
```

## Run tests

```bash
python3 verification/run_tests.py
```

Run one focused group:

```bash
python3 verification/run_tests.py --filter factorial
python3 verification/run_tests.py --filter expressions
```

Write a machine-readable report:

```bash
python3 verification/run_tests.py --json-report reports/verification.json
```

List test cases without running them:

```bash
python3 verification/run_tests.py --list
```

Test the harness itself (does not require Flex/Bison or built compiler binaries):

```bash
python3 -m unittest verification/test_runner_unit.py -v
```

## How a test is executed

1. The runner copies a fixture to an isolated temporary directory as `case.mc`.
2. It runs `minic case.mc` and checks that a `.uco` file was emitted without a syntax diagnostic.
3. It runs `ucodei case.uco`, passing any test input through standard input.
4. It normalizes whitespace and compares output with the expected result in the sidecar JSON file.
5. It reports `PASS`, `FAIL`, or `ERROR`, with failure categories such as `compile`, `wrong-output`, `runtime`, and timeout.

Every test has a `.mc` source and a same-named `.json` manifest. Add a test by creating both files. Keep each test small and focused so failures are easy to diagnose.

## Current scope and limitations

This is a starter verification suite, not proof of complete compiler correctness. It tests the existing Mini-C compiler plus its U-code interpreter as a combined pipeline. It does not yet test CUDA/PTX, GPU hardware, optimization correctness, randomized fuzzing, or invalid-program diagnostics. A future extension could add generated expressions, differential tests against a reference evaluator, and CI regression runs.
