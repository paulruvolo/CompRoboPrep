# The set of languages for which implicit dependencies are needed:
SET(CMAKE_DEPENDS_LANGUAGES
  "C"
  )
# The set of files for implicit dependencies of each language:
SET(CMAKE_DEPENDS_CHECK_C
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiCLI.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiCLI.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiCamControl.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiCamControl.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiPreview.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiPreview.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiStill.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiStill.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiTex.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiTex.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/RaspiTexUtil.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/RaspiTexUtil.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/mirror.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/mirror.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/models.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/models.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/sobel.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/sobel.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/square.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/square.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/teapot.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/teapot.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/gl_scenes/yuv.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/gl_scenes/yuv.c.o"
  "/home/pi/userland/host_applications/linux/apps/raspicam/tga.c" "/home/pi/userland/build/raspberry/release/host_applications/linux/apps/raspicam/CMakeFiles/raspistill.dir/tga.c.o"
  )
SET(CMAKE_C_COMPILER_ID "GNU")

# Preprocessor definitions for this target.
SET(CMAKE_TARGET_DEFINITIONS
  "_HAVE_SBRK"
  "_LARGEFILE64_SOURCE"
  "HAVE_CMAKE_CONFIG"
  "HAVE_VMCS_CONFIG"
  "_REENTRANT"
  "USE_VCHIQ_ARM"
  "VCHI_BULK_ALIGN=1"
  "VCHI_BULK_GRANULARITY=1"
  "OMX_SKIP64BIT"
  "EGL_SERVER_DISPMANX"
  "_LARGEFILE_SOURCE"
  "_LARGEFILE64_SOURCE"
  "_FILE_OFFSET_BITS=64"
  "__VIDEOCORE4__"
  "TV_SUPPORTED_MODE_NO_DEPRECATED"
  )

# Targets to which this target links.
SET(CMAKE_TARGET_LINKED_INFO_FILES
  "/home/pi/userland/build/raspberry/release/interface/mmal/core/CMakeFiles/mmal_core.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/mmal/util/CMakeFiles/mmal_util.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/mmal/vc/CMakeFiles/mmal_vc_client.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/vcos/pthreads/CMakeFiles/vcos.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/host_applications/linux/libs/bcm_host/CMakeFiles/bcm_host.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/khronos/CMakeFiles/GLESv2.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/khronos/CMakeFiles/EGL.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/host_applications/linux/libs/sm/CMakeFiles/vcsm.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/vmcs_host/CMakeFiles/vchostif.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/vmcs_host/linux/vcfiled/CMakeFiles/vcfiled_check.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/vchiq_arm/CMakeFiles/vchiq_arm.dir/DependInfo.cmake"
  "/home/pi/userland/build/raspberry/release/interface/khronos/CMakeFiles/khrn_client.dir/DependInfo.cmake"
  )

# The include file search paths:
SET(CMAKE_C_TARGET_INCLUDE_PATH
  "../../inc"
  "../../../host_applications/framework"
  "../../.."
  "../../../interface/vcos/pthreads"
  "../../../interface/vmcs_host/linux"
  "../../../interface/vmcs_host"
  "../../../interface/vmcs_host/khronos"
  "../../../interface/khronos/include"
  "."
  "../../../interface/vchiq_arm"
  "../../../host_support/include"
  "../../../interface/mmal"
  "../../../host_applications/linux/libs/bcm_host/include"
  "../../../host_applications/linux/apps/raspicam"
  )
SET(CMAKE_CXX_TARGET_INCLUDE_PATH ${CMAKE_C_TARGET_INCLUDE_PATH})
SET(CMAKE_Fortran_TARGET_INCLUDE_PATH ${CMAKE_C_TARGET_INCLUDE_PATH})
SET(CMAKE_ASM_TARGET_INCLUDE_PATH ${CMAKE_C_TARGET_INCLUDE_PATH})
