# SIC/XE Assembler Project

This project implements a two-pass assembler for the SIC and SIC/XE architectures, supporting both command-line usage and automated testing. It provides tools for compiling assembly source files, comparing object code, and running comprehensive test suites.

---

**Table of Contents**

- [Features](#features)
- [Quick Start](#quick-start)
- [Compiling Assembly Code](#compiling-assembly-code)
- [Object File Format](#object-file-format)
- [Comparing Object Files](#comparing-object-files)
- [Testing](#testing)
- [Configuration and Modes](#configuration-and-modes)
- [Constants and Limits](#constants-and-limits)
- [Notes](#notes)

---

## Features

- Supports both SIC and SIC/XE assembly modes
- Command-line interface for assembling and testing
- Automated test runner with pytest integration
- Object file comparison utility
- Customizable test case modes and flexible test selection

---

## Quick Start

### 1. Build the Test Environment

- Create a Python virtual environment and install dependencies:
  ```bash
  ./scripts/setup_test_env.sh
  ```

### 2. Assemble a Source File

- To assemble a source file and generate an object file:
  ```bash
  python3 assembler.py path/to/source.asm
  ```
- To specify the output file path:
  ```bash
  python3 assembler.py path/to/source.asm -o path/to/output.obj
  ```
- To force SIC mode (default is SIC/XE):
  ```bash
  python3 assembler.py path/to/source.asm -o path/to/output.obj --sic
  ```

---

## Compiling Assembly Code

- The assembler accepts `.asm` files as input and produces `.obj` files as output.
- Output path can be specified with `-o`; otherwise, it defaults to the same name as the source with `.obj` extension.
- Use `--sic` to enable strict SIC mode, which disables SIC/XE-only features and enforces SIC addressing and instruction set restrictions.

---

## Object File Format

- The object file consists of records in the following order:
  - Header (`H`)
  - One or more Text records (`T`)
  - Zero or more Modification records (`M`)
  - End record (`E`)
- Each Text record contains up to 60 hexadecimal characters. If adding a new instruction would exceed this limit, a new Text record is started.
- Example object file:
  ```
  HADDEX 001000000015
  T0010001200100C18100F0C10124C0000000003000005
  E001000
  ```

---

## Comparing Object Files

- To compare two object files (ignoring trailing newlines):
  ```bash
  python3 compareobjectcode.py path/to/generated.obj path/to/expected.obj
  ```
- The tool reports the first difference found, including line and column.

---

## Testing

- All tests are located in the `test/` directory.
- To run all test cases:
  ```bash
  ./scripts/run_tests.sh
  ```
- To run specific test cases (by name or filename):
  ```bash
  ./scripts/run_tests.sh addexample studentexample
  ./scripts/run_tests.sh addexample.asm textbookexample.obj
  ```
- Test cases are defined by pairs of `.asm` (input) and `.obj` (expected output) files in `test/original/` and `test/target/`.
- If a required file is missing, the test runner will report the missing file and halt.

---

## Configuration and Modes

- Test case modes (SIC or SIC/XE) can be set in `test/cases.json`:
  ```json
  {
    "modes": {
      "addexample": "sic",
      "studentexample": "sic",
      "textbookexample": "sic"
    }
  }
  ```
- If a mode is not specified, the default is `sic` (can be overridden with `--default-mode` in the test runner).

---

## Constants and Limits

- Memory limit: 1,048,576 bytes (1M)
- Maximum reserve value: 32,767
- Text record hex limit: 60 characters
- Word value range: -8,388,608 to 8,388,607
- Format 3 immediate: -2,048 to 2,047
- Format 4 immediate: -524,288 to 524,287
- PC-relative: -2,048 to 2,047
- BASE-relative: 0 to 4,095
- SIC direct: 0 to 32,767
- SVC: 0 to 15
- Shift: 0 to 15

---

## Notes

- The assembler enforces strict mode checks and will report errors for unsupported instructions or addressing modes in SIC mode.
- All paths are relative to the project root unless otherwise specified.
- For a detailed explanation of the assembler's Pass 2 logic, see [pass2.md](pass2.md). This document was generated with the help of Codex, based on a conversation in `conversations/generate_pass2_docs/conversation.md`.
- The `conversations/` folder contains my development conversations with Codex, which were used to assist in generating documentation or design ideas. All other code and documentation were written by myself.
- For more details on the assembler's internal logic, see `pass2.md` and the source code in the `passers/` and `lib/` directories.
  q
