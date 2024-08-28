import multiprocessing
from multiprocessing import shared_memory

QUESTIONS = [
    {"question": "Qual a capital do Ceará?", "answer": "Fortaleza"},
    {"question": "Quanto é 2 + 2?", "answer": "4"},
    {"question": "Qual é a cor do céu?", "answer": "Azul"},
    {"question": "Qual a capital do Brasil?", "answer": "Brasilia"},
    {"question": "Qual a raiz quadrada de 16?", "answer": "4"}
]

def servidor(shm_name, lock):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    shared_data = existing_shm.buf
    
    scores = multiprocessing.Manager().dict()

    for i, q in enumerate(QUESTIONS):
        with lock:
            question_text = q["question"].encode('utf-8')
            shared_data[0:len(question_text)] = question_text
            shared_data[len(question_text):64] = b' ' * (64 - len(question_text))  # Limpa o espaço restante
            shared_data[64:128] = b' ' * 64  # Limpa a resposta anterior
            shared_data[128:132] = str(i).zfill(4).encode('utf-8')  # Identificador da pergunta (4 bytes)
            shared_data[132:136] = b' ' * 4  # Limpa o identificador do jogador

        print(f"[Servidor] Nova pergunta: {q['question']}")

        while True:
            with lock:
                received_answer = shared_data[64:128].tobytes().decode('utf-8').rstrip()
                player_id = shared_data[132:136].tobytes().decode('utf-8').rstrip()

            if received_answer and player_id:
                if received_answer.lower() == q["answer"].lower():
                    scores[player_id] = scores.get(player_id, 0) + 1
                    print(f"[Servidor] Jogador {player_id} respondeu corretamente e marcou 1 ponto!")
                break

    print("\n[Servidor] Pontuações Finais:")
    for player, score in scores.items():
        print(f"{player}: {score} pontos")

    existing_shm.close()

if __name__ == "__main__":
    lock = multiprocessing.Lock()
    
    shm = shared_memory.SharedMemory(create=True, size=136)
    print(f"Memória compartilhada criada com o nome: {shm.name}")
    shared_data = shm.buf

    server_process = multiprocessing.Process(target=servidor, args=(shm.name, lock))
    server_process.start()
    server_process.join()

    shm.close()
    shm.unlink()
