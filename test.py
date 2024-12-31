import re
import tkinter as tk
from tkinter import messagebox
import json

# 외부 파일에서 데이터 로드
def load_data():
    try:
        with open('element_data.json', 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        messagebox.showerror("File Error", "element_data.json 파일을 찾을 수 없습니다!")
        return None

# 데이터 로드
DATA = load_data()
if DATA is None:
    exit()

# 데이터 검색 함수
def get_element_info(el):
    return DATA.get(el, None)

# 옥텟 규칙 계산 함수
def get_octet_need(grp):
    try:
        if grp >= 1 and grp <= 12:  # 1족, 2족은 전자를 잃음
            return grp
        elif grp >= 13 and grp <= 18:  # 13족~18족은 전자를 얻음
            return 18 - grp
        return 'Unknown'
    except Exception:
        return 'Unknown'

# 산화수 계산 함수 (기본 로직)
def calculate_oxidation_states(parsed_formula):
    try:
        oxidation_states = {}

        sorted_elements = sorted(parsed_formula.keys(),
                                 key=lambda x: DATA[x]["EN"] if DATA[x]["EN"] != "N/A" else 0,
                                 reverse=True)
        most_electronegative = sorted_elements[0]

        for el, num in parsed_formula.items():
            element_info = get_element_info(el)
            if element_info:
                grp = element_info.get("Group", None)
                if grp == 1:
                    oxidation_states[el] = min(1, num)
                elif grp == 2:
                    oxidation_states[el] = min(2, num)
                else:
                    octet_need = get_octet_need(grp)
                    oxidation_states[el] = octet_need if octet_need != "Unknown" else 0
            else:
                oxidation_states[el] = 0

        oxidation_states[most_electronegative] *= -1
        return oxidation_states
    except Exception as e:
        return {"Error": str(e)}

# 가운데 원소 산화수 조정 함수
def adjust_middle_oxidation_state(parsed_formula, oxidation_states):
    if len(parsed_formula) == 3:
        elements = list(parsed_formula.keys())
        middle_element = elements[1]  # 가운데 원소

        # 다른 원소들의 산화수는 옥텟 규칙과 전기음성도로만 계산
        for el in elements:
            if el != middle_element:
                element_info = get_element_info(el)
                if element_info:
                    grp = element_info.get("Group", None)
                    oxidation_states[el] = get_octet_need(grp)
                    if el == max(elements, key=lambda x: DATA[x]["EN"] if DATA[x]["EN"] != "N/A" else 0):
                        oxidation_states[el] *= -1

        # 1족, 2족 원소 산화수 고정
        for el in elements:
            element_info = get_element_info(el)
            if element_info:
                grp = element_info.get("Group", None)
                if grp == 1 and oxidation_states[el] > 1:
                    oxidation_states[el] = 1
                elif grp == 2 and oxidation_states[el] > 2:
                    oxidation_states[el] = 2

        # 가운데 원소 산화수 조정
        total_charge = sum(oxidation_states[el] * parsed_formula[el] for el in parsed_formula if el != middle_element)
        oxidation_states[middle_element] = -total_charge // parsed_formula[middle_element]

        # 최종적으로 전체 산화수 합이 0이 되도록 강제 조정
        total_charge = sum(oxidation_states[el] * parsed_formula[el] for el in parsed_formula)
        if total_charge != 0:
            oxidation_states[middle_element] -= total_charge // parsed_formula[middle_element]

    return oxidation_states

# 원소별 정보 출력 함수
def get_info(formula):
    try:
        elems = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
        parsed = {el[0]: int(el[1]) if el[1] else 1 for el in elems}

        oxidation_states = calculate_oxidation_states(parsed)

        if len(parsed) == 3:
            oxidation_states = adjust_middle_oxidation_state(parsed, oxidation_states)

        info = []
        oxidation_info = []
        for el, count in parsed.items():
            element_info = get_element_info(el)
            if element_info:
                en = element_info.get("EN", "정보 없음")
                num = element_info.get("Atomic#", "정보 없음")
                grp = element_info.get("Group", "정보 없음")
                octet = get_octet_need(grp)
                ox_state = oxidation_states.get(el, "정보 없음")

                info.append(f"{el}: 전기음성도={en}, 원자번호={num}, {grp}족, 분자 하나당 {count}개")
                if ox_state > 0:
                    ox = '+' + str(ox_state)
                else:
                    ox = str(ox_state)
                oxidation_info.append(f"{el}: {ox}")

        result_text = "\n".join(info) + "\n\n" + "산화수 정보:\n" + "\n".join(oxidation_info)
        return result_text
    except Exception as e:
        return f"Error: {str(e)}"

def on_calc():
    formula = entry.get().strip()
    if not formula:
        messagebox.showerror("Input Error", "Please enter a formula!")
        return

    info = get_info(formula)
    result.config(text=info)

def on_enter(event):
    on_calc()

# Tkinter GUI 설정
root = tk.Tk()
root.title("Element Info Viewer")
root.geometry("600x500")

FONT_LARGE = ("Arial", 14)
frame = tk.Frame(root)
frame.pack(pady=10)

lbl = tk.Label(frame, text="화학식: ", font=FONT_LARGE)
lbl.grid(row=0, column=0)

entry = tk.Entry(frame, width=20, font=FONT_LARGE)
entry.grid(row=0, column=1)
entry.bind("<Return>", on_enter)

btn = tk.Button(frame, text="계산하기", command=on_calc, font=FONT_LARGE)
btn.grid(row=0, column=2)

result = tk.Label(root, text="화학식을 입력해주세요", wraplength=550, justify="left", font=FONT_LARGE)
result.pack(pady=10)

root.mainloop()
