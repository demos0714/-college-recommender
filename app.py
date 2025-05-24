import streamlit as st
import pandas as pd
import ast
import uuid
import copy
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 科目名稱映射表
SUBJECT_MAPPING = {
    '國': '國文',
    '英': '英文',
    '數A': '數學 A',
    '數B': '數學 B',
    '社': '社會',
    '自': '自然'
}

# 在檔案最上面或 load config 時定義
SHOW_DEBUG_WARNINGS = False

# 推薦理由範本庫（量化描述）
REASON_TEMPLATES = {
    "工程": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議加強數理或面試準備。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他相關科系。"
    },
    "管理": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議準備校系特色項目。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他管理科系。"
    },
    "文史哲": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議加強背景知識準備。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議探索其他相關科系。"
    },
    "醫藥衛生": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議強化專業科目。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他相關科系。"
    },
    "資訊": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議提前準備程式基礎。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他資訊科系。"
    },
    "生物資源": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議準備相關實務能力。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他相關科系。"
    },
    "外語": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議加強語言能力準備。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他外語科系。"
    },
    "default": {
        "頂標": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，符合「頂標」條件，錄取機會極高。",
        "中段": "平均超出要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「中段」，建議加強準備校系特色。",
        "後段": "平均落後要求 {mean_diff:+.1f} 分，最小分差 {min_diff:+.1f} 分，屬於「後段」，建議備選其他相關科系。"
    }
}

# 內建測試資料（包含 school 和 dept）
DEFAULT_PROGRAMS = [
    {
        "program_name": "世新大學 企業管理學系",
        "expanded_score_dict": "{'國': 12, '社': 12}",
        "group": "管理",
        "school": "世新大學",
        "dept": "企業管理學系"
    },
    {
        "program_name": "世新大學 傳播管理學系",
        "expanded_score_dict": "{'國': 11}",
        "group": "管理",
        "school": "世新大學",
        "dept": "傳播管理學系"
    },
    {
        "program_name": "世新大學 行政管理學系",
        "expanded_score_dict": "{'英': 10, '社': 10}",
        "group": "管理",
        "school": "世新大學",
        "dept": "行政管理學系"
    },
    {
        "program_name": "世新大學 財務金融學系",
        "expanded_score_dict": "{'數B': 10, '社': 10}",
        "group": "管理",
        "school": "世新大學",
        "dept": "財務金融學系"
    },
    {
        "program_name": "銘傳大學 應用中文與華語文教",
        "expanded_score_dict": "{'國': 10, '英': 10}",
        "group": "文史哲",
        "school": "銘傳大學",
        "dept": "應用中文與華語文教"
    },
    {
        "program_name": "世新大學 數位多媒體設計學系",
        "expanded_score_dict": "{'國': 11}",
        "group": "藝術",
        "school": "世新大學",
        "dept": "數位多媒體設計學系"
    },
    {
        "program_name": "某大學 醫學系",
        "expanded_score_dict": "{'國': 14, '英': 14, '數A': 14, '自': 14}",
        "group": "醫藥衛生",
        "school": "某大學",
        "dept": "醫學系"
    },
    {
        "program_name": "某大學 護理學系",
        "expanded_score_dict": "{'英': 13, '自': 13}",
        "group": "醫藥衛生",
        "school": "某大學",
        "dept": "護理學系"
    },
    {
        "program_name": "某大學 資訊工程學系",
        "expanded_score_dict": "{'數A': 12, '自': 12}",
        "group": "資訊",
        "school": "某大學",
        "dept": "資訊工程學系"
    },
    {
        "program_name": "某大學 生物資源學系",
        "expanded_score_dict": "{'自': 11, '數A': 11}",
        "group": "生物資源",
        "school": "某大學",
        "dept": "生物資源學系"
    },
    {
        "program_name": "國立臺灣大學 外國語文學系",
        "expanded_score_dict": "{'國': 13, '英': 13}",
        "group": "外語",
        "school": "國立臺灣大學",
        "dept": "外國語文學系"
    }
]

# 設定頁面配置
st.set_page_config(
    page_title="學測志願模擬器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式（支援自動換行）
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Noto Sans TC', sans-serif !important;
        background-color: #ecf0f1 !important;
        color: #2c3e50 !important;
    }
    div[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stSidebar"] form[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .stCheckbox input[type="checkbox"] {
        appearance: auto !important;
        -webkit-appearance: checkbox !important;
        accent-color: #2c3e50 !important;
        width: 18px !important;
        height: 18px !important;
    }
    .stCheckbox > label {
        padding-left: 8px !important;
    }
    .stNumberInput > div > div > input {
        border: 1px solid #2c3e50 !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .stSelectbox > div > div > select {
        border: 1px solid #2c3e50 !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .stMultiSelect > div > div {
        border: 1px solid #2c3e50 !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .stButton>button, .stFormSubmitButton>button {
        border-radius: 5px;
        border: 1px solid #2c3e50;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        min-width: 100px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background-color: #3498db;
        color: white;
        border-color: #3498db;
        transform: scale(1.05);
    }
    button[title="移除"] {
        background-color: #e74c3c;
        color: white;
        border: 1px solid #e74c3c;
        padding: 5px 10px;
    }
    button[title="移除"]:hover {
        background-color: #c0392b;
        border-color: #c0392b;
        transform: scale(1.05);
    }
    .aspiration-container {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .aspiration-error {
        background-color: #D8A7B1 !important;
        color: #2c3e50 !important;
    }
    .aspiration-success {
        background-color: #A8C4B6 !important;
        color: #2c3e50 !important;
    }
    .recommendation-card {
        border: 1px solid #2c3e50;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-height: 120px;
        overflow: hidden;
    }
    .recommendation-card strong {
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        display: block;
        font-size: 1.1em;
        color: #2c3e50;
    }
    .recommendation-card .details {
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        margin-top: 8px;
        font-size: 0.9em;
        color: #555;
        line-height: 1.4;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_and_process_data():
    """預處理資料集，解析 CSV 並過濾無效資料，新增 school 和 dept 欄位"""
    try:
        df = pd.read_csv("programs.csv", encoding='utf-8-sig')
    except FileNotFoundError:
        logger.warning("找不到 programs.csv 檔案，使用內建測試資料。")
        df = pd.DataFrame(DEFAULT_PROGRAMS)
    
    # 清理 group 欄位的空白
    df["group"] = df["group"].astype(str).str.strip()
    
    # 確保 program_name 和 school 為字串型態
    df["program_name"] = df["program_name"].astype(str).replace("nan", "")
    df["school"] = df["program_name"].str.extract(r"^(\S+大學|\S+學院|\S+醫學大學|\S+市立大學)")[0]
    df["school"] = df["school"].fillna(df["program_name"].str.extract(r"^(\S+)")[0]).fillna("").astype(str)
    
    # 提取 dept 欄位
    df["dept"] = df.apply(
        lambda row: row["program_name"].replace(row["school"], "").strip(),
        axis=1
    )
    
    # 檢查是否有空或異常的 dept 值
    invalid_depts = df[df["dept"] == ""]
    if not invalid_depts.empty:
        logger.warning(f"發現 {len(invalid_depts)} 筆空的 dept 值：{invalid_depts['program_name'].tolist()}")
    
    # 生成動態學群選項
    group_options = sorted(df["group"].dropna().astype(str).str.strip().unique().tolist())
    logger.info(f"動態生成的學群選項：{group_options}")
    
    # 生成學校清單
    school_list = ["全部學校"] + sorted(df["school"].dropna().unique().tolist())
    
    programs_list = []
    invalid_subjects = set()
    invalid_scores_log = []
    skipped_programs = 0

    for idx, row in df.iterrows():
        try:
            score_dict = ast.literal_eval(row["expanded_score_dict"])
            score_dict = {k: max(0, v) for k, v in score_dict.items()}
            raw_subjects = list(score_dict.keys())
            required_subjects = [SUBJECT_MAPPING.get(k, k) for k in raw_subjects]
            
            # 檢查科目有效性
            invalid_subj = [subj for subj in required_subjects if subj not in ["國文", "英文", "數學 A", "數學 B", "社會", "自然"]]
            if invalid_subj:
                invalid_subjects.update(invalid_subj)
                skipped_programs += 1
                logger.warning(f"行 {idx+1}: {row['program_name']} 包含無效科目 {invalid_subj}")
                continue
            
            # 檢查分數範圍（允許 0-15）
            invalid_scores = [k for k, v in score_dict.items() if v < 0 or v > 15]
            if invalid_scores:
                invalid_scores_log.append((row["program_name"], invalid_scores))
                skipped_programs += 1
                logger.warning(f"行 {idx+1}: {row['program_name']} 包含無效分數 {invalid_scores}")
                continue
            
            programs_list.append({
                "program_name": row["program_name"],
                "required_subjects": required_subjects,
                "raw_subjects": raw_subjects,
                "expanded_score_dict": score_dict,
                "score": sum(score_dict.values()),
                "group": row["group"],
                "school": row["school"],
                "dept": row["dept"]
            })
        except Exception as e:
            skipped_programs += 1
            logger.error(f"行 {idx+1}: 解析 {row['program_name']} 時出錯：{str(e)}")
            continue
    
    if invalid_subjects:
        logger.warning(f"發現無效科目：{', '.join(invalid_subjects)}，已跳過 {skipped_programs} 個科系。")
    if invalid_scores_log:
        logger.warning(f"發現分數異常（<0或>15）的科系：{len(invalid_scores_log)} 筆，已跳過。")
    if skipped_programs > 0:
        logger.warning(f"共跳過 {skipped_programs} 個無效科系。")

    return programs_list, school_list, group_options

def get_user_input(school_list, group_options):
    """獲取使用者輸入"""
    st.header("學測志願模擬器")
    st.write("請輸入你的學測成績與志願設定，我們將幫你推薦最適合的志願組合！")
    st.markdown("<hr style='border: 1px solid #2c3e50; margin: 20px 0;'>", unsafe_allow_html=True)

    st.subheader("學測級分輸入")
    subject_options = ["國文", "英文", "數學 A", "數學 B", "社會", "自然"]
    
    if "subject_selections" not in st.session_state:
        st.session_state.subject_selections = {subject: False for subject in subject_options}
    
    subject_cols = st.columns(3)
    selected_subjects = []
    scores = {}
    for i, subject in enumerate(subject_options):
        with subject_cols[i % 3]:
            col1, col2 = st.columns([1, 1])
            with col1:
                checked = st.checkbox(subject, key=f"subject_{subject}", value=st.session_state.subject_selections[subject])
                st.session_state.subject_selections[subject] = checked
            if checked:
                selected_subjects.append(subject)
                with col2:
                    scores[subject] = st.number_input(
                        f"{subject} 級分",
                        min_value=0,
                        max_value=15,
                        value=10,
                        step=1,
                        key=f"score_{subject}",
                        label_visibility="collapsed"
                    )

    with st.sidebar:
        st.subheader("感興趣的學群")
        selected_groups = st.multiselect("", options=group_options, default=None)
        st.markdown(f"已選擇：**{', '.join(selected_groups) if selected_groups else '尚未選擇'}**")

        st.subheader("篩選學校")
        selected_school = st.selectbox("", school_list, index=0)

        st.subheader("志願風險偏好分配（共 6 個志願）")
        
        if "conservative" not in st.session_state:
            st.session_state.conservative = 2
        if "realistic" not in st.session_state:
            st.session_state.realistic = 2
        if "ambitious" not in st.session_state:
            st.session_state.ambitious = 2

        total = st.session_state.conservative + st.session_state.realistic + st.session_state.ambitious
        remaining = 6 - total
        aspiration_class = "aspiration-error" if total != 6 else "aspiration-success"
        message = (
            f"目前總和為 {total}，請調整為 6 個志願。還需 {remaining} 個志願。" if total < 6 else
            f"目前總和為 {total}，請調整為 6 個志願。請減少 {-remaining} 個志願。" if total > 6 else
            "志願分配總和正確（共 6 個）"
        )

        st.markdown(
            f"""
            <div class="aspiration-container {aspiration_class}">
                <p style="margin:0; font-weight:500;">{message}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col4, col5, col6 = st.columns(3)
        with col4:
            conservative = st.number_input("保守型", 0, 6, key="conservative")
        with col5:
            realistic = st.number_input("務實型", 0, 6, key="realistic")
        with col6:
            ambitious = st.number_input("夢幻型", 0, 6, key="ambitious")

    button_label = "模擬志願分發" if not st.session_state.get("submitted", False) else "重新生成推薦志願"
    
    with st.form(key="input_form"):
        submit_button = st.form_submit_button(button_label)
        if submit_button:
            logger.info("提交表單，開始處理使用者輸入")
            if not selected_subjects:
                st.error("請至少選擇一門科目以計算分數。")
                return None
            
            if total != 6:
                st.warning(f"志願總和為 {total}，自動調整為 6 個志願。")
                if total < 6:
                    st.session_state.ambitious += remaining
                elif total > 6:
                    excess = -remaining
                    while excess > 0:
                        if st.session_state.ambitious > 0:
                            st.session_state.ambitious -= 1
                            excess -= 1
                        elif st.session_state.realistic > 0:
                            st.session_state.realistic -= 1
                            excess -= 1
                        elif st.session_state.conservative > 0:
                            st.session_state.conservative -= 1
                            excess -= 1
                total = st.session_state.conservative + st.session_state.realistic + st.session_state.ambitious

            current_input = {
                "scores": scores,
                "selected_subjects": selected_subjects,
                "interests": selected_groups,
                "school": selected_school,
                "strategy_allocation": {
                    "保守型": st.session_state.conservative,
                    "務實型": st.session_state.realistic,
                    "夢幻型": st.session_state.ambitious
                }
            }
            
            if "prev_input" not in st.session_state or current_input != st.session_state.prev_input:
                st.session_state.prev_input = current_input
                st.session_state.user_input = current_input
                st.session_state.submitted = True
                # 清空舊狀態
                for key in list(st.session_state.keys()):
                    if key.startswith(('recommendation_data', 'shown_items', 'available_pools', 'message_')):
                        del st.session_state[key]
                logger.info("使用者輸入已更新，舊狀態已清除")
                return current_input
            else:
                st.error("請先調整「成績／興趣／學校／風險分配」等參數，才能重新生成推薦志願。")
                return None

    if "user_input" in st.session_state:
        return st.session_state.user_input

    return None

def is_skippable(program, user_scores):
    """檢查是否應跳過科系（完全無交集才跳過）"""
    return set(program["required_subjects"]).isdisjoint(user_scores.keys())

def generate_reason(program, user_input, strategy_type):
    """
    生成推薦理由 (量化＋模板)：
    1. 若沒填任何分數 → 提示輸入成績
    2. 若缺少必填科目 → 列出缺科目
    3. 若完全無交集 (is_skippable) → 無法評估
    4. 否則：
       • 計算各科 diff、min_diff、mean_diff
       • 用範本庫 (REASON_TEMPLATES) 依學群＋level(level: 頂標/中段/後段) 產生 summary
       • details 組合所需科目、你的分數、分差明細
    """
    scores = user_input.get("scores", {})
    # 1. 尚未輸入任何成績
    if not scores:
        return {"summary": "請先輸入學測成績。", "details": ""}

    required = program["required_subjects"]
    raw_keys = program["raw_subjects"]
    score_dict = program["expanded_score_dict"]
    group = program.get("group", "default")

    # 2. 缺少必填科目
    missing = [s for s in required if s not in scores]
    if missing:
        return {
            "summary": f"缺少科目：{', '.join(missing)}",
            "details": ""
        }

    # 3. 完全無交集 (自定義跳過條件)
    if is_skippable(program, scores):
        return {
            "summary": "無任何匹配的科目分數，無法評估錄取可能性。",
            "details": ""
        }

    # 4. 計算分差
    user_score_str = ", ".join(f"{subj}: {scores.get(subj, 0)} 分"
                               for subj in required)
    program_score_str = ", ".join(f"{subj}: {score_dict.get(key, 0)} 分"
                                 for key, subj in zip(raw_keys, required))

    diffs = [scores.get(subj, 0) - score_dict.get(key, 0)
             for key, subj in zip(raw_keys, required)]
    min_diff = min(diffs)
    mean_diff = sum(diffs) / len(diffs)

    diff_str = ", ".join(f"{subj}: {diff:+.1f} 分"
                         for subj, diff in zip(required, diffs))

    details = (
        f"📋 所需科目與分數：{program_score_str}<br>"
        f"✅ 你的分數：{user_score_str}<br>"
        f"🔍 分數差距：{diff_str}"
    )

    # 5. 判斷等級 (level) → 用於選模板
    if min_diff >= 3:
        level = "頂標"
    elif min_diff >= 0:
        level = "中段"
    else:
        level = "後段"

    # 6. 從 REASON_TEMPLATES 裡取對應範本
    template_group = group if group in REASON_TEMPLATES else "default"
    summary_tpl = REASON_TEMPLATES[template_group][level]

    # 7. 生成最終 summary（帶 icon）
    summary = f"💡 {summary_tpl.format(mean_diff=mean_diff, min_diff=min_diff)}"

    return {"summary": summary, "details": details}

def generate_recommendations(user_input):
    """生成推薦志願"""
    # 明確解包 load_and_process_data 的返回值
    programs_list, school_list, group_options = load_and_process_data()
    
    # 調試：檢查 programs_list 結構
    logger.info(f"programs_list type: {type(programs_list)}, length: {len(programs_list)}")
    if programs_list:
        logger.info(f"First program type: {type(programs_list[0])}, content: {programs_list[0]}")
    
    selected_groups = user_input.get("interests", [])
    selected_school = user_input.get("school", "全部學校")
    
    # 過濾學群
    if not selected_groups:
        logger.warning("未選擇任何感興趣的學群，將顯示所有有效科系。")
        filtered_programs = programs_list
    else:
        filtered_programs = [p for p in programs_list if p["group"] in selected_groups]
    
    # 過濾學校
    if selected_school != "全部學校":
        filtered_programs = [p for p in filtered_programs if p["school"] == selected_school]
    
    # 調試：檢查 filtered_programs 結構
    logger.info(f"filtered_programs type: {type(filtered_programs)}, length: {len(filtered_programs)}")
    if filtered_programs:
        logger.info(f"First filtered program type: {type(filtered_programs[0])}, content: {filtered_programs[0]}")
    
    conservative_pool = []
    realistic_pool = []
    ambitious_pool = []
    missing_subjects_log = {}

    user_scores = user_input.get("scores", {})
    for program in filtered_programs:
        if not isinstance(program, dict):
            logger.error(f"Invalid program type: {type(program)}, content: {program}")
            continue
        
        required_subjects = program["required_subjects"]
        raw_subjects = program["raw_subjects"]
        score_dict = program["expanded_score_dict"]

        missing_subjects = [s for s in required_subjects if s not in user_scores]
        if missing_subjects:
            for subj in missing_subjects:
                missing_subjects_log[subj] = missing_subjects_log.get(subj, 0) + 1
            continue

        subject_pairs = [(user_scores[subj], score_dict[raw_subj]) for raw_subj, subj in zip(raw_subjects, required_subjects)]

        if any(user < required for user, required in subject_pairs):
            ambitious_pool.append(program)
        elif all(user >= required + 2 for user, required in subject_pairs):
            conservative_pool.append(program)
        elif all(user >= required for user, required in subject_pairs):
            realistic_pool.append(program)
        else:
            ambitious_pool.append(program)

    conservative_pool.sort(key=lambda x: (x["score"], len(x["required_subjects"])), reverse=True)
    realistic_pool.sort(key=lambda x: (x["score"], len(x["required_subjects"])), reverse=True)
    ambitious_pool.sort(key=lambda x: (x["score"], len(x["required_subjects"])), reverse=True)

    logger.info(f"候選池大小 - 保守型: {len(conservative_pool)} 筆, 務實型: {len(realistic_pool)} 筆, 夢幻型: {len(ambitious_pool)} 筆")

    strategy_allocation = user_input.get("strategy_allocation", {})
    recommendation_result = {
        "保守型": [],
        "務實型": [],
        "夢幻型": []
    }

    for pool, count, strategy_type in [
        (conservative_pool, strategy_allocation.get("保守型", 0), "保守型"),
        (realistic_pool, strategy_allocation.get("務實型", 0), "務實型"),
        (ambitious_pool, strategy_allocation.get("夢幻型", 0), "夢幻型")
    ]:
        selected_programs = pool[:count]
        processed_programs = []
        for program in selected_programs:
            program_with_id = copy.deepcopy(program)
            program_with_id["uid"] = str(uuid.uuid4())
            program_with_id["reason"] = generate_reason(program_with_id, user_input, strategy_type)
            processed_programs.append(program_with_id)

        recommendation_result[strategy_type] = processed_programs

        if len(pool) < count:
            logger.warning(f"{strategy_type} 僅有 {len(pool)} 個符合條件的科系，少於要求的 {count} 個")
            st.warning(f"{strategy_type} 僅有 {len(pool)} 個符合條件的科系，無法滿足 {count} 個志願。")

    if "recommendation_data" not in st.session_state:
        st.session_state.recommendation_data = recommendation_result
        st.session_state.shown_items = {
            stype: copy.deepcopy(recommendation_result[stype]) for stype in recommendation_result
        }
        st.session_state.available_pools = {
            "保守型": [copy.deepcopy(p) for p in conservative_pool if not any(p["program_name"] == selected["program_name"] for selected in recommendation_result["保守型"])],
            "務實型": [copy.deepcopy(p) for p in realistic_pool if not any(p["program_name"] == selected["program_name"] for selected in recommendation_result["務實型"])],
            "夢幻型": [copy.deepcopy(p) for p in ambitious_pool if not any(p["program_name"] == selected["program_name"] for selected in recommendation_result["夢幻型"])]
        }
        logger.info(f"初始化 available_pools - 保守型: {len(st.session_state.available_pools['保守型'])}, 務實型: {len(st.session_state.available_pools['務實型'])}, 夢幻型: {len(st.session_state.available_pools['夢幻型'])}")

    return recommendation_result

def display_recommendations(user_input, recommendation_data):
    """顯示推薦志願並處理移除/遞補（不跨池）"""
    st.header("推薦志願（點擊移除可自動遞補）")
    st.markdown("<hr style='border: 1px solid #2c3e50; margin: 20px 0;'>", unsafe_allow_html=True)

    strategy_types = ["保守型", "務實型", "夢幻型"]

    def handle_remove(stype, item_uid):
        """處理移除與遞補邏輯（僅同池遞補）"""
        logger.info(f"進入 handle_remove，stype={stype}, item_uid={item_uid}")
        logger.info(f"shown_items[{stype}] = {[item['program_name'] for item in st.session_state.shown_items[stype]]}")
        
        removed_item = None
        for item in st.session_state.shown_items[stype]:
            if item["uid"] == item_uid:
                removed_item = item
                st.session_state.shown_items[stype].remove(item)
                logger.info(f"已移除 {item['program_name']} (UID: {item_uid})")
                break
        
        if not removed_item:
            logger.error(f"未找到 UID {item_uid} 的項目，移除失敗")
            st.session_state[f"message_{stype}"] = "移除失敗：未找到指定項目"
            st.rerun()
            return

        available = st.session_state.available_pools.get(stype, [])
        logger.info(f"可用項目數量 ({stype}): {len(available)}")
        if available:
            next_item = copy.deepcopy(available.pop(0))
            next_item["uid"] = str(uuid.uuid4())
            next_item["reason"] = generate_reason(next_item, user_input, stype)
            st.session_state.shown_items[stype].append(next_item)
            logger.info(f"從 {stype} 遞補 {next_item['program_name']} (UID: {next_item['uid']})")
            st.session_state[f"message_{stype}"] = f"已移除 {removed_item['program_name']}，已遞補 {next_item['program_name']}"
        else:
            logger.warning(f"{stype} 無更多可遞補項目")
            st.session_state[f"message_{stype}"] = f"已移除 {removed_item['program_name']}，無更多可遞補項目"
        
        logger.info(f"更新後 shown_items[{stype}] = {[item['program_name'] for item in st.session_state.shown_items[stype]]}")
        st.rerun()

    cols = st.columns(3)
    
    for i, stype in enumerate(strategy_types):
        with cols[i]:
            st.subheader(f"{stype}")
            target_count = user_input["strategy_allocation"].get(stype, 0)
            current_items = st.session_state.shown_items.get(stype, [])
            logger.info(f"顯示 {stype}：{len(current_items)} 筆，項目名稱={[item['program_name'] for item in current_items]}")
            
            if f"message_{stype}" in st.session_state:
                st.success(st.session_state[f"message_{stype}"])
                del st.session_state[f"message_{stype}"]
            
            if not current_items and target_count > 0:
                st.warning(f"{stype} 無符合條件的科系，可能因缺少所需科目或分數不足。")
            
            for item in current_items:
                with st.container():
                    reason = item["reason"]["summary"] if isinstance(item["reason"], dict) else item["reason"]
                    details = item["reason"]["details"] if isinstance(item["reason"], dict) else item["reason"]
                    
                    st.markdown(f"""
                        <div class="recommendation-card">
                            <strong>🎓 {item['program_name']}</strong>
                            <div class="details">
                            📚 學群：{item['group']}<br>
                            💡 推薦理由：{reason}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("查看詳細理由"):
                        st.markdown(details, unsafe_allow_html=True)
                    
                    btn_key = f"remove_{item['uid']}_{stype}"
                    logger.info(f"生成按鈕鍵：{btn_key}")
                    if st.button("移除", key=btn_key, help="移除此志願"):
                        logger.info(f"點擊移除按鈕，UID: {item['uid']}, 科系: {item['program_name']}")
                        handle_remove(stype, item["uid"])
            
            if len(current_items) < target_count:
                missing = target_count - len(current_items)
                st.warning(f"{stype} 目前僅有 {len(current_items)}/{target_count} 筆可推薦，無法再補充。")
            else:
                shown = len(current_items)
                pool = len(st.session_state.available_pools.get(stype, []))
                total_pool = shown + pool
                st.success(f"已顯示 {shown}/{target_count} 筆推薦，可遞補 {pool} 筆，共 {total_pool} 筆可選")

    st.markdown("<hr style='border: 1px solid #2c3e50; margin: 20px 0;'>", unsafe_allow_html=True)
    st.write("© 2025 學測志願模擬器")

def main():
    """主程式"""
    programs_list, school_list, group_options = load_and_process_data()
    user_input = get_user_input(school_list, group_options)
    
    if user_input:
        with st.spinner("正在生成推薦志願..."):
            recommendation_data = generate_recommendations(user_input)
        display_recommendations(user_input, recommendation_data)
    else:
        st.info("請輸入成績、選擇學群並設置志願分配，然後點擊「模擬志願分發」按鈕。")

if __name__ == "__main__":
    main()

st.markdown("""
<hr style='margin-top:50px; margin-bottom:10px;'>

<div style='text-align: center; font-size: 0.9em; color: gray;'>
    <strong>2025 GSAT College & Department Recommendation System</strong><br>
    Developed by 李韵柔, 葉芷妤, 許紓嫻, 范可軒, 黃詠笙, 高湘宜.<br>
    © 2025 CollegeMatch Initiative. All rights reserved.
</div>
""", unsafe_allow_html=True)
