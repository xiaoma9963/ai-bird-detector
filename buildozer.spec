# ========================================
# AI 智能驱鸟器 - Buildozer 配置文件
# 用途：打包安卓 APK 用于专利原型测试
# ========================================

[app]

# 应用标题
title = AI 智能驱鸟器

# 包名
package.name = birddetector

# 包域名（Android/IOS 打包需要）
package.domain = org.patent

# 源码目录
source.dir = .

# 包含的文件类型
source.include_exts = py,png,jpg,kv,atlas,json,mp3,wav

# 应用版本
version = 1.0.0

# 依赖库（轻量级配置，适合手机）
requirements = python3,kivy,opencv-python,torch,pillow,numpy

# 应用图标
#icon.filename = %(source.dir)s/icon.png

# 启动画面
#presplash.filename = %(source.dir)s/presplash.png

# 屏幕方向（竖屏）
orientation = portrait

# 全屏模式
fullscreen = 0

# ---------------------------
# Android 专用配置
# ---------------------------

# 权限：摄像头、振动、闪光灯
android.permissions = CAMERA,VIBRATE,FLASHLIGHT

# 目标 Android API（Android 13）
android.api = 33

# 最低支持 Android API（Android 5.0）
android.minapi = 21

# Android NDK 版本
android.ndk = 25b

# 跳过 SDK 更新（加快编译）
android.skip_update = False

# 自动接受 SDK 许可
android.accept_sdk_license = True

# 支持的 CPU 架构
android.archs = arm64-v8a, armeabi-v7a

# 允许数据备份
android.allow_backup = True

# 应用元数据
android.meta_data = com.google.android.gms.car.application=org.patent.birddetector

# ---------------------------
# 编译优化
# ---------------------------

# 启用编译优化
android.enable_androidx = True

# 使用 Gradle 构建
android.gradle_dependencies = 

# 最小化 APK 大小
android.release_artifact = aab

[buildozer]

# 日志级别（0=错误, 1=信息, 2=调试）
log_level = 2

# root 用户警告
warn_on_root = 1

# 构建目录
build_dir = ./.buildozer

# 输出目录
bin_dir = ./bin
