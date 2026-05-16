import subprocess
import random
import time
import logging
import cv2
import numpy as np
from datetime import datetime

# Importations Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle

try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format='%(message)s')

class BossOpenCVVision:
    def __init__(self):
        self.last_gray_frame = None

    def get_clean_frame(self):
        try:
            process = subprocess.Popen(['screencap', '-p'], stdout=subprocess.PIPE)
            img_data, _ = process.communicate()
            if not img_data:
                return None
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logging.error(f"[VISION ERROR] : {e}")
            return None

    def check_state(self):
        frame = self.get_clean_frame()
        if frame is None: return "ERREUR"
        
        h, w, _ = frame.shape
        roi = frame[int(h*0.35):int(h*0.60), int(w*0.20):int(w*0.80)]
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.last_gray_frame is None:
            self.last_gray_frame = gray_blurred
            return "STABLE"
            
        frame_delta = cv2.absdiff(self.last_gray_frame, gray_blurred)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        self.last_gray_frame = gray_blurred
        
        if np.sum(thresh) > 10000:
            return "ACTIF"
        return "STABLE"

class BossCrashApp(App):
    def build(self):
        self.vision = BossOpenCVVision()
        self.base_bet = 200     
        self.current_bet = 200
        self.robot_active = False
        self.game_state = "ATTENTE"
        
        Window.clearcolor = get_color_from_hex('#001f3f')
        self.root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.root.add_widget(Label(
            text="BOSS CRASH v8.6 - OPENCV", font_size='24sp', bold=True,
            color=get_color_from_hex('#D4AF37'), size_hint_y=0.1
        ))
        
        self.display_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
        with self.display_box.canvas.before:
            Color(rgb=get_color_from_hex('#D4AF37'))
            self.rect = RoundedRectangle(pos=self.display_box.pos, size=self.display_box.size, radius=[20,])
            self.display_box.bind(pos=self._update_rect, size=self._update_rect)
            
        self.multiplier_label = Label(text="SCANNING", font_size='50sp', bold=True, color=get_color_from_hex('#001f3f'))
        self.display_box.add_widget(self.multiplier_label)
        self.root.add_widget(self.display_box)

        self.stats_panel = BoxLayout(size_hint_y=0.1)
        self.info_label = Label(text=f"MISE: {self.base_bet}", color=get_color_from_hex('#D4AF37'), bold=True)
        self.stats_panel.add_widget(self.info_label)
        self.root.add_widget(self.stats_panel)
        
        self.scroll = ScrollView(size_hint_y=0.35)
        self.log_txt = Label(
            text="[SYSTEM] Protocole OpenCV activé.\\n",
            color=get_color_from_hex('#D4AF37'), size_hint_y=None, halign='left', valign='top',
            text_size=(Window.width - 40, None), font_size='13sp'
        )
        self.log_txt.bind(texture_size=self.log_txt.setter('size'))
        self.scroll.add_widget(self.log_txt)
        self.root.add_widget(self.scroll)
        
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        self.btn_start = Button(text="START ENGINE", background_color=get_color_from_hex('#D4AF37'), color=(0,0,0,1), bold=True)
        self.btn_start.bind(on_release=self.activate_robot)
        btns.add_widget(self.btn_start)
        self.root.add_widget(btns)
        
        return self.root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def add_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_txt.text += f"[{ts}] {msg}\\n"
        self.scroll.scroll_y = 0

    def engine_step(self, dt):
        if not self.robot_active: return
        state = self.vision.check_state()
        
        if state == "ACTIF" and self.game_state == "ATTENTE":
            self.game_state = "EN_COURS"
            self.add_log("[VISION] Mouvement détecté.")
        elif state == "STABLE" and self.game_state == "EN_COURS":
            self.game_state = "FINALISATION"
            subprocess.run(['input', 'tap', '840', '1000'])
            self.current_bet = self.base_bet
            self.add_log(f"[ACTION] Clic injecté (840, 1000). Mise : 200.")
            self.game_state = "ATTENTE"

    def activate_robot(self, instance):
        self.robot_active = True
        self.add_log("MOTEUR OPENCV EN ROUTE.")
        Clock.schedule_interval(self.engine_step, 0.4)

if __name__ == "__main__":
    BossCrashApp().run()
