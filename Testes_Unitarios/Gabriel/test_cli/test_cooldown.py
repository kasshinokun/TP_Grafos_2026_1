import sys
import os
import threading
import time
import json
import logging

# Adiciona o diretório v1d ao path para importar o Orchestrator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from orchestrator_hibrido_alpha0b import Orchestrator, EventBus, TokenManager, ShutdownManager

def test_cooldown_notification():
    logging.info("Iniciando teste de notificação de cooldown...")
    
    # Configuração de teste
    tokens = ["fake_token_1", "fake_token_2"]
    bus = EventBus()
    tm = TokenManager(tokens)
    sm = ShutdownManager()
    
    # Simula o Orchestrator monitorando a notification_queue
    def monitor():
        last_notify = 0
        while not sm.is_shutdown_requested():
            notif = bus.consume_notification(timeout=0.1)
            if notif:
                print(f"\n>>> NOTIFICAÇÃO RECEBIDA: {notif['type']} para token ...{notif['token'][-4:]}")
            
            if tm.all_in_cooldown():
                now = time.time()
                if now - last_notify > 2: # Intervalo curto para o teste
                    reset_at = tm.get_next_reset_time()
                    wait_sec = int(reset_at - now)
                    print(f"\n>>> ALERTA CRÍTICO: Todos os tokens em cooldown! Espera: {wait_sec}s")
                    last_notify = now
            time.sleep(0.1)

    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()

    # 1. Simula um cooldown individual
    print("\nSimulando cooldown do token 1...")
    reset_time = time.time() + 5
    tm.set_cooldown(tokens[0], reset_time)
    bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": tokens[0], "reset_time": reset_time})
    time.sleep(1)

    # 2. Simula cooldown total
    print("\nSimulando cooldown do token 2 (cooldown total)...")
    tm.set_cooldown(tokens[1], reset_time)
    bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": tokens[1], "reset_time": reset_time})
    time.sleep(3)

    print("\nEncerrando teste...")
    sm.request_shutdown()
    monitor_thread.join()
    print("\nTeste concluído com sucesso!")

if __name__ == "__main__":
    test_cooldown_notification()
