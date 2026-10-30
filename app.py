    st.markdown(
        '<div class="rpt-h">상세 항목별 대조 리포트</div>'
        '<table class="rpt"><colgroup><col style="width:22%"><col style="width:28%">'
        '<col style="width:32%"><col style="width:18%"></colgroup>'
        "<thead><tr><th>검증 항목</th><th>기준 DB (정품)</th><th>이미지 OCR 검출값</th><th>검증 결과</th></tr></thead>"
        "<tbody>" + body + "</tbody></table>"
        '<div class="fine">사진 속 글자 인식(OCR) 결과를 기준 데이터와 비교한 참고용 판정입니다. '
        "조명·초점에 따라 결과가 달라질 수 있으니, 의심되면 약사 또는 의약품안전나라에서 한 번 더 확인해주세요.</div>",
        unsafe_allow_html=True,
    )
