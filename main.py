"""
AI 识鸟 App - 驱鸟器原型测试版
功能：识别鸟类 → 报警 + 模拟激光驱赶
用途：专利原型演示
使用 OpenCV DNN 替代 PyTorch，无需下载大模型
"""
import os
import cv2
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image

# ==================== 配置参数 ====================
DETECT_EVERY = 5          # 每5帧检测一次
CONFIDENCE_THRESHOLD = 0.3  # 置信度阈值（降低以提高检测率）
ALARM_DURATION = 3         # 报警持续时间（秒）

# ImageNet 鸟类类别索引（MobileNet SSD 的鸟类类别）
# COCO 数据集中的鸟类类别是 14（bird）
BIRD_CLASS_ID = 14


class BirdDetectorApp(App):
    """AI 识鸟 App 主类"""

    def build(self):
        """构建界面"""
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # 顶部标题栏
        title_bar = BoxLayout(size_hint=(1, 0.08))
        self.title_label = Label(
            text='AI 智能驱鸟器 - 原型测试',
            font_size='20sp',
            bold=True
        )
        title_bar.add_widget(self.title_label)
        self.layout.add_widget(title_bar)

        # 摄像头画面区域
        self.image = Image(size_hint=(1, 0.72), allow_stretch=True)
        self.layout.add_widget(self.image)

        # 状态信息栏
        info_bar = BoxLayout(size_hint=(1, 0.12), orientation='vertical', spacing=3)

        self.bird_label = Label(
            text='鸟类: 未检测',
            font_size='16sp',
            size_hint=(1, 0.5),
            halign='left',
