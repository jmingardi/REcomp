cmake_minimum_required(VERSION 3.20)
project(ResidentEvilRecomp LANGUAGES C CXX)

set(PSXRECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/third_party/psxrecomp" CACHE PATH
    "Pinned PSXRecomp checkout")
if(NOT EXISTS "${PSXRECOMP_ROOT}/runtime/runtime.cmake")
    message(FATAL_ERROR "Run python scripts/project.py bootstrap first")
endif()

# Establish the original single-player presentation before adding enhancements.
set(RECOMP_UI_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/third_party/recomp-ui" CACHE PATH
    "Pinned shared launcher and in-game settings" FORCE)
set(PSX_RECOMP_UI ON CACHE BOOL "Controller, keybind and display settings" FORCE)
set(PSX_NETPLAY OFF CACHE BOOL "Single-player game" FORCE)
set(PSX_REWIND OFF CACHE BOOL "Keep initial bring-up minimal" FORCE)
set(PSX_ENABLE_VULKAN OFF CACHE BOOL "Qualify OpenGL first" FORCE)
option(RE1_QA_TOOLS "Enable upstream local debugging for bring-up" OFF)
set(PSX_DEBUG_TOOLS ${RE1_QA_TOOLS} CACHE BOOL "Development diagnostics" FORCE)
set(PSXRECOMP_REQUIRE_GAME_C ON CACHE BOOL "Never build a BIOS-only setup host" FORCE)
set(PSXRECOMP_BIOS_STEMS OpenBIOS CACHE STRING "Use bundled open-source BIOS" FORCE)
set(PSX_PGXP_VARIANT OFF CACHE BOOL "Qualify the original renderer first" FORCE)
include("${PSXRECOMP_ROOT}/runtime/runtime.cmake")

psxrecomp_add_game_runtime(psx-runtime
    GAME_OVERLAY_STATIC_C "${CMAKE_CURRENT_SOURCE_DIR}/generated/overlays_static.c"
    PRELOADED_MODS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded"
    WINDOW_TITLE "Resident Evil Recompiled"
    DEFAULT_GAME_CONFIG_PATH "game.toml"
    MAX_PLAYERS 1
    GEN_MARKER "generated/SLUS_001.70_dispatch.c"
    GEN_FULL_GLOB "generated/SLUS_001.70_full_*.c"
)
target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src/settings_menu.cpp")
target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src/smooth_motion.cpp")

set(RE1_RELEASE_VERSION "" CACHE STRING "Optional local Windows release version (major.minor.patch)")
if(WIN32 AND NOT RE1_RELEASE_VERSION STREQUAL "")
    if(NOT RE1_RELEASE_VERSION MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
        message(FATAL_ERROR "RE1_RELEASE_VERSION must be major.minor.patch")
    endif()
    enable_language(RC)
    string(REPLACE "." "," RE1_WINDOWS_VERSION "${RE1_RELEASE_VERSION}")
    configure_file("src/windows_version.rc.in" "windows_version.rc" @ONLY)
    target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/windows_version.rc")
endif()

if(MSVC AND CMAKE_C_COMPILER_ID STREQUAL "MSVC")
    # MSVC requires an explicit opt-in for the runtime's C11 atomic sources.
    foreach(_source audio_trace.c gpu_gl_renderer.c guest_tty.c host_overlay.c
                    host_span_ring.c render_thread.c starvation_ring.c)
        set_property(SOURCE "${PSXRECOMP_ROOT}/runtime/src/${_source}"
            APPEND PROPERTY COMPILE_OPTIONS /experimental:c11atomics)
    endforeach()
endif()

if(RE1_QA_TOOLS)
    set_property(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/src/settings_menu.cpp"
        APPEND PROPERTY COMPILE_DEFINITIONS RE1_QA_TOOLS=1)
    target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/qa/host_input_probe.cpp")
    target_include_directories(psx-runtime PRIVATE
        "${PSXRECOMP_ROOT}/runtime/third_party/json11")
endif()
