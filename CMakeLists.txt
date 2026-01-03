cmake_minimum_required(VERSION 3.10)
project(FoodProcessing)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_compile_options(-Wall -Wextra -Wpedantic)

if (WIN32)
    set(OpenCL_INCLUDE_DIR "C://opencl/OpenCL-SDK/install/include")
    set(OpenCL_LIBRARY "C://opencl/OpenCL-SDK/install/lib/OpenCL.lib")
endif()

# Find OpenCL
find_package(OpenCL REQUIRED)

set(JSON_INCLUDE_DIR ${CMAKE_BINARY_DIR}/include)

file(MAKE_DIRECTORY ${JSON_INCLUDE_DIR})

set(JSON_URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.hpp)
set(JSON_FILE ${JSON_INCLUDE_DIR}/json.hpp)

if (NOT EXISTS ${JSON_FILE})
    message(STATUS "Downloading nlohmann/json single header...")
    file(DOWNLOAD ${JSON_URL} ${JSON_FILE} SHOW_PROGRESS)
endif()

# Add executable
add_executable(main main.cpp)

# Link Winsock on Windows
if(WIN32)
    target_link_libraries(main ws2_32)
endif()

target_link_libraries(main OpenCL::OpenCL)
target_include_directories(main PRIVATE ${OpenCL_INCLUDE_DIRS} ${JSON_INCLUDE_DIR})

configure_file(${CMAKE_SOURCE_DIR}/data1.json ${CMAKE_BINARY_DIR}/data1.json COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/data2.json ${CMAKE_BINARY_DIR}/data2.json COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/data3.json ${CMAKE_BINARY_DIR}/data3.json COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/data4.json ${CMAKE_BINARY_DIR}/data4.json COPYONLY)

configure_file(${CMAKE_SOURCE_DIR}/kernel.cl ${CMAKE_BINARY_DIR}/kernel.cl COPYONLY)