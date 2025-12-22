
file(GLOB EXAMPLE_SRCS "*.c")

foreach(example_src ${EXAMPLE_SRCS})
    get_filename_component(example_name ${example_src} NAME_WE)
    
    # Prefix example target names to avoid potential conflicts
    set(example_target "example_${example_name}")
    
    add_executable(${example_target} ${example_src})
    target_link_libraries(${example_target} PRIVATE lite3)
endforeach()
