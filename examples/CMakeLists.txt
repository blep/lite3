

file(GLOB_RECURSE EXAMPLE_SRCS "*.c")

foreach(example_src ${EXAMPLE_SRCS})
    get_filename_component(example_name ${example_src} NAME_WE)
    get_filename_component(example_dir ${example_src} DIRECTORY)
    get_filename_component(example_dir_name ${example_dir} NAME)
    
    # Prefix example target names with directory to avoid conflicts
    set(example_target "example_${example_dir_name}_${example_name}")
    
    add_executable(${example_target} ${example_src})
    target_link_libraries(${example_target} PRIVATE lite3)
    
    # Group examples in solution folders by directory
    source_group("Source Files" FILES ${example_src})
    set_property(TARGET ${example_target} PROPERTY FOLDER "examples/${example_dir_name}")
endforeach()
