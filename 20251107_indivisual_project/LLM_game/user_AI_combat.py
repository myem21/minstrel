import streamlit as st
import random
import os
import csv
from datetime import datetime
from openai import OpenAI

# EEVE API 설정
client = OpenAI(
    api_key=os.environ.get("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1/solar"
)

st.set_page_config(page_title="EEVE 20고개 - 대결모드", page_icon="🤖")
st.title("🤖 EEVE vs 2명 플레이어 낱말맞추기 대결")

st.write("두 명의 플레이어가 단어를 정하면 EEVE가 맞히는 대결입니다.")
st.info("EEVE가 질문을 던지고, 플레이어는 예/아니오/모름으로만 대답하세요. 3판 2선승제 ⚔️")

# 난이도별 단어 후보 (플레이어 참고용)
WORD_LIST = {
    "쉬움": ["사과", "고양이", "컴퓨터", "책", "물", "자동차"],
    "보통": ["냉장고", "코끼리", "피아노", "비행기", "커피", "초콜릿"],
    "어려움": ["현미경", "성운", "메아리", "감정", "시간", "인터넷"],
}

# 세션 초기화
if "round" not in st.session_state:
    st.session_state.round = 1
if "scores" not in st.session_state:
    st.session_state.scores = {"Player 1": 0, "Player 2": 0}
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "player_words" not in st.session_state:
    st.session_state.player_words = {}
if "difficulty" not in st.session_state:
    st.session_state.difficulty = None
if "history" not in st.session_state:
    st.session_state.history = []

# 난이도 선택
if not st.session_state.difficulty:
    st.subheader(f"⚙️ {st.session_state.round}라운드 난이도 선택")
    difficulty = st.radio("단어 난이도 선택", ["쉬움", "보통", "어려움"])
    if st.button("시작하기 🚀"):
        st.session_state.difficulty = difficulty
        st.experimental_rerun()

# 플레이어 단어 입력
elif len(st.session_state.player_words) < 2:
    st.subheader(f"🧩 {st.session_state.difficulty} 난이도 — 플레이어 단어 설정")

    col1, col2 = st.columns(2)
    with col1:
        word1 = st.text_input("Player 1 단어 입력", type="password")
    with col2:
        word2 = st.text_input("Player 2 단어 입력", type="password")

    if st.button("단어 확정 ✅"):
        if word1 and word2:
            st.session_state.player_words = {"Player 1": word1, "Player 2": word2}
            st.success("두 플레이어의 단어가 설정되었습니다. 이제 EEVE가 맞힙니다!")
            st.experimental_rerun()
        else:
            st.warning("두 단어 모두 입력해주세요!")

# EEVE 질문 및 맞추기
elif not st.session_state.game_over:
    st.subheader(f"🎮 {st.session_state.round}라운드 — EEVE의 도전!")

    for player in ["Player 1", "Player 2"]:
        word = st.session_state.player_words[player]
        st.write(f"🤖 **{player}의 단어를 맞히는 중...**")

        # EEVE가 5개의 질문을 생성
        system_prompt = f"너는 20고개 게임을 하는 AI야. '{word}'를 맞혀야 해. 단, '예/아니오/모름'으로만 답할 수 있는 질문 5개를 만들어."
        q_response = client.chat.completions.create(
            model="solar-1-mini-chat",
            messages=[
                {"role": "system", "content": "너는 퀴즈 마스터야."},
                {"role": "user", "content": system_prompt},
            ],
            temperature=0.7
        )
        questions = [q.strip("-• \n") for q in q_response.choices[0].message.content.split("\n") if q.strip()]

        st.write("🤔 EEVE의 질문:")
        for i, q in enumerate(questions[:5], 1):
            st.write(f"{i}. {q}")

        # 플레이어의 대답 입력
        st.write("🗣️ 각 질문에 대해 '예', '아니오', '모름' 중 하나로 대답해주세요.")
        answers = []
        for i, q in enumerate(questions[:5], 1):
            a = st.selectbox(f"{player} → {q}", ["예", "아니오", "모름"], key=f"{player}_q{i}")
            answers.append(a)

        if st.button(f"{player} 답변 전송 🚀", key=f"send_{player}"):
            qa_summary = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
            guess_prompt = f"다음은 플레이어의 단어에 대한 Q&A입니다:\n{qa_summary}\n\n이 단어가 무엇인지 추측해봐. 가능한 한 단어 하나로 대답해."
            g_response = client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[
                    {"role": "system", "content": "너는 추리하는 인공지능이야."},
                    {"role": "user", "content": guess_prompt},
                ],
                temperature=0.5
            )
            guess = g_response.choices[0].message.content.strip()
            st.write(f"🤖 EEVE의 추측: **{guess}**")

            if guess == word:
                st.success(f"✅ EEVE가 {player}의 단어 '{word}'를 맞혔습니다!")
                st.session_state.scores[player] += 1
            else:
                st.error(f"❌ EEVE가 틀렸습니다! (정답: {word})")

            st.session_state.history.append({
                "round": st.session_state.round,
                "player": player,
                "word": word,
                "guess": guess,
                "result": guess == word
            })

    # 라운드 종료
    st.session_state.round += 1
    st.session_state.player_words = {}
    st.session_state.difficulty = None

    # 3판 2선승 판단
    if st.session_state.scores["Player 1"] >= 2 or st.session_state.scores["Player 2"] >= 2:
        st.session_state.game_over = True

    st.experimental_rerun()

# 게임 종료
else:
    st.header("🏁 경기 종료!")
    winner = max(st.session_state.scores, key=st.session_state.scores.get)
    st.success(f"🎉 최종 승자는 {winner}입니다!")
    st.write(f"스코어: {st.session_state.scores}")

    # CSV 저장
    filename = f"game_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["round", "player", "word", "guess", "result"])
        writer.writeheader()
        writer.writerows(st.session_state.history)
    st.info(f"📁 게임 기록이 CSV 파일로 저장되었습니다: `{filename}`")

    # 리셋 버튼
    if st.button("🔄 새 경기 시작"):
        st.session_state.round = 1
        st.session_state.scores = {"Player 1": 0, "Player 2": 0}
        st.session_state.game_over = False
        st.session_state.player_words = {}
        st.session_state.difficulty = None
        st.session_state.history = []
        st.experimental_rerun()
