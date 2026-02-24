cmake_minimum_required(VERSION 3.14)

# Optional Compiler Override (Set during generation)
if(NOT CMAKE_CXX_COMPILER AND NOT "{{COMPILER_PATH}}" STREQUAL "")
    set(CMAKE_CXX_COMPILER "{{COMPILER_PATH}}")
endif()

project({{PROJECT_NAME}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD {{CPP_STD}})
set(CMAKE_CXX_STANDARD_REQUIRED {{CPP_STD_REQ}})
set(CMAKE_EXPORT_COMPILE_COMMANDS {{EXPORT_CMDS}})

# Enable warnings
if(MSVC)
    add_compile_options(/W4)
    if({{WERROR}})
        add_compile_options(/WX)
    endif()
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
    if({{WERROR}})
        add_compile_options(-Werror)
    endif()
endif()

# Interprocedural Optimization (LTO)
if({{LTO}})
    include(CheckIPOSupported)
    check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)
    if(ipo_supported)
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
    else()
        message(STATUS "LTO not supported: ${ipo_error}")
    endif()
endif()

# Static Analysis (Clang-Tidy)
if({{CLANG_TIDY}} AND CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    find_program(CLANG_TIDY_EXE NAMES clang-tidy)
    if(CLANG_TIDY_EXE)
        message(STATUS "Integrating Clang-Tidy into build process (Clang detected)")
        set(CMAKE_CXX_CLANG_TIDY "${CLANG_TIDY_EXE}")
    else()
        message(WARNING "Clang-Tidy was requested but the executable was not found.")
    endif()
elseif({{CLANG_TIDY}})
    message(STATUS "Clang-Tidy disabled: Only supports Clang compiler (Detected: ${CMAKE_CXX_COMPILER_ID})")
endif()

# Create library
add_library({{PROJECT_NAME}} STATIC src/{{PROJECT_NAME}}.cpp)

# Include directories
target_include_directories({{PROJECT_NAME}}
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/interface>
    PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/inc>
)

# Tests
option(BUILD_TESTING "Build unit tests" ON)
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()

# Examples
option(BUILD_EXAMPLES "Build examples" ON)
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
