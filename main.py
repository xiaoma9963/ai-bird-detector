"""
AI 识鸟 App - 驱鸟器原型测试版
功能：识别鸟类 → 报警 + 模拟激光驱赶
用途：专利原型演示
"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
import cv2
import torch
import numpy as np
from PIL import Image as PILImage

# ==================== 配置参数 ====================
DETECT_EVERY = 5          # 每5帧检测一次
CONFIDENCE_THRESHOLD = 0.5 # 置信度阈值
ALARM_DURATION = 3         # 报警持续时间（秒）

# ImageNet 鸟类类别索引（正确的鸟类范围）
# 80-100: 鸡、鸭、鹅等家禽
# 12-24: 部分鸟类
# 完整鸟类列表见：https://deeplearning.cms.waikato.ac.nz/user-guide/class-maps/IMAGENET/
BIRD_CLASSES = set(range(80, 101)) | set(range(12, 25)) | set(range(7, 18))

# 中文鸟名映射（常见鸟类）
BIRD_NAMES_CN = {
    7: "鱼雷鸟", 8: "公鸡", 9: "母鸡", 10: "鸵鸟",
    11: "雷鸟", 12: "金丝雀", 13: "乌鸦", 14: "鸽子",
    80: "黑天鹅", 81: "白喉鹊鸲", 82: "松鸦", 83: "喜鹊",
    84: "蓝鸟", 85: "鹪鹩", 86: "知更鸟", 87: "鹬鸟",
    88: "松鸡", 89: "鹦鹉", 90: "啄木鸟", 91: "猫头鹰",
    92: "蜂鸟", 93: "翠鸟", 94: "杜鹃", 95: "啄木鸟",
    96: "鹰", 97: "雕", 98: "猫头鹰", 99: "鹅", 100: "鸭"
}


class BirdDetectorApp(App):
    """AI 识鸟 App 主类"""

    def build(self):
        """构建界面"""
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # 顶部标题栏
        title_bar = BoxLayout(size_hint=(1, 0.08))
        self.title_label = Label(
            text='🦅 AI 智能驱鸟器 - 原型测试',
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
            valign='middle'
        )
        self.bird_label.bind(size=self.bird_label.setter('text_size'))

        self.status_label = Label(
            text='状态: 正在初始化...',
            font_size='14sp',
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            color=(0.5, 0.5, 0.5, 1)
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))

        info_bar.add_widget(self.bird_label)
        info_bar.add_widget(self.status_label)
        self.layout.add_widget(info_bar)

        # 底部控制按钮
        btn_bar = BoxLayout(size_hint=(1, 0.08), spacing=10)

        self.alarm_btn = Button(
            text='🔊 测试报警',
            font_size='16sp',
            disabled=True
        )
        self.alarm_btn.bind(on_press=self.test_alarm)
        btn_bar.add_widget(self.alarm_btn)

        self.laser_btn = Button(
            text='⚡ 测试激光',
            font_size='16sp',
            disabled=True
        )
        self.laser_btn.bind(on_press=self.test_laser)
        btn_bar.add_widget(self.laser_btn)

        self.layout.add_widget(btn_bar)

        # 初始化变量
        self.model_loaded = False
        self.cap = None
        self.frame_num = 0
        self.bird_detected = False
        self.alarm_active = False
        self.detection_count = 0

        # 延迟加载模型
        Clock.schedule_once(self.load_model, 0.5)

        return self.layout

    def load_model(self, dt):
        """加载 AI 模型"""
        try:
            self.status_label.text = '⏳ 正在加载 AI 模型...'

            # 使用 MobileNetV3 轻量级模型（适合手机）
            self.model = torch.hub.load(
                'pytorch/vision:v0.10.0',
                'mobilenet_v3_small',
                pretrained=True
            )
            self.model.eval()

            # 图像预处理
            from torchvision import transforms
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])

            self.model_loaded = True
            self.status_label.text = '✅ 模型加载完成，正在打开摄像头...'

            # 打开摄像头
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            if self.cap.isOpened():
                self.status_label.text = '✅ 摄像头已就绪，对准鸟类测试！'
                self.alarm_btn.disabled = False
                self.laser_btn.disabled = False
                Clock.schedule_interval(self.update_frame, 0.05)  # 20 FPS
            else:
                self.status_label.text = '❌ 无法打开摄像头，请检查权限'
                self.status_label.color = (1, 0, 0, 1)

        except Exception as e:
            self.status_label.text = f'❌ 加载失败: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)

    def detect_bird(self, frame):
        """检测画面中的鸟类"""
        try:
            # 转换图像格式
            img = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tensor = self.transform(img).unsqueeze(0)

            # AI 推理
            with torch.no_grad():
                output = self.model(tensor)
                probs = torch.nn.functional.softmax(output[0], dim=0)
                confidence, pred = torch.max(probs, 0)
                pred = pred.item()
                confidence = confidence.item()

            # 检查是否为鸟类
            is_bird = pred in BIRD_CLASSES and confidence > CONFIDENCE_THRESHOLD

            if is_bird:
                bird_name = BIRD_NAMES_CN.get(pred, f"鸟类#{pred}")
                return True, bird_name, confidence

            return False, None, confidence

        except Exception as e:
            print(f"检测错误: {e}")
            return False, None, 0.0

    def update_frame(self, dt):
        """更新摄像头画面"""
        if not self.cap or not self.cap.isOpened():
            return

        ok, frame = self.cap.read()
        if not ok:
            return

        self.frame_num += 1
        display_frame = frame.copy()

        # 每5帧检测一次
        if self.frame_num % DETECT_EVERY == 0:
            is_bird, bird_name, confidence = self.detect_bird(frame)

            if is_bird:
                self.bird_detected = True
                self.detection_count += 1

                # 更新显示
                self.bird_label.text = f'🐦 检测到: {bird_name} ({confidence*100:.1f}%)'
                self.bird_label.color = (1, 0.3, 0, 1)  # 橙色

                # 触发报警和激光驱赶
                self.trigger_alarm(bird_name)
                self.trigger_laser(display_frame)

            else:
                self.bird_detected = False
                self.bird_label.text = '鸟类: 未检测'
                self.bird_label.color = (0.3, 0.8, 0.3, 1)  # 绿色
                self.status_label.text = f'状态: 监控中... (帧: {self.frame_num})'
                self.status_label.color = (0.5, 0.5, 0.5, 1)

        # 显示画面
        self.display_frame(display_frame)

    def trigger_alarm(self, bird_name):
        """触发报警"""
        if not self.alarm_active:
            self.alarm_active = True
            self.status_label.text = f'🚨 报警！检测到 {bird_name}！'
            self.status_label.color = (1, 0, 0, 1)

            # 模拟报警声（实际设备会触发蜂鸣器）
            print(f"🔔 报警: 检测到 {bird_name}")

            # 3秒后停止报警
            Clock.schedule_once(self.stop_alarm, ALARM_DURATION)

    def stop_alarm(self, dt):
        """停止报警"""
        self.alarm_active = False
        self.status_label.text = '状态: 监控中...'

    def trigger_laser(self, frame):
        """触发激光驱赶（模拟）"""
        # 在画面上显示激光效果（实际设备会发射真实激光）
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)

        # 绘制红色激光点
        cv2.circle(frame, center, 20, (0, 0, 255), -1)
        cv2.circle(frame, center, 25, (0, 0, 255), 2)

        # 添加激光光束效果
        cv2.line(frame, (0, h), center, (0, 0, 255), 2)
        cv2.line(frame, (w, h), center, (0, 0, 255), 2)

        # 添加文字提示
        cv2.putText(
            frame, "⚡ LASER ACTIVE", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
        )

    def display_frame(self, frame):
        """显示画面到界面"""
        # OpenCV BGR -> Kivy 纹理
        buf = cv2.flip(frame, 0).tostring()
        texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt='bgr'
        )
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture

    def test_alarm(self, instance):
        """测试报警功能"""
        self.status_label.text = '🔊 报警测试中...'
        self.status_label.color = (1, 0.5, 0, 1)

        # 3秒后恢复
        Clock.schedule_once(lambda dt: setattr(
            self.status_label, 'text', '✅ 报警测试完成'
        ), 2)

    def test_laser(self, instance):
        """测试激光功能"""
        if self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                self.trigger_laser(frame)
                self.display_frame(frame)
                self.status_label.text = '⚡ 激光测试完成'
                self.status_label.color = (0, 0.5, 1, 1)

    def on_stop(self):
        """应用退出时清理资源"""
        if self.cap:
            self.cap.release()
        print("应用已关闭")


if __name__ == '__main__':
    BirdDetectorApp().run()
