import streamlit as st
from ollama import Ollama  # ollama 파이썬 클라이언트 필요, 실제 설치 및 세팅 요망

# Ollama LLM 클라이언트 초기화 (로컬 LLM 구동)
client = Ollama()

# EEVE-Korean-10.8B 모델 지정
MODEL_NAME = "eeve-korean-10.8b"

def ask_llm(question, chat_history):
    """
    LLM에 질문 및 대화내역 전달하고 답변 수신
    """
    messages = chat_history + [{"role": "user", "content": question}]
    response = client.chat(model=MODEL_NAME, messages=messages)
    return response['choices'][0]['message']['content']

def main():
    st.title("20고개 LLM과 게임 - EEVE AI 모델 사용")
    st.write("생각한 단어를 LLM이 20번 질문으로 맞추는 게임입니다.")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 0
    if 'game_over' not in st.session_state:
        st.session_state['game_over'] = False

    user_word = st.text_input("게임 시작 전, 당신이 생각한 단어를 입력하세요 (LLM에게는 비공개):")

    st.write("LLM이 질문을 하면 예/아니오로 대답해 주세요.")

    # LLM 질문 받고 출력
    if not st.session_state['game_over'] and user_word:
        if st.button("LLM 질문 받기"):
            question = ask_llm("단어를 맞추기 위해 한 가지 질문을 해주세요.", st.session_state['chat_history'])
            st.session_state['chat_history'].append({"role": "assistant", "content": question})
            st.session_state['question_count'] += 1
            st.experimental_rerun()

    # 게임 질문 표시 및 사용자 답변 입력
    if st.session_state['chat_history']:
        last_question = st.session_state['chat_history'][-1]['content']
        st.write(f"LLM 질문 {st.session_state['question_count']}: {last_question}")

        user_answer = st.radio("답변을 선택하세요", ("예", "아니오"))

        if st.button("답변 제출"):
            st.session_state['chat_history'].append({"role": "user", "content": user_answer})
            # 20회 질문 제한 체크
            if st.session_state['question_count'] >= 20:
                st.write("질문 횟수 초과: LLM이 맞추지 못했습니다. 당신의 승리!")
                st.session_state['game_over'] = True
            else:
                # LLM이 단어 추측 시도 (여기서 실제 단어 추측 로직은 LLM 메시지 포맷에 맞게 조절 필요)
                guess = ask_llm("이제 단어를 맞춰보세요.", st.session_state['chat_history'])
                if guess.strip() == user_word.strip():
                    st.write(f"LLM이 단어를 맞췄습니다! 정답: {guess}")
                    st.session_state['game_over'] = True
                else:
                    st.write(f"LLM의 단어 추측: {guess} (틀렸습니다)")

            st.experimental_rerun()

    if st.session_state['game_over']:
        if st.button("게임 다시 시작"):
            st.session_state.clear()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
