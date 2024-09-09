import multiprocessing
from multiprocessing import shared_memory
import time

def cliente(shm_name, lock):
    # Conecta-se à memória compartilhada usando o nome fornecido pelo servidor
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    shared_data = existing_shm.buf

    # Atribui um nome ao jogador (Jogador 1, Jogador 2, etc.) com base no valor no arquivo player_count.txt
    with open("player_count.txt", "r+") as f:
        # Lê o valor atual no arquivo, que indica quantos jogadores já se conectaram
        count = int(f.read().strip())
        
        # O novo jogador recebe um nome com base no valor atual
        player_name = f"Jogador {count + 1}"
        
        # Atualiza o arquivo com o novo valor para o próximo jogador
        f.seek(0)
        f.write(str(count + 1))

    last_question_id = -1  # Variável que guarda o ID da última pergunta recebida

    while True:
        with lock:
            # Lê a pergunta da memória compartilhada, que foi escrita pelo servidor
            question = shared_data[0:256].tobytes().decode('utf-8').rstrip()
            # Lê o ID da pergunta atual
            question_id = shared_data[320:324].tobytes().decode('utf-8').rstrip()

        # Verifica se a pergunta já foi respondida e se o jogo terminou
        if question_id == last_question_id:
            # Verifica se o jogo acabou (quando o servidor escreve "ACABOU" na memória)
            if shared_data[328:334].tobytes().decode('utf-8').rstrip() == 'ACABOU':
                # Verifica se o jogador atual é o vencedor
                winner_name_length = len(shared_data[334:338].tobytes().decode('utf-8').rstrip())
                if shared_data[334:334+winner_name_length].tobytes().decode('utf-8').rstrip() == player_name:
                    print(f"{player_name} ganhou!")
                else:
                    print(f"{shared_data[334:334+winner_name_length].tobytes().decode('utf-8').rstrip()} ganhou!")
                break  # Sai do loop e encerra o jogo
            time.sleep(1)  # Espera um pouco antes de tentar ler a memória novamente
            continue

        last_question_id = question_id  # Atualiza o ID da última pergunta recebida

        # Exibe a pergunta ao jogador
        print(f"{player_name} recebeu a pergunta: {question}")
        
        # Solicita a resposta do jogador
        answer = input(f"{player_name}, digite sua resposta (A, B, C, ou D): ")
        
        with lock:
            # Armazena a resposta do jogador na memória compartilhada para que o servidor possa ler
            shared_data[256:320] = answer.encode('utf-8') + b' ' * (64 - len(answer))
            
            # Armazena o nome do jogador (truncado para caber em 4 bytes)
            player_name_bytes = player_name.encode('utf-8')[:4]
            player_name_bytes += b' ' * (4 - len(player_name_bytes))  # Preenche o restante dos 4 bytes com espaços
            shared_data[324:328] = player_name_bytes  # Escreve o nome do jogador na memória
            
            # Incrementa o contador de respostas
            response_count = int(shared_data[340:344].tobytes().decode('utf-8'))
            shared_data[340:344] = str(response_count + 1).zfill(4).encode('utf-8')

    existing_shm.close()  # Fecha a conexão com a memória compartilhada

if __name__ == "__main__":
    lock = multiprocessing.Lock()  # Cria um lock para controlar o acesso à memória compartilhada
    
    # Lê o nome da memória compartilhada a partir do arquivo gerado pelo servidor
    with open("shm_name.txt", "r") as f:
        shm_name = f.read().strip()

    # Executa o cliente
    cliente(shm_name, lock)
