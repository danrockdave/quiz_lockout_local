import multiprocessing
from multiprocessing import shared_memory
import time
import random

def cliente(name, shm_name, lock):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    shared_data = existing_shm.buf
    
    while True:
        with lock:
            question = shared_data[0:64].tobytes().decode('utf-8').rstrip()
            question_id = shared_data[128:132].tobytes().decode('utf-8').rstrip()
            previous_player = shared_data[132:136].tobytes().decode('utf-8').rstrip()

        if question:
            print(f"{name} recebeu a pergunta: {question}")
            # Simular uma resposta automática
            possible_answers = ["Fortaleza", "Sobral", "Juazeiro do Norte", "Quixadá"]
            answer = random.choice(possible_answers)
            print(f"{name} envia resposta simulada: {answer}")

            with lock:
                if previous_player == '':  # Verifica se a pergunta já foi respondida
                    shared_data[64:128] = answer.encode('utf-8') + b' ' * (64 - len(answer))  # Escreve a resposta na memória compartilhada
                    
                    # Garantir que o nome tenha exatamente 4 bytes
                    player_name_bytes = name.encode('utf-8')[:4]  # Truncar para 4 bytes se necessário
                    player_name_bytes += b' ' * (4 - len(player_name_bytes))  # Completar para 4 bytes se necessário

                    shared_data[132:136] = player_name_bytes  # Nome do jogador que respondeu
                    print(f"{name} enviou a resposta: {answer}")
                else:
                    print(f"{name}, você foi muito lento, outro jogador já respondeu!")

        time.sleep(1)  # Aguarda antes de tentar ler a próxima pergunta

    existing_shm.close()

if __name__ == "__main__":
    lock = multiprocessing.Lock()
    
    # Recuperar o nome da memória compartilhada
    shm_name = "wnsm_5aa05575"

    # Iniciar processos clientes
    players = ["Jogador 1", "Jogador 2", "Jogador 3", "Jogador 4"]
    processes = [multiprocessing.Process(target=cliente, args=(name, shm_name, lock)) for name in players]

    for p in processes:
        p.start()

    for p in processes:
        p.join()
