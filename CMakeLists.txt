cmake_minimum_required(VERSION 3.14)

project(lite3
    VERSION 1.0.0
    DESCRIPTION "A JSON-Compatible Zero-Copy Serialization Format"
    HOMEPAGE_URL "https://lite3.io"
    LANGUAGES C
)

# Options
option(LITE3_ENABLE_JSON "Enable JSON support (includes yyjson and nibble_base64)" ON)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    option(LITE3_BUILD_EXAMPLES "Build examples" ON)
    option(LITE3_BUILD_TESTS "Build tests" ON)
else()
    option(LITE3_BUILD_EXAMPLES "Build examples" OFF)
    option(LITE3_BUILD_TESTS "Build tests" OFF)
endif()

# Core Library
add_library(lite3 STATIC
    src/lite3.c
    src/json_dec.c
    src/json_enc.c
)

add_library(lite3::lite3 ALIAS lite3)

target_include_directories(lite3
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        lib
)

target_compile_features(lite3 PUBLIC c_std_99)

# JSON Support
if(LITE3_ENABLE_JSON)
    target_sources(lite3 PRIVATE
        lib/yyjson/yyjson.c
        lib/nibble_base64/base64.c
    )
    # Note: Symbol hiding (prefixing third-party libraries) is not currently implemented in CMake.
    # This differs from the Makefile which uses `objcopy`.
    # This might cause symbol collisions if `lite3` is linked statically alongside other versions of `yyjson` or `base64`.
else()
    # If JSON is disabled, users must ensure LITE3_JSON is not defined in include/lite3.h
    # or handle preprocessor definitions appropriately if we were defining it here.
    # Current design relies on include/lite3.h settings.
endif()

if(MSVC)
    target_compile_options(lite3 PRIVATE /std:c11 /W4 /FI"${CMAKE_CURRENT_SOURCE_DIR}/cmake/msvc_compat.h")
else()
    target_compile_options(lite3 PRIVATE -Wall -Wextra)
endif()

# Installation
include(GNUInstallDirs)

install(TARGETS lite3
    EXPORT lite3Targets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(FILES
    include/lite3.h
    include/lite3_context_api.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# Export Configuration
install(EXPORT lite3Targets
    FILE lite3Targets.cmake
    NAMESPACE lite3::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lite3
)

include(CMakePackageConfigHelpers)
write_basic_package_version_file(
    lite3ConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/lite3Config.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/lite3Config.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lite3
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/lite3Config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/lite3ConfigVersion.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lite3
)

# pkg-config generation
configure_file(lite3.pc.in lite3.pc @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/lite3.pc" DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig)

# Subdirectories
if(LITE3_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(LITE3_BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
