cmake_minimum_required(VERSION 3.14)

include(FetchContent)
 
{{GTEST_DECLARATION}}
 
# For Windows: prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable({{PROJECT_NAME}}_test {{PROJECT_NAME}}_test.cpp)
target_link_libraries({{PROJECT_NAME}}_test PRIVATE {{PROJECT_NAME}} GTest::gtest_main)
target_include_directories({{PROJECT_NAME}}_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../inc)

include(GoogleTest)
gtest_discover_tests({{PROJECT_NAME}}_test)
