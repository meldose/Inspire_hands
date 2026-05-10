cmake_minimum_required(VERSION 3.10)  

# Set the project name and version
project(HandAPI VERSION 1.0 LANGUAGES C CXX)  

# Find the pthread library
find_package(Threads REQUIRED)  

# Build the C static library
 add_library(hand_api STATIC hand_api.c)  

# Build the C++ test executable
add_executable(test test.cpp hand_api.c)  

# Link pthread and hand_api into the test executable
 target_link_libraries(test PRIVATE hand_api Threads::Threads)  

# # Set the C and C++ language standards
# set_target_properties(hand_api PROPERTIES  
#     C_STANDARD 11  
#     C_STANDARD_REQUIRED True  
# )  

# set_target_properties(test PROPERTIES  
#     CXX_STANDARD 11  
#     CXX_STANDARD_REQUIRED True  
# )  

# Remind the user to update the serial port and hand ID
message(STATUS "请在 hand_api.c 中修改 ttyUSB0 为实际串口USB名，以及对于手的ID。")
