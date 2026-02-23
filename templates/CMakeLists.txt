cmake_minimum_required(VERSION 3.14)
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

# Coverage support
option(ENABLE_COVERAGE "Enable coverage instrumentation" OFF)
if(ENABLE_COVERAGE AND NOT MSVC)
    add_compile_options(--coverage -O0 -g)
    add_link_options(--coverage)
endif()

# Create library
add_library({{PROJECT_NAME}} {{LIB_TYPE}} src/{{PROJECT_NAME}}.cpp)

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

# Helpful messages
message(STATUS "-----------------------------------------------------------")
message(STATUS "  {{PROJECT_NAME}} Configuration Complete")
message(STATUS "  - Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  - Testing:    ${BUILD_TESTING}")
message(STATUS "  - Coverage:   ${ENABLE_COVERAGE}")
message(STATUS "-----------------------------------------------------------")
message(STATUS "💡 TIP: Use './script/auto_run.ps1' for one-click build & test.")
message(STATUS "-----------------------------------------------------------")
