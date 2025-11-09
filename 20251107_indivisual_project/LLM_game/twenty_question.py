import streamlit as st
import random
import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

# # EEVE 모델 클라이언트 설정 (Upstage API)
# client = OpenAI(
#     api_key=os.environ.get("UPSTAGE_API_KEY"),
#     base_url="https://api.upstage.ai/v1/solar"
# )

st.set_page_config(page_title="EEVE와 20고개 게임", page_icon="🎮")
st.title("🎮 EEVE와 함께하는 낱말맞추기 20고개 게임")
st.write("EEVE가 생각한 단어를 예/아니오 질문으로 맞혀보세요! (최대 20번 질문 가능)")

# 카테고리별 단어 목록
WORD_CATEGORIES = {
    "동물": ["고양이", "강아지", "코끼리", "호랑이", "펭귄", "토끼", "원숭이", "거북이"],
    "음식": ["사과", "바나나", "김치", "라면", "피자", "커피", "빵", "초콜릿"],
    "사물": ["책상", "의자", "컴퓨터", "연필", "시계", "우산", "자동차", "전화기"],
}

# 세션 상태 초기화
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "word" not in st.session_state:
    st.session_state.word = None
if "category" not in st.session_state:
    st.session_state.category = None
if "qna" not in st.session_state:
    st.session_state.qna = []
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_history" not in st.session_state:
    st.session_state.game_history = []

# 게임 시작
if not st.session_state.game_started:
    st.subheader("카테고리를 선택하세요 👇")
    category = st.radio("단어 카테고리", list(WORD_CATEGORIES.keys()))

    if st.button("게임 시작 🎯"):
        st.session_state.category = category
        st.session_state.word = random.choice(WORD_CATEGORIES[category])
        st.session_state.qna = []
        st.session_state.question_count = 0
        st.session_state.game_over = False
        st.session_state.game_started = True
        st.success(f"'{category}' 카테고리에서 단어를 선택했습니다. 질문을 시작하세요!")
        st.experimental_rerun()

else:
    # 현재 진행 상태 표시
    st.info(f"🔢 질문 횟수: {st.session_state.question_count}/20")
    st.write(f"🎯 카테고리: **{st.session_state.category}**")

    if not st.session_state.game_over:
        question = st.text_input("질문을 입력하세요 (예: 먹을 수 있나요?)")

        # 질문 처리
        if st.button("질문하기"):
            if question:
                if st.session_state.question_count >= 20:
                    st.error("질문 제한(20번)을 초과했습니다! 😢 정답을 입력해보세요.")
                else:
                    system_prompt = f"너는 '{st.session_state.category}' 카테고리의 단어 '{st.session_state.word}'를 알고 있어. 사용자의 질문에 '예', '아니오', '모름' 중 하나로만 간단히 대답해."
                    user_prompt = f"질문: {question}"

                    response = client.chat.completions.create(
                        model="solar-1-mini-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.3
                    )
                    answer = response.choices[0].message.content.strip()
                    st.session_state.qna.append((question, answer))
                    st.session_state.question_count += 1
                    if st.session_state.question_count >= 20:
                        st.warning("질문 20번이 모두 사용되었습니다. 정답을 입력해보세요!")

            else:
                st.warning("질문을 입력해주세요!")

        # 정답 입력
        guess = st.text_input("정답을 입력해보세요 (예: 사과)")
        if st.button("정답 확인"):
            if guess.strip() == st.session_state.word:
                st.success(f"🎉 정답입니다! '{st.session_state.word}'를 맞히셨어요!")

                # EEVE에게 힌트 설명 요청
                hint_prompt = f"단어 '{st.session_state.word}'에 대한 간단한 설명(힌트)을 2~3문장으로 해줘. 사용자가 이걸 보고 알 수 있도록."
                hint_response = client.chat.completions.create(
                    model="solar-1-mini-chat",
                    messages=[
                        {"role": "system", "content": "너는 친절한 설명자야."},
                        {"role": "user", "content": hint_prompt},
                    ],
                    temperature=0.7
                )
                hint = hint_response.choices[0].message.content.strip()
                st.info(f"💡 힌트: {hint}")

                st.session_state.game_over = True

                # 게임 기록 저장
                st.session_state.game_history.append({
                    "category": st.session_state.category,
                    "word": st.session_state.word,
                    "question_count": st.session_state.question_count,
                    "success": True
                })

            else:
                st.error("틀렸습니다! 계속 질문해보세요.")

    # 질문/답변 내역 표시
    st.subheader("💬 질문/답변 기록")
    for i, (q, a) in enumerate(st.session_state.qna, 1):
        st.write(f"**Q{i}.** {q}")
        st.write(f"→ {a}")

    # 게임 리셋 버튼
    if st.button("🔄 새 게임 시작"):
        st.session_state.game_started = False
        st.experimental_rerun()

# 게임 기록
if st.session_state.game_history:
    st.subheader("📜 게임 기록")
    for i, record in enumerate(st.session_state.game_history, 1):
        result = "성공 ✅" if record["success"] else "실패 ❌"
        st.write(f"{i}. [{record['category']}] '{record['word']}' — 질문 {record['question_count']}회 — {result}")



# 실행하는 방법 
# export UPSTAGE_API_KEY="YOUR_API_KEY"
# streamlit run streamlit_app.py