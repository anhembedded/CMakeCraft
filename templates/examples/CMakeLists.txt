cmake_minimum_required(VERSION 3.14)

add_executable({{PROJECT_NAME}}_example {{PROJECT_NAME}}_main.cpp)
target_link_libraries({{PROJECT_NAME}}_example PRIVATE {{PROJECT_NAME}})
