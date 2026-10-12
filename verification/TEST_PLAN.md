# Verification Test Plan

| Test | Area | Expected behavior | Failure caught |
|---|---|---|---|
| `arithmetic_precedence` | Expressions | `10 + 20 * 2` produces `50` | Incorrect precedence or arithmetic lowering |
| `parentheses_override_precedence` | Expressions | `(10 + 20) * 2` produces `60` | Incorrect parenthesized expression handling |
| `integer_division` | Expressions | `17 / 5` produces `3` | Incorrect integer division behavior |
| `if_else` | Control flow | True condition assigns and prints `1` | Incorrect conditional branch generation |
| `while_loop_sum` | Control flow | Sum from 1 through 5 is `15` | Incorrect loop condition, body or back edge |
| `recursive_factorial` | Functions | `factorial(5)` produces `120` | Incorrect calls, stack frames or return values |
| `input_output` | I/O | Input `21` produces `42` | Incorrect read, arithmetic or write behavior |
| `multiple_writes` | I/O | Outputs remain `3 8 13` in order | Lost, reordered or corrupted output |

## Test design principles

1. Keep each program focused on one behavior where possible.
2. Use an expected result that is easy to verify independently.
3. Include test input in the JSON manifest, not in the runner implementation.
4. Run the full suite after every compiler or interpreter change.
5. Preserve failing inputs as fixtures so regressions stay reproducible.

## Known gaps / next steps

- Add malformed-source tests once the compiler's parser error/exit behavior is made reliable.
- Add deterministic generated arithmetic expressions and compare against a Python reference evaluator.
- Add boundary cases for integer limits, nested control flow, arrays, and function arguments.
- Add a CI job that builds with Flex/Bison and runs the suite on each change.
- For GPU relevance, create a separate CUDA/PTX testing track rather than implying these Mini-C tests verify NVIDIA hardware or CUDA compilers.
