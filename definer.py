'''
[General File Information]
Created_On: yyyymmdd_20250513
Auther: 상무고등학교_1106김성현
Contact: 010-9873-1915
Description:
메인 파일에서 쓰이는 각종 모형 등 클래스, 함수를 선언하는 파일입니다!
최대한 주석을 달긴 했지만 주석을 꼼꼼하게 다는 건 처음이라 미흡할 수 있습니다
궁금증이 있으시면 갠톡으로 편하게 질문 주세요 :)
Copyrightⓒ2025 All rights reserved by 김성현
!!!!!!!! 폰트 ttf를 _internal/matplotlib/mpl-data/fonts/ttf에다가 넣어서 해결!!!!!!!!! 힘들었다
'''


import matplotlib.pyplot as plt   # 그래프를 시각화하는 라이브러리를 불러옵니다.
import matplotlib.font_manager as fm
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as QtCanvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as TkCanvas
import sys
import os


# 예외처리 클래스인 Exception에서 상속받은 클래스를 선언하며, 별도의 추가 요소를 지정하지 않습니다. Exeption의 메서드를 그대로 이용 가능합니다. 사용자 지정 오류를 출력할 수 있게 합니다.
class PopDoesNotMatch(Exception): pass   # 부동소숫점 오류 등의 이유로 모형의 연산 도중 인구의 총합이 맞지 않을 경우 출력할 오류입니다.   
class DaysTooLarge(Exception): pass   # 시뮬레이션 일수가 너무 길어질 경우 MemoryError를 미연에 방지하고자 출력할 오류입니다.

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        # PyInstaller가 내부 폴더 _internal에 리소스를 풀 경우도 처리
        internal_path = os.path.join(base_path, "_internal", relative_path)
        if os.path.exists(internal_path):
            return internal_path
        else:
            return os.path.join(base_path, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)

class SEIIdv:   # SEIIdv 클래스를 선언합니다.
    'SEIIdv 모형을 이용한 다양한 작업을 수행합니다.'   # docstring: 클래스나 함수에 마우스를 오버레이했을 때 띄울 설명을 쓸 수 있습니다.

    #__init은 클래스가 처음 만들어질 때에 한 번만 실행됩니다!
    def __init__(self, Pop: int, Inf: int, **kwargs):   # 인자의 자료형을 ':' 뒤에 강제합니다. **kwargs는 길이 미정 딕셔너리를 받습니다.
        font_path = resource_path("NanumGothic\\NanumGothic.ttf")
        font_prop = fm.FontProperties(fname=font_path)
        print("Font path used:", font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
        #kwargs 딕셔너리의 값들을 인스턴스에 할당해줍니다.
        self.ExpR = kwargs.get('ExpR')   # 일당 노출률 (다른 연구과의 통일성을 위해 일당 노출률이라는 단어를 사용했으나, 실제로는 감염자와 만났을 때 잠복기로 전환될 확률입니다.)
        self.RcvR = kwargs.get('RcvR')   # 일당 회복률
        self.DthR = kwargs.get('DthR')   # 일당 사망률
        self.VcnR = kwargs.get('VcnR')   # 일당 접종률
        self.InfR = kwargs.get('InfR')   # 잠복기 길이
        self.rILR = kwargs.get('rILR')   # 회복면역 상실률
        self.vILR = kwargs.get('vILR')   # 백신면역 상실률

        self.VcnS = kwargs.get('VcnS')   # 백신접종 시작일
        self.lim = kwargs.get('lim')
        self.S = Pop-Inf   # 비감염자 인구수를 선언해줍니다. 전체 인구수에서 초기 감염자 수를 뺀 값입니다.
        self.E = 0   # 노출자(잠복기) 인구수를 선언합니다. 초기에는 0으로 가정합니다.
        self.I = Inf   # 감염자 인구수를 선언합니다. 할당하는 값은 초기 감염자로 입력받은 Inf입니다.
        self.rI, self.vI = 0, 0  # 회복면역자(rI), 백신면역자(vI) 인구수를 선언합니다. 초기이므로 모두 0입니다.
        self.D = 0   # 사망자 인구수를 선언해줍니다. 마찬가지로 초기이므로 0으로 합니다.
        self.logList = [(self.S, self.E, self.I, self.rI, self.vI, self.D)]   # 매일마다의 감염병 진행상태를 저장할 리스트입니다. 첫날의 값을 추가해줍니다.
        self.days = 1   # 일수를 1일차로 지정해줍니다.
        self.acuI, self.acuV, self.acuR = self.I, 0, 0   #누적자 인스턴스를 선언해줍니다. 아래에 있는  __str__() 메서드에서 다룰 예정입니다.
        self.expList = []

    def __str__(self):   #print(class) 등의 상황에서 자동으로 호출되는 함수입니다.
        return f'''시뮬레이션 일수: {self.days}\n누적 확진 건수: {self.acuI}\n누적 회복 건수: {self.acuR}
        \033[8D누적 접종 건수: {self.acuV}\n누적 사망 건수: {self.D}'''   # 각 누적자 수를 반환하도록 합니다. \033[8D는 터미널의 커서를 8칸 앞으로 당기기 위한 탈출문자입니다.

    def nextDay(self) -> None:   # 함수 선언 시, 괄호를 닫은 후 -> 뒤에 반환 타입을 명시할 수 있습니다. 이후 유지보수나 인수인계 시 가독성을 향상시킵니다.
        'SEIIdv모형을 이용해 현재 변수상태에서 다음날의 감염자 상태를 예측합니다.'
        if self.days > 10*6: DaysTooLarge("Simulation term is too long. Days cannot be over 10^6.")
        self.days += 1   # 일수를 하루 늘려줍니다.
        rIL, vIL = round(self.rI * self.rILR), round(self.vI *self.vILR)   # 회복면역상실자수(rIL), 백신면역상실자수(vIL) 지역변수를 선언해줍니다. 면역을 잃는 인원수입니다.
        nR, nD = round(self.I * self.RcvR), round(self.I * self.DthR)   # 신규 회복자수(nR), 신규 사망자수(nD) 지역변수를 선언해줍니다. 새로 회복하거나 죽는 인원수입니다.
        livepop = self.S + self.E + self.I + self.rI + self.vI   # 현재 살아있는 인구수입니다.
        exposureProb = self.I / livepop if livepop else 0   # 노출확률입니다. 감염자를 만날 확률을 말합니다. livepop이 0일 경우 오류방지를 위해 노출확률을 0으로 지정합니다.
        nE = round(self.S * exposureProb * self.ExpR)   # 새로 노출되는 이들입니다. (비감염자수) * (노출확률) * (일당노출률)로 계산합니다.
        nV = round(self.S * self.VcnR)   # 신규접종자수 지역변수를 선언해줍니다. 비감염자 중, 백신을 접종하여 백신 면역을 획득하는 인원수입니다.
        self.S += (rIL + vIL)   # 비감염자의 증가 업데이트: (비감염자수) += {(회복면역상실자수) + (백신면역상실자수)}
        self.rI -= rIL   # 회복 면역자의 면역 상실 업데이트: (회복면역자수) -= (회복면역상실자수)
        self.vI -= vIL   # 백신 면역자의 면역 상실 업데이트: (백신면역자수) -= (백신면역상실자수)
        self.I -= (nR + nD)   # 감염자의 감소 업데이트: (감염자수) -= {(신규회복자수) + (신규사망자수)}
        self.rI += nR   # 감염자의 회복 업데이트: (회복면역자수) += (신규회복자수)
        self.D += nD   # 감염자의 사망 업데이트: (사망자수) += (신규사망자수)
        self.expList.append(nE)   # 노출자 리스트에 신규 노출자 추가
        if len(self.expList) > self.InfR:   # 잠복기 리스트 길이가 잠복기 길이보다 길때(잠복기를 넘어가는 인원이 있을때)
            nI = self.expList[0]   # 신규 감염자수 지역변수를 선언해줍니다. 증상이 시작되어, 새로 전파능력을 습득하게 되는 인원수입니다.
            self.I += nI   # 감염자 인원에 잠복기 넘어간 인원을 더합니다.
            self.E -= nI   # 잠복기 인원에 잠복기 넘어간 인원을 뺍니다.
            self.acuI += nI   # 누적감염자 수를 업데이트합니다.
            self.expList.remove(nI)   # 잠복기 리스트에서 해당인원을 뻅니다.
        self.E += nE   # 비감염자의 노출 업데이트: (노출자수) += (신규노출자수)
        self.S -= nE   # 비감염자의 노출 업데이트: (비감염자수) -= (신규노출자수)
        self.acuR = self.acuR+nR   # 누적 회복자 수를 업데이트합니다.
        if self.days >= self.VcnS:   # 현재 일자가 백신접종 시작 일자 이후이면 조건문 안 내용이 실행됩니다.
            self.vI += nV   # 비감염자의 접종 업데이트: (백신면역자수) += (신규접종자수)
            self.S -= nV   # 비감염자의 접종 업데이트: (비감염자수) -= (신규접종자수)
            self.acuV += nV   # 누적 접종자수를 업데이트해줍니다.
        if sum(self.logList[-1]) != self.sum(isLive=False):
            raise PopDoesNotMatch(f"Population does not match at {self.days}.")   # 사망자를 포함한 각 인구 총합은 항상 같아야 합니다. 다를 시 오류를 출력하고 프로그램을 멈춥니다.
        self.logList.append((self.S, self.E, self.I, self.rI, self.vI, self.D))   # 로그 리스트에 현재 확산 진행 상태를 .append() 메서드를 이용해 튜플로 추가합니다.

    # *, 뒤의 파라미터는 키워드인자를 받게 되어, 호출 시 이름 명시가 강제됩니다. 함수를 처음 보는 이로 하여금 각 인자의 역할을 더 쉽게 유추할 수 있도록 하는 효과를 가집니다.
    #또한 파라미터명 뒤의 =를 통해, 함수 호출 시 인자가 넘어오지 않을 시 기본값을 설정할 수 있습니다.
    def update(self, *, ExpR=None, RcvR=None, DthR=None, VcnR=None, InfR=None, rILR=None, vILR=None) -> None:
        '감염에 영향을 미치는 인스턴스들을 업데이트합니다.'
        for attr, val in dict(ExpR=ExpR, RcvR=RcvR, DthR=DthR, VcnR=VcnR, InfR=InfR, rILR=rILR, vILR=vILR).items():   # attr엔 이름, val엔 실제값을 할당하며 돕니다.
            if val is not None: setattr(self, attr, val)   # val, 즉 attr 이름의 값이 None이 아니라면, setattr()을 통해 self의 attr 이름을 가진 인스턴스의 값을 val로 설정합니다.
    
    def sum(self, *, isLive:bool=True) -> int:   # 인구 총합을 출력하는 메서드입니다. 자료형 강제와 기본값 설정을 동시에 할 경우, 기본값을 나중에 설정합니다.
        '''인구 총합을 출력합니다. isLive는 사망자 포함 여부를 결정하며, 기본값이 True로 설정되어 있습니다.'''
        if isLive: return self.S + self.E + self.I + self.rI + self.vI   # isLive가 참일 경우, 사망자를 포함하지 않습니다. 인자를 넘기지 않고 호출 시에도 실행됩니다.
        else: return self.S + self.E + self.I + self.rI + self.vI + self.D   # isLive가 거짓인 경우, 사망자를 포함합니다. 이 값은 항상 같으므로, 이를 통해 모형의 무결성을 검증합니다.
    

    def init_graph(self, *, PopScale: str, overComeLimit: int, win=None) -> QtCanvas:
        'logList에 저장 된 SEIIdv 모형 시뮬레이션 결과를 matplotlib을 이용해 시각화하는 함수입니다.'
        data = list(zip(*self.logList))   # [[S1, E1, ..], [S2, E2, ..], ...] 형식에서 [[S1, S2, ..], [E1, E2, ..], ...]형식으로 변환합니다.
        labels = ['비감염자', '노출자', '감염자', '회복면역자', '백신면역자', '사망자']   # 각 그룹별 이름을 선언합니다. 추후 범례를 붙일 때 사용됩니다.
        Colors = ['Blue', "Orange", 'Red', 'Green', "Skyblue", "Black"]   # 각 그룹별 그래프의 색상을 선언합니다.
        isFirst = True   # 종식선언 기준의 최초 충족 여부를 판단하는 변수를 선언합니다. 초기값은 참입니다.
        plt.rc('font', family='NanumGothic')   # 한글 깨짐 문제를 없애기 위해, 폰트를 나눔고딕으로 명시해줍니다.
        plt.rcParams['axes.unicode_minus'] = False   # 일부 폰트는 수학에서 쓰는 -기호(유니코드 다름)가 없어서 오류가 나므로, 방지를 위해 일반 -기호로 대체하도록 강제합니다.
        self.fig = plt.figure(figsize=(10, 5))   # fig는 그래프창을 생성해줍니다.
        self.ax = self.fig.add_subplot(111)   # ax는 subplot입니다. 여러 개의 그래프를 그릴 수 있으나, 하나가 목적이므로 pos에 111(가로1개, 세로1개 그래프중 1번째 위치)을 전달합니다.
        self.plotLines = []  # 추후 update_graph()에서 각 선을 갱신하기 위해 저장합니다.
        for i in range(6):
            if i == 2: w = 3
            else: w = 1
            line, = self.ax.plot(data[i], label=labels[i], color=Colors[i], linewidth = w)   # 각 그룹별 그래프 선을 그립니다.
            self.plotLines.append(line)   # 선 객체를 저장해둡니다.
        for i in range(self.days):   # 그래프를 모두 그린 후, 각 일을 도는 루프입니다. 일수를 i에 할당합니다.
            livepop = sum(self.logList[i])  #  i일째 당시 살아있는 인구수를 미리 계산합니다.
            if data[2][i]/livepop * 100 < overComeLimit and isFirst and i>self.lim:   # 감염자가 인구수의 overComeLimit% 미만이 되며 감염자가 하락세인 최초시점이면 조건문 안 내용이 실행됩니다.
                self.ax.axvline(x=i, color='red', linestyle='--', linewidth=2)   # 해당 시점을 종식일로 잡고,  linestyle에 '--'를 전달하여 그래프에 빨간 점선을 그립니다.
                isFirst = False   # 세로선이 여러개 생기지 않도록 if문 진입을 차단합니다.
        self.ax.set_xlabel('일수')   # X축 이름을 설정합니다.
        self.ax.set_ylabel(f'인구수 ({PopScale})')   # Y축 이름을 설정합니다.
        self.ax.set_title('SEIIdv 모형에 따른 감염병 확산 추이')   # 그래프 제목을 설정합니다.
        self.ax.legend()   # 범례를 표시합니다. 위에서 선을 그릴 때 지정한 label을 통해, matplotlib에서 자동으로 색상을 맞춰줍니다.
        self.ax.grid(True)   # visible에 True를 전달하여 눈금 표시를 켭니다.
        if __name__ == "__main__": plt.show()   # definer.py에서 직접 호출되는 경우, 그래프 창을 열어줍니다.
        elif win is None:
            return QtCanvas(self.fig)   # PyQt6용 FigureCanvas 반환
        else:
            return TkCanvas(self.fig, master=win)  # tkinter용 FigureCanvas 반환


    def update_graph(self):
        '현재 logList의 데이터를 기준으로 plotLines 선 데이터를 업데이트하는 함수입니다.'
        new_data = list(zip(*self.logList))  # 최신 데이터를 가져옵니다.
        for i, line in enumerate(self.plotLines):
            line.set_ydata(new_data[i])  # y값을 갱신해줍디나.
            line.set_xdata(range(len(new_data[i])))  # x값도 갱신해줍니다.
        self.ax.relim()  # 축을 다시 계산합니다.
        self.ax.autoscale_view()  # 자동으로 스케일링을 진행해줍니다.

#테스트용 코드입니당 value에 값 바꿔가면서 돌려보세요!
if __name__ == '__main__':   # 직접 실행할때는 __name__이 '__main__'이고, 임포트했을 때는 해당 파일명입니다.
    value = {'ExpR' : 0.6, 'InfR' : 50, 'DthR' : 0.003, 'RcvR' : 0.1,
             'VcnR' : 0.1, 'rILR' : 0.051, 'vILR' : 0.073, 'VcnS' : 565, 'lim' : 300}   # 모형에 들어갈 초기세팅값들(딕셔너리)을 지정해줍니다.
    model = SEIIdv(5*10**7, 3000, **value)   # SEIIdv 클래스를 model에 할당하여, 모형을 생성합니다.
    for i in range(565): model.nextDay()   # 1000일동안 인스턴스 값의 변화 없이 시뮬레이션합니다.
    model.update(RcvR=0.6)
    for i in range(5000): model.nextDay()
    print(model)   # __str__()의 반환값을 출력합니다. 상술한 것과 같이, 누적 인원수를 출력하게 됩니다.
    model.init_graph(overComeLimit=0.01, PopScale="천만")   # 그래프를 그립니다. PopScale 파라미터에 "천만"을 전달해, 단위를 표시하도록 합니다.
