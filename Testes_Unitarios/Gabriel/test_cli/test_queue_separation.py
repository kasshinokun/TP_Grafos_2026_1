#!/usr/bin/env python3
"""
Teste de Separação de Filas
Valida que dados e notificações não se misturam mais.
"""

import sys
import os
import threading
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from orchestrator_hibrido_alpha0b import EventBus, TokenManager, ShutdownManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_queue_separation():
    """Testa se dados e notificações estão em filas separadas."""
    logging.info("Iniciando teste de separação de filas...")
    
    bus = EventBus()
    
    # 1. Publica dados em data_queue
    logging.info("Publicando dados em data_queue...")
    bus.publish_data({"type": "DATA_EXTRACTED", "data_type": "issue_comments", "payload": [{"id": 1}]})
    
    # 2. Publica notificação em notification_queue
    logging.info("Publicando notificação em notification_queue...")
    bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "fake_token_123"})
    
    # 3. Verifica se consegue consumir dados sem pegar notificação
    logging.info("Consumindo de data_queue...")
    data = bus.consume_data(timeout=0.5)
    if data and data["type"] == "DATA_EXTRACTED":
        logging.info("✅ Dados consumidos corretamente de data_queue")
    else:
        logging.error("❌ Falha ao consumir dados de data_queue")
        return False
    
    # 4. Verifica se consegue consumir notificação sem pegar dados
    logging.info("Consumindo de notification_queue...")
    notif = bus.consume_notification(timeout=0.5)
    if notif and notif["type"] == "TOKEN_COOLDOWN":
        logging.info("✅ Notificação consumida corretamente de notification_queue")
    else:
        logging.error("❌ Falha ao consumir notificação de notification_queue")
        return False
    
    # 5. Verifica que filas estão vazias
    logging.info("Verificando filas vazias...")
    if bus.consume_data(timeout=0.1) is None and bus.consume_notification(timeout=0.1) is None:
        logging.info("✅ Filas vazias conforme esperado")
    else:
        logging.error("❌ Filas não estão vazias")
        return False
    
    logging.info("✅ Teste de separação de filas passou!")
    return True

def test_concurrent_producers():
    """Testa múltiplos produtores publicando simultaneamente."""
    logging.info("\nIniciando teste de produtores concorrentes...")
    
    bus = EventBus()
    results = {"data_count": 0, "notif_count": 0}
    
    def producer_data():
        for i in range(5):
            bus.publish_data({"type": "DATA_EXTRACTED", "payload": [{"id": i}]})
            time.sleep(0.01)
    
    def producer_notif():
        for i in range(5):
            bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": f"token_{i}"})
            time.sleep(0.01)
    
    # Inicia produtores
    t1 = threading.Thread(target=producer_data)
    t2 = threading.Thread(target=producer_notif)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Consome dados
    logging.info("Consumindo dados...")
    while True:
        data = bus.consume_data(timeout=0.1)
        if data is None: break
        results["data_count"] += 1
    
    # Consome notificações
    logging.info("Consumindo notificações...")
    while True:
        notif = bus.consume_notification(timeout=0.1)
        if notif is None: break
        results["notif_count"] += 1
    
    if results["data_count"] == 5 and results["notif_count"] == 5:
        logging.info(f"✅ Produtores concorrentes: {results['data_count']} dados + {results['notif_count']} notificações")
        return True
    else:
        logging.error(f"❌ Contagem incorreta: {results}")
        return False

def test_token_manager_state():
    """Testa o gerenciador de tokens com cooldown."""
    logging.info("\nIniciando teste de gerenciador de tokens...")
    
    tokens = ["token_1", "token_2", "token_3"]
    tm = TokenManager(tokens)
    
    # 1. Inicialmente, nenhum em cooldown
    if not tm.all_in_cooldown():
        logging.info("✅ Inicialmente, nem todos em cooldown")
    else:
        logging.error("❌ Erro: todos em cooldown no início")
        return False
    
    # 2. Coloca um em cooldown
    reset_time = time.time() + 10
    tm.set_cooldown(tokens[0], reset_time)
    if not tm.all_in_cooldown():
        logging.info("✅ Com 1 em cooldown, nem todos bloqueados")
    else:
        logging.error("❌ Erro: todos bloqueados com apenas 1 em cooldown")
        return False
    
    # 3. Coloca todos em cooldown
    tm.set_cooldown(tokens[1], reset_time)
    tm.set_cooldown(tokens[2], reset_time)
    if tm.all_in_cooldown():
        logging.info("✅ Com todos em cooldown, detecção correta")
    else:
        logging.error("❌ Erro: não detectou todos em cooldown")
        return False
    
    # 4. Verifica tempo de reset
    next_reset = tm.get_next_reset_time()
    if next_reset > 0:
        logging.info(f"✅ Próximo reset em {int(next_reset - time.time())}s")
    else:
        logging.error("❌ Erro ao obter tempo de reset")
        return False
    
    logging.info("✅ Teste de gerenciador de tokens passou!")
    return True

if __name__ == "__main__":
    results = []
    results.append(("Separação de Filas", test_queue_separation()))
    results.append(("Produtores Concorrentes", test_concurrent_producers()))
    results.append(("Gerenciador de Tokens", test_token_manager_state()))
    
    logging.info("\n" + "="*50)
    logging.info("RESUMO DOS TESTES")
    logging.info("="*50)
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        logging.info(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        logging.info("\n🎉 Todos os testes passaram!")
    else:
        logging.error("\n⚠️ Alguns testes falharam!")
        sys.exit(1)
