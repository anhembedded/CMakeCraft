cmake_minimum_required(VERSION 3.14)
project({{PROJECT_NAME}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Enable warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Coverage support
option(ENABLE_COVERAGE "Enable coverage instrumentation" OFF)
if(ENABLE_COVERAGE AND NOT MSVC)
    add_compile_options(--coverage -O0 -g)
    add_link_options(--coverage)
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

# Helpful messages
message(STATUS "-----------------------------------------------------------")
message(STATUS "  {{PROJECT_NAME}} Configuration Complete")
message(STATUS "  - Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  - Testing:    ${BUILD_TESTING}")
message(STATUS "  - Coverage:   ${ENABLE_COVERAGE}")
message(STATUS "-----------------------------------------------------------")
message(STATUS "💡 TIP: Use './script/auto_run.ps1' for one-click build & test.")
message(STATUS "-----------------------------------------------------------")
