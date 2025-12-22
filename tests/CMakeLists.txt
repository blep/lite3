
file(GLOB TEST_SRCS "*.c")

foreach(test_src ${TEST_SRCS})
    get_filename_component(test_name ${test_src} NAME_WE)
    
    # Prefix test target names to avoid potential conflicts
    set(test_target "test_${test_name}")
    
    add_executable(${test_target} ${test_src})
    target_link_libraries(${test_target} PRIVATE lite3)
    
    # Register test with CTest (using the original name for the test itself if desired, or matching target)
    add_test(NAME ${test_name} COMMAND ${test_target})
endforeach()
