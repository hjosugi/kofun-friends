cmake_minimum_required(VERSION 3.18)
project(mound_breaker C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

option(KOFUN_FETCH_RAYLIB "Download raylib when it is not installed" OFF)
find_package(raylib 6.0 QUIET)

if(NOT raylib_FOUND AND KOFUN_FETCH_RAYLIB)
  include(FetchContent)
  set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    raylib
    GIT_REPOSITORY https://github.com/raysan5/raylib.git
    GIT_TAG 6.0
    GIT_SHALLOW TRUE
  )
  FetchContent_MakeAvailable(raylib)
endif()

if(NOT TARGET raylib)
  message(FATAL_ERROR
    "raylib 6.0 was not found. Install it or configure with "
    "-DKOFUN_FETCH_RAYLIB=ON.")
endif()

add_executable(mound_breaker src/main.c)
target_link_libraries(mound_breaker PRIVATE raylib)

add_custom_command(TARGET mound_breaker POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_CURRENT_SOURCE_DIR}/assets
          $<TARGET_FILE_DIR:mound_breaker>/assets)
