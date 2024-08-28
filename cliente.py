import multiprocessing
from multiprocessing import shared_memory
import time

def cliente(name, shm_name, lock):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    shared_data = existing_shm.buf
    
    last_question_id = -1

    while True:
        with lock:
            question = shared_data[0:64].tobytes().decode('utf-8').rstrip()
            question_id = shared_data[128:132].tobytes().decode('utf-8').rstrip()
            previous_player = shared_data[132:136].tobytes().decode('utf-8').rstrip()

        # Se não há mais perguntas novas, terminamos o jogo
        if not question or question_id == last_question_id:
            print(f"{name}: Todas as perguntas foram respondidas. Encerrando o jogo.")
            break

        last_question_id = question_id

        print(f"{name} recebeu a pergunta: {question}")
        
        # Captura a resposta do jogador manualmente
        answer = input(f"{name}, digite sua resposta: ")
        print(f"{name} enviou a resposta: {answer}")

        with lock:
            if previous_player == '':  # Verifica se a pergunta já foi respondida
                shared_data[64:128] = answer.encode('utf-8') + b' ' * (64 - len(answer))  # Escreve a resposta na memória compartilhada
                
                # Garantir que o nome tenha exatamente 4 bytes
                player_name_bytes = name.encode('utf-8')[:4]  # Truncar para 4 bytes se necessário
                player_name_bytes += b' ' * (4 - len(player_name_bytes))  # Completar para 4 bytes se necessário

                shared_data[132:136] = player_name_bytes  # Nome do jogador que respondeu
            else:
                print(f"{name}, você foi muito lento, outro jogador já respondeu!")

        time.sleep(1)  # Aguarda antes de tentar ler a próxima pergunta

    existing_shm.close()

if __name__ == "__main__":
    lock = multiprocessing.Lock()
    
    # Nome da memória compartilhada gerado pelo servidor
    shm_name = "wnsm_ceef6b56"
    
    # Executar o cliente diretamente
    cliente("Jogador 1", shm_name, lock)
