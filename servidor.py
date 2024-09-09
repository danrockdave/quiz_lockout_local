import multiprocessing
from multiprocessing import shared_memory
import os

# Lista de perguntas e respostas que o servidor vai enviar aos clientes
QUESTIONS = [
    {"question": "\nQual a capital do Ceará?\nA: Fortaleza\nB: Itapipoca\nC: Maranguape\nD: Caucaia\n", "answer": "A"},
    {"question": "\nQuanto é 2 + 2?\nA: 1\nB: 2\nC: 3\nD: 4\n", "answer": "D"},
    {"question": "\nQual é a cor do céu?\nA: Amarelo\nB: Azul\nC: Vermelho\nD: Roxo\n", "answer": "B"},
    {"question": "\nQual a capital do Brasil?\nA: São Paulo\nB: Fortaleza\nC: Rio de Janeiro\nD: Brasília\n", "answer": "D"},
    {"question": "\nQual a raiz quadrada de 16?\nA: 8\nB: 2\nC: 4\nD: 12\n", "answer": "C"}
]

# Função principal do servidor, responsável por controlar o jogo
def servidor(shm_name, lock, player_count):
    # Conecta à memória compartilhada já criada
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    shared_data = existing_shm.buf

    # Dicionário para armazenar as pontuações dos jogadores
    scores = multiprocessing.Manager().dict()

    # Para cada pergunta na lista de QUESTIONS
    for i, q in enumerate(QUESTIONS):
        with lock:
            # Escreve a pergunta na memória compartilhada, convertendo-a para bytes
            question_text = q["question"].encode('utf-8')
            shared_data[0:len(question_text)] = question_text
            
            # Limpa o espaço restante da pergunta no buffer (caso a pergunta anterior fosse maior)
            shared_data[len(question_text):256] = b' ' * (256 - len(question_text))
            
            # Limpa o espaço onde será escrita a resposta do jogador
            shared_data[256:320] = b' ' * 64
            
            # Escreve o número da pergunta na memória compartilhada
            shared_data[320:324] = str(i).zfill(4).encode('utf-8')
            
            # Limpa o espaço onde será armazenado o identificador do jogador
            shared_data[324:328] = b' ' * 4

        print(f"[Servidor] Nova pergunta: {q['question']}")

        while True:
            with lock:
                # Lê a resposta que o cliente escreveu na memória compartilhada
                received_answer = shared_data[256:320].tobytes().decode('utf-8').rstrip()
                
                # Lê o identificador do jogador (Jogador 1, Jogador 2, etc.)
                player_id = shared_data[324:328].tobytes().decode('utf-8').rstrip()

            # Se o jogador já enviou uma resposta e um identificador
            if received_answer and player_id:
                # Verifica se a resposta está correta
                if received_answer.lower() == q["answer"].lower():
                    # Adiciona 1 ponto ao jogador se a resposta estiver certa
                    scores[player_id] = scores.get(player_id, 0) + 1
                    print(f"[Servidor] Jogador {player_id} respondeu corretamente e marcou 1 ponto!")
                else:
                    print(f"[Servidor] Jogador {player_id} respondeu incorretamente.")
                break  # Sai do loop para enviar a próxima pergunta

    # Exibe as pontuações finais após todas as perguntas terem sido feitas
    print("\n[Servidor] Pontuações Finais:")
    player_winner = ''
    higher_score = 0
    for player, score in scores.items():
        if score > higher_score:
            player_winner = player
            higher_score = score
        print(f"{player}: {score} pontos")
    
    # Marca o jogo como "ACABOU" e grava o nome do vencedor na memória compartilhada
    shared_data[328:334] = b"ACABOU"
    shared_data[334:334+len(player_winner)] = player_winner.encode('utf-8')

    print("[Servidor] Todas as perguntas foram respondidas. O jogo terminou.")
    existing_shm.close()

if __name__ == "__main__":
    lock = multiprocessing.Lock()

    # Cria a memória compartilhada que será usada para armazenar as perguntas e respostas
    shm = shared_memory.SharedMemory(create=True, size=339)
    print(f"Memória compartilhada criada com o nome: {shm.name}")
    shared_data = shm.buf

    # Grava o nome da memória compartilhada em um arquivo para que os clientes possam acessar
    with open("shm_name.txt", "w") as f:
        f.write(shm.name)

    # Quando o servidor inicia, reseta o arquivo de contagem de jogadores para começar do zero
    with open("player_count.txt", "w") as f:
        f.write("0")

    # Inicia o processo do servidor, que vai controlar o jogo
    server_process = multiprocessing.Process(target=servidor, args=(shm.name, lock, None))
    server_process.start()
    server_process.join()

    shm.close()
    shm.unlink()
