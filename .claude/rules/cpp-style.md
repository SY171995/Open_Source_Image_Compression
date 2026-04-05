---
description: Coding style rules for C and C++ files
globs: ["**/*.cpp", "**/*.hpp", "**/*.c", "**/*.h"]
---

# Coding Style Rules

## Language Standard
- Always use C++20 or C++23 for new C++ code
- Use modern C++ features where appropriate (concepts, ranges, constexpr, etc.)

## Naming Conventions
- Member variables of classes and structs must have a trailing underscore (e.g., `width_`, `buffer_size_`)
- Use camelCase for all names: variables, functions, methods, parameters (e.g., `frameWidth`, `encodeImage`)
- Class and struct names use PascalCase (e.g., `ImageEncoder`, `ColorSpace`)

## Header vs Source
- If a function can be inlined, define it in the `.hpp` header file
- Otherwise, declare in `.hpp` and define in the `.cpp` source file
- Keep headers clean — avoid including unnecessary headers; prefer forward declarations

## General
- Prefer `const` and `constexpr` wherever possible
- Prefer references over raw pointers where ownership is not being transferred
- Do not use `using namespace` in header files
