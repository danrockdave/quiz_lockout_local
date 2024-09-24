import multiprocessing
from multiprocessing import shared_memory
import time

# Define as perguntas e respostas.
QUESTIONS = [
    {"question": "\nQual a capital do Ceará?\nA: Fortaleza\nB: Itapipoca\nC: Maranguape\nD: Caucaia\n", "answer": "A"},
    {"question": "\nQuanto é 2 + 2?\nA: 1\nB: 2\nC: 3\nD: 4\n", "answer": "D"},
    {"question": "\nQual é a cor do céu?\nA: Amarelo\nB: Azul\nC: Vermelho\nD: Roxo\n", "answer": "B"},
    {"question": "\nQual a capital do Brasil?\nA: São Paulo\nB: Fortaleza\nC: Rio de Janeiro\nD: Brasília\n", "answer": "D"},
    {"question": "\nQual a raiz quadrada de 16?\nA: 8\nB: 2\nC: 4\nD: 12\n", "answer": "C"}
]

# Função do servidor para controlar o fluxo do jogo.
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
            correct_answer_given = False
            
            # Limpa o espaço restante da pergunta no buffer (caso a pergunta anterior fosse maior)
            shared_data[len(question_text):256] = b' ' * (256 - len(question_text))
            
            # Limpa o espaço onde será escrita a resposta do jogador
            shared_data[256:320] = b' ' * 64
            
            # Escreve o número da pergunta na memória compartilhada
            shared_data[320:324] = str(i).zfill(4).encode('utf-8')
            
            # Limpa o espaço onde será armazenado o identificador do jogador
            shared_data[324:328] = b' ' * 4
            
            # Reseta o contador de respostas
            shared_data[340:344] = b'0000'

            # Reseta a flag de resposta correta
            shared_data[344:348] = b'0000'  # Inicializando com "não respondido"

            shared_data[349:358] = b' ' * 9  # Limpa o identificador do jogador

        print(f"[Servidor] Nova pergunta: {q['question']}")

        # Processa as respostas recebidas
        while True:
            with lock:
                response_count = int(shared_data[340:344].tobytes().decode('utf-8'))
                for player_id in range(1, player_count + 1):
                    received_answer = shared_data[256:320].tobytes().decode('utf-8').rstrip()

                    # Verifica se a resposta está correta e nenhuma resposta correta foi dada anteriormente
                    if received_answer.lower() == q["answer"].lower() and not correct_answer_given:
                        player_id_str = shared_data[349:358].tobytes().decode('utf-8').rstrip()
                        # Adiciona 1 ponto ao jogador se a resposta estiver certa
                        scores[player_id_str] = scores.get(player_id_str, 0) + 1
                        shared_data[344:348] = b'0001'  # Marca que a resposta correta foi dada
                        print(f"[Servidor] {player_id_str} respondeu corretamente primeiro e marcou 1 ponto!")
                        correct_answer_given = True
                        break  # Sai do loop após encontrar a primeira resposta correta
                
                if response_count >= player_count:
                    break

    # Determina o jogador com a maior pontuação
    max_score = max(scores.values(), default=0)
    winners = [player for player, score in scores.items() if score == max_score]

    print("\n[Servidor] Pontuações Finais:")
    for player_id, score in scores.items():
        print(f"{player_id}: {score} pontos")
    if winners:
        print(f"O vencedor é: {', '.join(winners)} com {max_score} pontos.")

    # Marca o jogo como "ACABOU" e grava o nome do vencedor na memória compartilhada
    shared_data[328:334] = b"ACABOU"

    # Converte o nome do vencedor em bytes e escreve na memória compartilhada
    if winners:
        winner_name = winners[0].encode('utf-8')
        shared_data[334:334 + len(winner_name)] = winner_name  # Escreve o nome do vencedor
        # Preenche o restante do espaço com espaços em branco para evitar dados residuais
        shared_data[334 + len(winner_name):354] = b' ' * (354 - (334 + len(winner_name)))

    existing_shm.close()

if __name__ == "__main__":
    lock = multiprocessing.Lock()

    # Cria a memória compartilhada que será usada para armazenar as perguntas e respostas
    shm = shared_memory.SharedMemory(create=True, size=358, )
    print(f"Memória compartilhada criada com o nome: {shm.name}")
    shared_data = shm.buf

    # Grava o nome da memória compartilhada em um arquivo para que os clientes possam acessar
    with open("shm_name.txt", "w") as f:
        f.write(shm.name)

    # Quando o servidor inicia, reseta o arquivo de contagem de jogadores para começar do zero
    with open("player_count.txt", "w") as f:
        f.write("0")

    # Define o número de jogadores esperados
    player_count = 4

    # Inicia o processo do servidor, que vai controlar o jogo
    server_process = multiprocessing.Process(target=servidor, args=(shm.name, lock, player_count))
    server_process.start()
    server_process.join()

    shm.close()
    shm.unlink()
