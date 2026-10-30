# -*- coding: utf-8 -*-
"""
진짜약 (Jinzzayak) - 약 성분표 OCR 대조 앱
requirements: streamlit>=1.40, easyocr, opencv-python-headless, pillow, pandas, numpy
"""
import base64
import contextlib
import gc
import html
import io
import logging
import re
import warnings
from datetime import datetime
from difflib import SequenceMatcher

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

warnings.filterwarnings("ignore")
logging.getLogger("easyocr").setLevel(logging.ERROR)

st.set_page_config(
    page_title="진짜약 · Jinzzayak",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ss = st.session_state
esc = html.escape

NAME, ING, MANUF, CODE = "Product Name", "Active Ingredient", "Manufacturer", "MTRAL_CC"
MAX_FILES = 6

# =========================================================
# 스타일
# =========================================================
CSS = """
<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");

:root{
  --red:#E5383B; --red-d:#C92A2D; --green:#12A150;
  --ink:#191F28; --sub:#4E5968; --mute:#8B95A1;
  --line:#E5E8EB; --bg:#F2F4F6; --soft:#F9FAFB;
}
html, body, .stApp, p, div, label, input, textarea, button, table, td, th {
  font-family:"Pretendard Variable",Pretendard,-apple-system,BlinkMacSystemFont,system-ui,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  letter-spacing:-0.01em;
}

/* Streamlit 기본 UI 숨김 */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu, footer, .stDeployButton,
[data-testid="InputInstructions"], [data-testid="stElementToolbar"] { display:none !important; }

/* 폰 프레임 */
.stApp { background:#E9ECEF; }
.block-container, [data-testid="stMainBlockContainer"]{
  max-width:440px !important; padding:0 20px 100px !important;
  background:#fff; min-height:100dvh;
}
@media (max-width:480px){ .stApp{ background:#fff; } }
[data-testid="stVerticalBlock"]{ gap:0.6rem; }

/* 모바일에서도 컬럼이 줄바꿈되지 않게 */
[data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; gap:8px !important; }
[data-testid="stColumn"], [data-testid="column"]{ min-width:0 !important; }

/* 버튼 공통 */
.stButton, .stFormSubmitButton{ width:100%; }
.stButton > button, .stFormSubmitButton > button{
  width:100%; min-height:50px; border-radius:12px;
  font-size:16px; font-weight:600; color:var(--ink);
  background:#fff; border:1px solid var(--line); box-shadow:none;
  transition:background .15s, transform .05s;
}
.stButton > button:hover, .stButton > button:focus:not(:active){ color:var(--ink); border-color:#D1D6DB; }
.stButton > button:active, .stFormSubmitButton > button:active{ transform:scale(.985); }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--red) !important; color:#fff !important; border:none !important;
}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover{
  background:var(--red-d) !important; color:#fff !important;
}

/* 검색 폼 전체 영역 */
[data-testid="stForm"]{ 
    border: none !important; 
    padding: 0 !important; 
}

/* 검색창과 버튼을 감싸는 블록: 간격(gap) 조절 가능 */
.st-key-searchrow [data-testid="stHorizontalBlock"]{ 
    display: flex !important;
    align-items: center !important; 
    gap: 12px !important; /* 회색박스와 빨간버튼 사이 간격 */
}

/* 회색 입력창(텍스트박스) 길이와 높이 맞춤 */
.stTextInput {
    width: 100% !important;
}
.stTextInput [data-baseweb="input"]{
    height: 46px !important; /* 위아래 높이를 슬림하게 조절 */
    border: 1.5px solid var(--line) !important; 
    border-radius: 12px !important;
    background: #fff !important; 
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
}
.stTextInput [data-baseweb="input"]:focus-within{ 
    border-color: var(--ink) !important; 
}
.stTextInput input{
    font-size: 15px !important; 
    color: var(--ink) !important; 
    padding: 0 14px !important;
    background: transparent !important; 
    border: none !important; 
    outline: none !important;
}
.stTextInput input::placeholder{ color: #B0B8C1 !important; }

/* 오른쪽 빨간색 검색 버튼: 회색 박스와 높이(46px)를 정확히 일치시킴 */
.st-key-searchrow .stFormSubmitButton {
    width: auto !important;
}
.st-key-searchrow .stFormSubmitButton > button{
    width: 65px !important; /* 버튼 가로 폭 */
    min-height: 35px !important; 
    height: 46px !important; 
    border-radius: 12px !important;
    font-size: 15px !important; 
    font-weight: 600 !important;
    background: var(--red) !important; 
    color: #fff !important;
    border: none !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.st-key-searchrow .stFormSubmitButton > button:hover{
    background: var(--red-d) !important;
}

/* 상단바: 아이콘과 글씨를 한 버튼에 넣어 정렬 */
.st-key-topbar{ position:sticky; top:0; z-index:50; background:#fff; padding:10px 0 6px; }
.st-key-topbar .stButton{ width:auto; }
.st-key-topbar .stButton > button{
  width:auto; min-height:44px; padding:0 6px 0 0; gap:8px;
  border:none !important; background:transparent !important; justify-content:flex-start;
}
.st-key-topbar button > div{ align-items:center; gap:8px; }
.st-key-topbar [data-testid="stIconMaterial"]{ font-size:26px; color:var(--ink); }
.st-key-topbar button p{ font-size:21px; font-weight:800; color:var(--ink); letter-spacing:-0.03em; line-height:1; margin:0; }
.st-key-tb_back button p{ font-size:18px; font-weight:700; }

/* 섹션 */
.sec{ display:flex; justify-content:space-between; align-items:baseline; margin:12px 0 0; }
.sec b{ font-size:15px; font-weight:700; color:var(--ink); }
.sec small{ font-size:12px; color:var(--mute); }
.sec.up{ margin:14px 0 10px; }
.empty{ color:var(--mute); font-size:14px; line-height:1.6; padding:14px 2px; }
.notice{
  background:var(--soft); border:1px solid var(--line); border-radius:14px;
  padding:22px 18px; text-align:center; color:var(--sub); font-size:15px; line-height:1.6;
}
.notice b{ color:var(--ink); display:block; font-size:16px; margin-bottom:4px; }
.err{ background:#FFF1F1; color:var(--red-d); border-radius:12px; padding:12px 14px; font-size:14px; }

/* 검색 기록 */
[data-testid="stButtonGroup"] button{ border-radius:999px !important; font-size:14px; }
.st-key-hist_clear .stButton > button{
  min-height:28px; border:none; background:transparent; color:var(--mute);
  font-size:13px; font-weight:500; justify-content:flex-end; padding:0;
}

/* 약품 목록 */
.st-key-reslist{ background:var(--bg); border-radius:14px; padding:4px 10px; }
.st-key-favlist{ background:var(--bg); border-radius:14px; padding:4px 10px; }
[class*="st-key-row_"], [class*="st-key-hrow_"]{ border-bottom:1px solid #E1E4E8; }
[class*="st-key-row_"]:last-child, [class*="st-key-hrow_"]:last-child{ border-bottom:none; }
[class*="st-key-res_"] .stButton > button, [class*="st-key-open_"] .stButton > button{
  background:transparent; border:none; min-height:48px; padding:0 4px;
  justify-content:flex-start; font-size:15px; font-weight:500;
}
[class*="st-key-res_"] button > div, [class*="st-key-open_"] button > div{ justify-content:flex-start; width:100%; }
[class*="st-key-res_"] button p, [class*="st-key-open_"] button p{
  text-align:left; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
[class*="st-key-bm_"] .stButton > button{
  background:transparent; border:none; min-height:44px; width:44px; padding:0;
}
[class*="st-key-bm_"] [data-testid="stIconMaterial"]{ font-size:22px; color:#B0B8C1; }
[class*="st-key-bmcon_"] [data-testid="stIconMaterial"]{ color:var(--red) !important; }

/* 적용된 약품 카드 */
.applied{ background:var(--soft); border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.applied .tag{ display:inline-block; font-size:11px; font-weight:700; color:var(--red);
  background:#FFECEC; border-radius:6px; padding:2px 7px; margin-bottom:5px; }
.applied .nm{ font-size:16px; font-weight:700; color:var(--ink); line-height:1.4; }
.applied .meta{ font-size:12.5px; color:var(--mute); margin-top:2px; line-height:1.5; }

/* 업로드 박스 */
[class*="st-key-upwrap"]{ margin-top:4px; }
.st-key-upwrap{ margin-top:12px; }
[class*="st-key-upwrap"] [data-testid="stFileUploaderDropzone"]{
  position:relative; min-height:60px; border:1.5px dashed #CDD2D8; background:var(--bg);
  border-radius:14px; display:flex; align-items:center; justify-content:center; padding:0;
}
.st-key-upwrap_empty [data-testid="stFileUploaderDropzone"]{ min-height:110px; }
[class*="st-key-upwrap"] [data-testid="stFileUploaderDropzoneInstructions"]{ display:none; }
[class*="st-key-upwrap"] [data-testid="stFileUploaderDropzone"] button{
  position:absolute; inset:0; width:100%; height:100%; opacity:0; z-index:2; cursor:pointer;
}
[class*="st-key-upwrap"] [data-testid="stFileUploaderDropzone"]::after{
  content:"+ 사진 추가"; font-size:15px; font-weight:600; color:var(--mute); pointer-events:none;
}
[class*="st-key-upwrap"] [data-testid="stFileUploaderFile"],
[class*="st-key-upwrap"] [data-testid="stFileUploaderPagination"]{ display:none; }

/* 업로드된 사진 (작게, X는 우측 상단) */
[class*="st-key-chip_"]{ position:relative; gap:0 !important; }
.chip img{ width:100%; aspect-ratio:1; object-fit:cover; display:block;
  border-radius:10px; border:1px solid var(--line); background:var(--bg); }
.chip .n{ font-size:11px; font-weight:600; color:var(--ink); margin-top:4px; line-height:1.2;
  letter-spacing:-0.02em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.chip .s{ font-size:10px; color:var(--mute); line-height:1.2; margin-top:1px; letter-spacing:-0.01em; }
[class*="st-key-rm_"]{ position:absolute !important; top:4px; right:4px; width:auto !important; z-index:5; }
[class*="st-key-rm_"] .stButton{ width:auto; }
[class*="st-key-rm_"] .stButton > button{
  width:22px; height:22px; min-height:22px; padding:0; border-radius:50%;
  background:rgba(25,31,40,.72) !important; border:none !important;
}
[class*="st-key-rm_"] [data-testid="stIconMaterial"]{ font-size:14px; color:#fff; }

/* 성분 비교 (빨간 테두리, 조금 더 짧게) */
.st-key-btn_compare{ margin-top:6px; }
.st-key-btn_compare, .st-key-btn_compare .stButton{ width:100% !important; display:flex; justify-content:center; }
.st-key-btn_compare .stButton > button{
  width:86% !important; min-width:220px; white-space:nowrap;
  border:1.5px solid var(--red) !important; color:var(--red) !important; background:#fff;
}
.st-key-btn_compare button p{ white-space:nowrap; }

/* 분석 중 */
.analyzing{ min-height:calc(100dvh - 40px); display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; }
.scanbox{ position:relative; width:200px; height:200px; border-radius:22px; overflow:hidden;
  background:var(--bg); box-shadow:0 8px 28px rgba(0,0,0,.08); }
.scanbox img{ width:100%; height:100%; object-fit:cover; }
.scanbox::after{ content:""; position:absolute; left:0; right:0; height:3px; background:var(--red);
  box-shadow:0 0 14px var(--red); animation:scan 1.8s ease-in-out infinite; }
@keyframes scan{ 0%{top:0} 50%{top:calc(100% - 3px)} 100%{top:0} }
.an-t{ font-size:18px; font-weight:700; color:var(--ink); margin-top:26px; white-space:nowrap; }
.dots b{ font-weight:700; opacity:0; animation-duration:1.6s; animation-iteration-count:infinite; }
.dots b:nth-child(1){ animation-name:d1; }
.dots b:nth-child(2){ animation-name:d2; }
.dots b:nth-child(3){ animation-name:d3; }
@keyframes d1{ 0%,10%{opacity:0} 15%,100%{opacity:1} }
@keyframes d2{ 0%,40%{opacity:0} 45%,100%{opacity:1} }
@keyframes d3{ 0%,70%{opacity:0} 75%,100%{opacity:1} }
.an-s{ color:var(--mute); font-size:13px; margin-top:6px; line-height:1.6; }

/* 결과 */
.r-title{ font-size:25px; font-weight:800; color:var(--ink); letter-spacing:-0.035em; margin:6px 0 4px; }
.r-drug{ color:var(--mute); font-size:14px; margin-bottom:6px; }
.r-item{ padding:18px 0; border-bottom:1px solid var(--line); }
.r-item:last-child{ border-bottom:none; }
.r-label{ display:block; font-size:13px; color:var(--mute); font-weight:500; margin-bottom:4px; }
.r-value{ font-size:30px; font-weight:800; letter-spacing:-0.03em; line-height:1.25; }
.r-value.sm{ font-size:24px; }
.ok{ color:var(--green); } .bad{ color:var(--red); }
.bar{ height:6px; background:var(--bg); border-radius:99px; margin-top:10px; overflow:hidden; }
.bar i{ display:block; height:100%; border-radius:99px; }
[class*="st-key-light_"] .stButton > button{
  background:var(--bg) !important; border:none !important; color:var(--sub) !important; font-weight:500;
}

/* 리포트 표 */
.rpt-h{ font-size:22px; font-weight:800; color:var(--ink); letter-spacing:-0.03em; margin:4px 0 12px; }
.rpt{ width:100%; border-collapse:separate; border-spacing:0; border:1px solid var(--line);
  border-radius:12px; overflow:hidden; font-size:13px; table-layout:fixed; }
.rpt th{ background:var(--soft); color:var(--mute); font-weight:500; text-align:left; padding:10px 8px; font-size:12px; }
.rpt td{ padding:11px 8px; border-top:1px solid var(--line); color:var(--ink); word-break:break-all; vertical-align:top; }
.rpt td.k{ color:var(--sub); }
.rpt .pct{ display:block; font-size:11px; color:var(--mute); margin-top:2px; }
.fine{ font-size:12px; color:var(--mute); line-height:1.6; margin-top:6px; }

/* 메뉴 화면 */
.st-key-drawer{ animation:fadein .2s ease-out; }
@keyframes fadein{ from{ opacity:0; margin-left:-16px } to{ opacity:1; margin-left:0 } }
.st-key-drawer [class*="st-key-dr_"] .stButton > button{
  border:none; background:transparent; justify-content:flex-start; font-size:17px; font-weight:700;
  min-height:56px; padding:0 4px; border-bottom:1px solid var(--line); border-radius:0;
}
.st-key-drawer [class*="st-key-dr_"] button > div{ justify-content:flex-start; gap:10px; }
.st-key-drawer [class*="st-key-dr_"] [data-testid="stIconMaterial"]{ font-size:22px; color:var(--sub); }

/* 메뉴 하단 고정: 마이메뉴(왼쪽) / 설정(오른쪽) */
.st-key-drawer_bottom{
  position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:100%; max-width:440px;
  background:#fff; border-top:1px solid var(--line);
  padding:6px 20px calc(6px + env(safe-area-inset-bottom)); z-index:100;
}
.st-key-drawer_bottom .stButton > button{
  border:none; background:transparent; font-size:15px; font-weight:600; color:var(--sub); min-height:52px; padding:0;
}
.st-key-db_my .stButton > button, .st-key-db_my button > div{ justify-content:flex-start; }
.st-key-db_set .stButton > button, .st-key-db_set button > div{ justify-content:flex-end; }

/* 설정 */
.set-sec{ font-size:13px; color:var(--mute); font-weight:600; margin:18px 0 2px; }
.stToggle label p{ font-size:15px; color:var(--ink); }

/* 결과 화면 버튼 우측 정렬 */
.st-key-btn_report, 
[class*="st-key-light_"] {
    display: flex !important;
    justify-content: flex-end !important;
}
.st-key-btn_report .stButton > button, 
[class*="st-key-light_"] .stButton > button {
    margin-left: auto !important;
    margin-right: 0 !important;
    min-width: 220px !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# 텍스트 정규화 / 성분 별칭
# =========================================================
def normalize(s):
    return re.sub(r"[^0-9a-z가-힣]", "", str(s).lower())


_ALIAS_GROUPS = [
    ["acetaminophen", "아세트아미노펜", "paracetamol", "파라세타몰"],
    ["ibuprofen", "이부프로펜"],
    ["dexibuprofen", "덱시부프로펜"],
    ["naproxen", "나프록센"],
    ["aspirin", "아스피린", "acetylsalicylic acid", "아세틸살리실산"],
    ["caffeine", "카페인", "무수카페인", "caffeine anhydrous"],
    ["glucose", "포도당", "dextrose", "덱스트로오스"],
    ["loratadine", "로라타딘"],
    ["cetirizine", "세티리진"],
    ["fexofenadine", "펙소페나딘"],
    ["chlorpheniramine", "클로르페니라민"],
    ["pseudoephedrine", "슈도에페드린"],
    ["dextromethorphan", "덱스트로메토르판"],
    ["guaifenesin", "구아이페네신"],
    ["famotidine", "파모티딘"],
    ["omeprazole", "오메프라졸"],
    ["esomeprazole", "에스오메프라졸"],
    ["metformin", "메트포르민"],
    ["amlodipine", "암로디핀"],
    ["atorvastatin", "아토르바스타틴"],
    ["rosuvastatin", "로수바스타틴"],
    ["loperamide", "로페라미드"],
    ["simethicone", "시메티콘", "시메치콘"],
    ["magnesium oxide", "산화마그네슘"],
    ["sodium chloride", "염화나트륨"],
    ["ascorbic acid", "아스코르브산", "아스코르빈산", "비타민c", "vitamin c"],
]
ALIAS = {}
for _g in _ALIAS_GROUPS:
    for _w in _g:
        ALIAS[normalize(_w)] = _g

UNIT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:mg|mcg|μg|ug|g|ml|iu|%|밀리그램|그램|㎎|㎖)", re.I)


def split_ingredients(s):
    """'아세트아미노펜(Acetaminophen) 500mg, 카페인' -> [[아세트아미노펜, Acetaminophen], [카페인]]"""
    if not s:
        return []
    s = UNIT_RE.sub(" ", s)
    groups = []
    for p in re.split(r"[,/;+·|\n]|\s및\s|\sand\s", s):
        p = p.strip(" .-")
        if not p:
            continue
        inner = re.findall(r"\(([^)]*)\)", p)
        outer = re.sub(r"\([^)]*\)", " ", p).strip()
        names = [x.strip() for x in [outer] + inner if len(normalize(x)) >= 2]
        if names:
            groups.append(names)
    return groups


def expand_aliases(names):
    out = list(names)
    for n in names:
        out += ALIAS.get(normalize(n), [])
    seen, uniq = set(), []
    for o in out:
        k = normalize(o)
        if k and k not in seen:
            seen.add(k)
            uniq.append(k)
    return uniq


def fuzzy_find(token, text):
    """정규화된 OCR 전문에서 token과 가장 비슷한 조각을 찾아 (유사도, 조각) 반환"""
    if len(token) < 2 or not text:
        return 0.0, ""
    if token in text:
        return 1.0, token
    sm = SequenceMatcher(autojunk=False)
    sm.set_seq2(token)
    m, best, frag = len(token), 0.0, ""
    for size in range(max(2, m - 2), m + 3):
        for i in range(0, max(1, len(text) - size + 1)):
            sm.set_seq1(text[i:i + size])
            if sm.real_quick_ratio() <= best or sm.quick_ratio() <= best:
                continue
            r = sm.ratio()
            if r > best:
                best, frag = r, text[i:i + size]
    return best, frag


_CONFUSE = str.maketrans("OoDQIil|SsBZz", "0000111155822")


def digit_stream(text):
    """OCR이 숫자를 문자로 잘못 읽는 경우(O->0, l->1 등)를 보정한 숫자열"""
    runs = re.findall(r"[0-9OoDQIil|SsBZz]{3,}", text)
    good = [r for r in runs if sum(ch.isdigit() for ch in r) >= len(r) / 2]
    return "".join(r.translate(_CONFUSE) for r in good)


def normalize_company(s):
    s = re.sub(r"\(주\)|㈜|주식회사|\(유\)|유한회사|co\.?,?\s*ltd\.?|inc\.?", "", str(s), flags=re.I)
    return normalize(s)


# =========================================================
# 데이터
# =========================================================
@st.cache_data(show_spinner=False)
def load_drug_data(path="drugs.csv"):
    df = None
    for enc in ("utf-8-sig", "cp949"):
        try:
            df = pd.read_csv(path, encoding=enc, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("drugs.csv 인코딩을 읽을 수 없습니다.")
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    for c in (NAME, ING, MANUF, CODE):
        if c not in df.columns:
            df[c] = ""
    df[CODE] = df[CODE].str.replace(r"\.0$", "", regex=True)
    df = df[df[NAME] != ""].drop_duplicates(subset=[NAME]).reset_index(drop=True)
    df["_n"] = df[NAME].map(normalize)
    df["_i"] = df[ING].map(normalize)
    return df


try:
    DF = load_drug_data()
except Exception as e:
    st.markdown(
        '<div class="err">drugs.csv 파일을 불러오지 못했습니다.<br>' + esc(str(e)) + "</div>",
        unsafe_allow_html=True,
    )
    st.stop()


def has_code(code):
    """품목기준코드가 비었거나 null 계열이면 False"""
    return str(code).strip().lower() not in ("", "nan", "null", "none", "-", "0")


def to_rec(row):
    return {"name": row[NAME], "ingredient": row[ING], "manufacturer": row[MANUF], "code": row[CODE]}


def search_drugs(q, limit=50):
    nq = normalize(q)
    if not nq:
        return [], 0
    mask = DF["_n"].str.contains(nq, regex=False) | DF["_i"].str.contains(nq, regex=False)
    hit = DF[mask].copy()
    if hit.empty:
        return [], 0
    hit["_r"] = np.select([hit["_n"] == nq, hit["_n"].str.startswith(nq)], [0, 1], 2)
    hit = hit.sort_values(["_r", NAME])
    return [to_rec(r) for _, r in hit.head(limit).iterrows()], len(hit)


# =========================================================
# OCR
# =========================================================
@st.cache_resource(show_spinner=False)
def get_ocr_reader():
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        import easyocr
        return easyocr.Reader(["ko", "en"], gpu=False, verbose=False)


def preprocess(pil, variant):
    img
