# pyinstaller Build 명령어: pyinstaller --noconfirm --windowed --add-data "Images;Images" main.py
import sys
import json
import time
import os
from PyQt6.QtWidgets import (QScrollArea, 
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider, QInputDialog, QStackedLayout, QLineEdit, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt, QSize, Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon
from definer import SEIIdv
import dropbox

e = 0
SAVE_PATH = "settings.json"
DEFAULT_SETTINGS = {
    'ExpR': 0.6, 'InfR': 5, 'DthR': 0.003, 'RcvR': 0.1,
    'VcnR': 0, 'rILR': 0.005, 'vILR': 0.01,
    'VcnS': 1,
    'distancing_days': [30, 70, 130],
    'distancing_exprs': [0.5, 0.3, 0.1],
    'cure_days': 30,
    'overcome_limit': 0.0001,
    'vaccine_s': 100,
    'cue_s': 30
}

ACCESS_TOKEN = ""

import requests
import dropbox
import time
import os

APP_KEY = ''
APP_SECRET = ''
REFRESH_TOKEN = ''

def get_access_token():
    url = 'https://api.dropbox.com/oauth2/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': APP_KEY,
        'client_secret': APP_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    tokens = response.json()
    return tokens['access_token']

def upload_timestamped_json(local_path, dropbox_folder):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

    basename = os.path.splitext(os.path.basename(local_path))[0]
    timestamp = time.strftime('%y%m%d%H%M%S')
    filename = f"{basename}_{timestamp}.json"
    dropbox_path = f"/{dropbox_folder}/{filename}"

    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.add)

    print(f"업로드 완료: {local_path} -> {dropbox_path}")

def download_file(dropbox_path, local_path):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

    metadata, res = dbx.files_download(path=dropbox_path)
    with open(local_path, "wb") as f:
        f.write(res.content)
    print(f"다운로드 완료: {dropbox_path} -> {local_path}")



LEADERBOARD_PATH = "leaderboard.json"
MAX_RANK = 10
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def load_leaderboard():
    if os.path.exists(LEADERBOARD_PATH):
        with open(LEADERBOARD_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_leaderboard(data):
    with open(LEADERBOARD_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_settings():
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, 'r') as f:
            settings = json.load(f)
    else:
        settings = DEFAULT_SETTINGS.copy()
    for key in DEFAULT_SETTINGS:
        if key not in settings:
            settings[key] = DEFAULT_SETTINGS[key]
    return settings


def save_settings(data):
    with open(SAVE_PATH, 'w') as f:
        json.dump(data, f)

class SettingPanel(QWidget):
    def __init__(self, settings, on_return):
        super().__init__()
        self.settings = settings
        self.on_return = on_return
        self.vaccine_days_active = 0
        self.cure_days_active = 0

        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon(QPixmap(resource_path("back_icon.png"))))
        self.back_button.setIconSize(self.back_button.iconSize())
        self.back_button.clicked.connect(self.apply_and_return)
        top_layout.addWidget(self.back_button)

        layout.addLayout(top_layout)

        # 텍스트 입력: vaccine_s, cue_s
        input_layout = QHBoxLayout()
        self.vaccine_input = QLineEdit(str(self.settings.get('vaccine_s', 100)))
        self.vaccine_input.setPlaceholderText("vaccine_s")
        self.vaccine_input.setFixedWidth(100)
        input_layout.addWidget(QLabel("백신 개발 일수:"))
        input_layout.addWidget(self.vaccine_input)

        self.cue_input = QLineEdit(str(self.settings.get('cue_s', 30)))
        self.cue_input.setPlaceholderText("cue_s")
        self.cue_input.setFixedWidth(100)
        input_layout.addWidget(QLabel("치료제 개발 일수:"))
        input_layout.addWidget(self.cue_input)

        layout.addLayout(input_layout)

        # 슬라이더들
        slider_row = QHBoxLayout()
        self.sliders = {}

        for key in ['ExpR', 'InfR', 'DthR', 'RcvR', 'VcnR', 'rILR', 'vILR']:
            col = QVBoxLayout()
            slider = QSlider(Qt.Orientation.Vertical)

            if key == 'InfR':
                slider.setMinimum(1)
                slider.setMaximum(100)
                slider.setValue(int(self.settings[key]))
                label = QLabel(f"{key}: {self.settings[key]:.0f}")
                slider.valueChanged.connect(lambda v, k=key, l=label: l.setText(f"{k}: {v}"))
            else:
                slider.setMinimum(1)
                slider.setMaximum(1000)
                slider.setValue(int(self.settings[key] * 1000))
                label = QLabel(f"{key}: {self.settings[key]:.3f}")
                slider.valueChanged.connect(lambda v, k=key, l=label: l.setText(f"{k}: {v/1000:.3f}"))

            slider.setStyleSheet("""
                QSlider::groove:vertical {
                    background: #ccc;
                    width: 18px;
                    border-radius: 9px;
                }
                QSlider::handle:vertical {
                    background: #be4ad7;
                    height: 40px;
                    margin: 0 -6px;
                    border-radius: 20px;
                }
            """)

            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label = QLabel(f"<b>{key}</b>")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(slider, stretch=1)
            col.addWidget(name_label)
            col.addWidget(label)
            slider_row.addLayout(col)
            self.sliders[key] = slider

        layout.addLayout(slider_row, stretch=1)
        self.setLayout(layout)

    def apply_and_return(self):
        for k, s in self.sliders.items():
            self.settings[k] = s.value() / 1000 if k != 'InfR' else s.value()

        # 텍스트박스 값도 저장
        try:
            self.settings['vaccine_s'] = int(self.vaccine_input.text())
        except ValueError:
            self.settings['vaccine_s'] = 100

        try:
            self.settings['cue_s'] = int(self.cue_input.text())
        except ValueError:
            self.settings['cue_s'] = 30

        save_settings(self.settings)
        self.on_return()
        self.hide()
        

class SEIIdvGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.value = self.settings.copy()
        self.setWindowTitle("SEIIdv: 감염자 0에 도전하라!")
        self.setGeometry(100, 100, 1800, 1000)
        self.setStyleSheet("background-color: #FFFDFA;")
        self.vaccine_log = {}  # 일차: 'On' 또는 'Off'
        self.cure_log = {}

        self.vaccine_days_active = 0
        self.cure_days_active = 0
        self.isRunning = False
        self.vaccineClicked = False
        self.cureClicked = False
        self.flash_state = False
        self.value['VcnS'] = self.settings.get('vaccine_s', 100)
        self.value['lim'] = 300  # 종식 판단 기준 (임계일)
        self.model = SEIIdv(Pop=5 * 10**7, Inf=3000, **self.value)
        self.e = 0

        self.main_widget = QWidget()
        self.setting_panel = SettingPanel(self.settings, self.show_main)

        self.stack_layout = QStackedLayout()
        self.stack_layout.addWidget(self.main_widget)
        self.stack_layout.addWidget(self.setting_panel)

        stack_container = QWidget()
        stack_container.setLayout(self.stack_layout)
        self.setCentralWidget(stack_container)

        self.vaccine_days_active = 0
        self.cure_days_active = 0

        # 리더보드 UI
        self.leaderboard_label = QLabel("🏆 리더보드")
        self.leaderboard_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.leaderboard_layout = QVBoxLayout()
        self.leaderboard_widgets = []


        self.initMainUI()
        self.startTimers()

        try:
            access_token = get_access_token()
            self.dbx = dropbox.Dropbox(access_token)
        except Exception as e:
            print(f"Dropbox 초기화 실패: {e}")
            self.dbx = None

    # Dropbox에서 최신 leaderboard 파일 다운로드하여 로컬 leaderboard.json로 저장
        try:
            entries = self.dbx.files_list_folder("/leaderboard").entries
            leaderboard_files = [e for e in entries if isinstance(e, dropbox.files.FileMetadata) and e.name.startswith("leaderboard_")]
            leaderboard_files.sort(key=lambda x: x.name, reverse=True)
            latest_file_path = f"/leaderboard/{leaderboard_files[0].name}" if leaderboard_files else None
        except Exception as e:
            print(f"❌ Dropbox 목록 불러오기 실패: {e}")
            latest_file_path = None

        if latest_file_path:
            try:
                metadata, res = self.dbx.files_download(path=latest_file_path)
                with open("leaderboard.json", "wb") as f:
                    f.write(res.content)
                print(f"✅ 최신 리더보드 파일 다운로드 완료: {latest_file_path} → leaderboard.json")
                self.update_leaderboard_display()
            except Exception as e:
                print(f"❌ 리더보드 다운로드 실패: {e}")


    def closeEvent(self, event):
        reply = QMessageBox.question(self, '종료 확인', '정말 창을 닫으시겠습니까?',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Dropbox에서 가장 최근 leaderboard_*.json 찾기
            try:
                entries = self.dbx.files_list_folder("/leaderboard").entries
                leaderboard_files = [e for e in entries if isinstance(e, dropbox.files.FileMetadata) and e.name.startswith("leaderboard_")]
                leaderboard_files.sort(key=lambda x: x.name, reverse=True)
                latest_file_path = f"/leaderboard/{leaderboard_files[0].name}" if leaderboard_files else None
            except Exception as e:
                print(f"❌ Dropbox 파일 목록 불러오기 실패: {e}")
                latest_file_path = None

            # timestamped 업로드
            import time
            timestamp = time.strftime('%y%m%d%H%M%S')
            upload_name = f"leaderboard_{timestamp}.json"
            dropbox_path = f"/leaderboard/{upload_name}"
            with open('leaderboard.json', "rb") as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.add)
            print(f"✅  리더보드 업로드 완료: {dropbox_path}")

            timestamp = time.strftime('%y%m%d%H%M%S')
            upload_name = f"playlog_{timestamp}.json"
            dropbox_path = f"/playlog/{upload_name}"
            with open('playlog.json', "rb") as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.add)
            print(f"✅  로그 업로드 완료: {dropbox_path}")

            # 5. 로컬 파일 삭제
            for filename in ["leaderboard.json", "playlog.json"]:
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"🧹 {filename} 삭제 완료")
                else:
                    print(f"⚠️ {filename} 없음")

            event.accept()
        else:
            event.ignore()



    def initMainUI(self):
        main_layout = QHBoxLayout(self.main_widget)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, stretch=5)
        main_layout.addLayout(right_layout, stretch=1)

        title_row = QHBoxLayout()

        title_label = QLabel()
        title_pixmap = QPixmap(resource_path(resource_path("Images/title.png")))
        title_label.setPixmap(title_pixmap)
        title_label.setFixedSize(1000, title_pixmap.height() * 1000 // title_pixmap.width())
        title_label.setScaledContents(True)
        title_row.addWidget(title_label)

        self.pause_button = QPushButton("Go")
        self.pause_button.setFixedSize(100, 130)
        self.pause_button.setFont(QFont("Arial", 60, QFont.Weight.Bold))
        self.pause_button.setStyleSheet("background-color: #be4ad7; color: white;")
        self.pause_button.clicked.connect(self.togglePause)
        title_row.addWidget(self.pause_button)

        self.reset_button = QPushButton("↻")
        self.reset_button.setFixedSize(100, 130)
        self.reset_button.setFont(QFont("Arial", 60, QFont.Weight.Bold))
        self.reset_button.setStyleSheet("background-color: #be4ad7; color: white;")
        self.reset_button.clicked.connect(self.resetGraph)
        title_row.addWidget(self.reset_button)

        left_layout.addLayout(title_row)

        # 감염자 수 표시
        self.infection_count = QLabel()
        self.infection_count.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.infection_count.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        left_layout.addWidget(self.infection_count)

        self.tip = QLabel()
        self.tip.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.tip.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(self.tip)
        self.tip.setText(f"- 비감염자, 감염자 등 간 상호작용으로 전염병의 확산을 예측하는 수학적 모델입니다.\n- 여러분의 플레이 기록은 과학적으로 매우 가치있으며, 관련 연구에 활용될 예정입니다.\n\ntip: [중요] 버튼을 계속 누르면 껐다 켤 수 있습니다!!\ntip: 적은 백신과 치료제로 단기간에 감염자를 줄이면 고득점이 가능합니다.\n프로그램 삭제는 문서->seiidv->unins000.exe를 실행하세요 :)\nContact: todguess@outlook.kr")

        self.canvas = self.model.init_graph(overComeLimit=self.settings['overcome_limit'], PopScale="천만", win=None)
        left_layout.addWidget(self.canvas, stretch=3)

        self.setting_button = QPushButton("Setting")
        self.setting_button.clicked.connect(self.show_settings)
        right_layout.addWidget(self.setting_button)

        self.vaccine_imgs = [resource_path("Images/VcnDev.png"), resource_path("Images/VcnRea.png"), resource_path("Images/VcnTak.png")]
        self.vaccine_button = QPushButton()
        self.vaccine_button.setIcon(QIcon(self.vaccine_imgs[0]))
        self.vaccine_button.setFixedSize(200, 140)
        self.vaccine_button.setIconSize(QSize(200, 200))
        self.vaccine_button.clicked.connect(self.activateVaccine)
        right_layout.addWidget(self.vaccine_button)

        self.vaccine_label = QLabel()
        self.vaccine_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.vaccine_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.vaccine_label)

        self.cure_imgs = [resource_path("Images/CurDev.png"), resource_path("Images/CurRea.png"), resource_path("Images/CurTak.png")]
        self.cure_button = QPushButton()
        self.cure_button.setIcon(QIcon(self.cure_imgs[0]))
        self.cure_button.setFixedSize(200, 140)
        self.cure_button.setIconSize(QSize(200, 200))
        self.cure_button.clicked.connect(self.activateCure)
        right_layout.addWidget(self.cure_button)

        self.cure_label = QLabel("치료제 개발까지 남은 일수:")
        self.cure_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.cure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.cure_label)

        self.vaccine_button.setEnabled(False)
        self.cure_button.setEnabled(False)
        # 스크롤 영역 추가
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.leaderboard_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(400)  # 적당한 높이로 고정
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right_layout.addWidget(self.leaderboard_label)
        right_layout.addWidget(scroll_area)
        self.update_leaderboard_display()


    def togglePause(self):
        self.isRunning = not self.isRunning
        self.pause_button.setText("⏸" if self.isRunning else "▶")

    def activateVaccine(self):
        if not self.vaccineClicked:
            self.value['VcnR'] = 0.1  # <- 추가
            self.model.update(VcnR=0.1)
            self.vaccineClicked = True
            self.vaccine_button.setIcon(QIcon(self.vaccine_imgs[2]))
            self.vaccine_label.setText("백신 접종 시작됨!")
            self.vaccine_log[self.model.days] = "On"
        else:
            self.value['VcnR'] = 0  # <- 추가
            self.model.update(VcnR=0)
            self.vaccineClicked = False
            self.vaccine_button.setIcon(QIcon(self.vaccine_imgs[1]))
            self.vaccine_label.setText("백신 접종 중단됨!")
            self.vaccine_log[self.model.days] = "Off"


    # 치료제 버튼 동작: 토글 방식으로 투여 시작/중단
    def activateCure(self):
        if not self.cureClicked:
            self.RcvRB = self.value['RcvR']
            self.model.update(RcvR=0.8)
            self.cureClicked = True
            self.cure_button.setIcon(QIcon(self.cure_imgs[2]))
            self.cure_label.setText("치료제 투여 시작됨!")
            self.cure_log[self.model.days] = "On"
        else:
            self.model.update(RcvR = self.RcvRB)
            self.cureClicked = False
            self.cure_button.setIcon(QIcon(self.cure_imgs[1]))
            self.cure_label.setText("치료제 접종 중단됨!")
            self.cure_log[self.model.days] = "Off"
    def show_settings(self):
        password, ok = QInputDialog.getText(self, "비밀번호 입력", "설정에 들어가려면 비밀번호를 입력하세요:", QLineEdit.EchoMode.Password)
        if ok and password == '299792458':
            self.stack_layout.setCurrentWidget(self.setting_panel)
        elif ok:
            QMessageBox.warning(self, "비밀번호 오류", "비밀번호가 올바르지 않습니다.")

    def show_main(self):
        self.stack_layout.setCurrentWidget(self.main_widget)

    def resetGraph(self):
        self.value['VcnS'] = self.settings.get('vaccine_s', 100)
        self.value['lim'] = 300
        # 모델 재생성
        self.model = SEIIdv(Pop=5 * 10**7, Inf=3000, **self.value)
        self.e = 0

        # 기존 캔버스 제거
        self.canvas.setParent(None)

        # 새 그래프 생성 및 표시
        self.canvas = self.model.init_graph(overComeLimit=self.settings['overcome_limit'], PopScale="천만", win=None)
        self.main_widget.layout().itemAt(0).layout().addWidget(self.canvas, stretch = 3)
        self.vaccineClicked = False
        self.cureClicked = False
        self.cure_button.setIcon(QIcon(resource_path('Images/CurDev.png')))
        self.cure_button.setEnabled(False)
        self.vaccine_button.setIcon(QIcon(resource_path('Images/VcnDev.png')))
        self.vaccine_button.setEnabled(False)

    def updateGraph(self):
        if self.isRunning:
            self.model.nextDay()
        self.model.update_graph()
        self.canvas.draw()
        self.infection_count.setText(f"현재 감염자 수: {self.model.I:,}")
        if self.model.I < 40: self.infection_count.setText(f"현재 감염자 수: 0")

        Vcndays_left = self.settings['vaccine_s']- self.model.days
        if not self.vaccineClicked:
            if Vcndays_left > 0:
                self.vaccine_label.setText(f"백신 개발까지 남은 일수: {Vcndays_left}")
            else:
                self.vaccine_label.setText("백신 개발됨!")
                self.vaccine_button.setIcon(QIcon(resource_path('Images/VcnRea.png')))
                self.vaccine_button.setEnabled(True)  # 개발 완료 후 활성화
        else:
            self.vaccine_label.setText("백신 접종 시작됨!")
            self.vaccine_button.setIcon(QIcon(resource_path('Images/VcnTak.png')))
        
        if self.vaccineClicked:
            self.vaccine_days_active += 1
        if self.cureClicked:
            self.cure_days_active += 1


        # updateGraph 혹은 update 상태에서 조건에 따라 활성화
        Curdays_left = self.settings['cue_s'] - self.model.days
        if not self.cureClicked:
            if Curdays_left > 0:
                self.cure_label.setText(f"치료제 개발까지 남은 일수: {Curdays_left}")
            else:
                self.cure_label.setText("치료제 개발됨!")
                self.cure_button.setIcon(QIcon(resource_path('Images/CurRea.png')))
                self.cure_button.setEnabled(True)  # 개발 완료 시 버튼 활성화
        elif Curdays_left <= 0:
            self.cure_label.setText("치료제 투여 시작됨!")
            self.cure_button.setIcon(QIcon(resource_path('Images/CurTak.png')))
        if self.model.I / self.model.sum() < self.settings['overcome_limit'] and not self.e and self.model.days > 500:
            self.e = 1

            vaccine_days = max(self.vaccine_days_active, 1)
            cure_days = max(self.cure_days_active, 1)
            deaths = max(self.model.D, 1)
            infected_scale = max(self.model.acuI / 10_000_000, 0.0001)

            score = 100000000000 / (vaccine_days + cure_days + deaths + infected_scale)

            # 1. 닉네임 입력
            name, ok1 = QInputDialog.getText(self, "🎉 축하합니다!", 
                f"감염병이 사실상 종식되었습니다!\n\n🎯 점수: {int(score):,}\n\n닉네임을 입력하세요. DB에 저장되며, 타인에게 보여지므로 실명을 입력하지 마세요.")

            # 2. 나이 입력
            age, ok2 = QInputDialog.getInt(self, "나이 입력", "나이를 입력해 주세요.", min=1, max=80)

            # 3. 성별 입력 (텍스트 입력 또는 선택 방식)
            gender, ok3 = QInputDialog.getItem(self, "성별 선택", "성별을 선택해 주세요.", ["남성", "여성"], editable=False)

            # 4. 모두 입력한 경우에만 저장
            if ok1 and name.strip() and ok2 and ok3:
                name = name.strip()
                # 1. leaderboard 저장 (이름, 점수, 시간만)
                leaderboard = load_leaderboard()
                leaderboard.append({
                    'name': name,
                    'score': score,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_leaderboard(leaderboard)
                self.update_leaderboard_display()

                # 2. playlog 저장 (나머지 모든 정보)
                playlog_path = "playlog.json"
                if os.path.exists(playlog_path):
                    with open(playlog_path, 'r', encoding='utf-8') as f:
                        playlog = json.load(f)
                else:
                    playlog = []

                playlog.append({
                    'name': name,
                    'age': age,
                    'gender': gender,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'settings': self.settings.copy(),
                    'vaccine_log': self.vaccine_log,
                    'cure_log': self.cure_log,
                    'graph_log': self.model.logList
                })

                with open(playlog_path, 'w', encoding='utf-8') as f:
                    json.dump(playlog, f, indent=2, ensure_ascii=False)
            




        if self.model.days > 2500 and not self.e:
            QMessageBox.critical(self, "실패", "2500일 경과 후에도 감염병을 잡아내지 못했습니다.\n감염병에 의해 인류는 큰 손실을 안게 되었습니다.")
            self.e = 1
            

    def startTimers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGraph)
        self.timer.start(1)

    def update_leaderboard_display(self):
        for widget in self.leaderboard_widgets:
            widget.deleteLater()
        self.leaderboard_widgets.clear()
        self.leaderboard_layout.setSpacing(2)

        board = load_leaderboard()
        board.sort(key=lambda x: x['score'], reverse=True)

        for i, entry in enumerate(board[:MAX_RANK], 1):
            timestamp = entry.get('timestamp', '시간없음')
            if i < 4:
                st, bgC, ftC = ['st', 'nd', 'rd'][i-1], ['red', 'blue', 'green'][i-1], 'white'
                bgC2, ftC2 = ['pink', 'skyblue', 'lightgreen'][i-1], 'black'
            else: st, bgC, ftC, bgC2, ftC2 = 'th', 'black', 'white', 'lightgrey', 'black'
            label = QLabel()
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(
                f"<span style='background-color:{bgC}; color:{ftC}; padding:2px;'>"
                f"<b><font size=+3>"+"     "+f"{i}</font>{st}   </b></span>"
                f"<span style='background-color:{bgC2}; color:{ftC2}; padding:2px;'>"
                f"<font size=+2> {entry['name']} </font></span><br>"
                f"<b><font size=+2>{int(entry['score']):,}</font>점</b> <br>({timestamp})<br>"
            )
            self.leaderboard_layout.addWidget(label)
            self.leaderboard_widgets.append(label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QMessageBox.information(None, "안내", "종료 시에는 반드시 \"창 오른쪽 위\"의 X를 눌러서 꺼 주세요.")
    gui = SEIIdvGUI()
    gui.show()
    sys.exit(app.exec())
