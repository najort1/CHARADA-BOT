from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import time
import unicodedata
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, Style, init

init(autoreset=True)

def puxa_dados(original, left, right, capturar_todos=False):
    split_str = original.split(left)[1:]
    result = [s.split(right)[0] for s in split_str]

    return result if capturar_todos else result[0] if result else None

def esperar_elemento(browser, selector):
    return WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def carregar_palavras(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as file:
        return [remover_acentos(palavra).lower().strip() for palavra in file.readlines()]

def obter_resultado(browser, linha_atual):
    resultado = []
    divs = browser.find_elements(By.CSS_SELECTOR, f'div.flex-grow > div:nth-child({linha_atual + 1}) > div.cellAnimation')
    for i, div in enumerate(divs):
        texto = div.text.lower()
        cor = div.get_attribute('class')
        tipo = 'correta' if 'bg-green-500' in cor else 'presente' if 'bg-yellow-500' in cor else 'ausente'
        resultado.append({'letra': texto, 'posicao': i, 'tipo': tipo})
    return resultado

def reiniciar_memoria(memoria):
    for key in memoria:
        memoria[key].clear() if isinstance(memoria[key], set) else memoria[key].clear()

def obter_palavras_possiveis(palavras, tentativa, resultado, memoria):
    for res in resultado:
        letra, posicao, tipo = res['letra'], res['posicao'], res['tipo']
        if tipo == 'correta':
            memoria['corretas'][posicao] = letra
        elif tipo == 'presente':
            memoria['presentes'].setdefault(letra, set()).add(posicao)
        elif tipo in ['ausente', 'não existe na palavra']:
            if letra not in memoria['corretas'].values() and letra not in memoria['presentes']:
                memoria['ausentes'].add(letra)

    palavras_possiveis = []
    for palavra in palavras:
        palavra_sem_acento = remover_acentos(palavra).lower().strip()
        if any(letra in palavra_sem_acento and letra not in memoria['letras_duplicadas'] for letra in memoria['ausentes']):
            continue
        if any(palavra_sem_acento[posicao] != letra for posicao, letra in memoria['corretas'].items()):
            continue
        if any(letra not in palavra_sem_acento or any(palavra_sem_acento[posicao] == letra for posicao in posicoes) for letra, posicoes in memoria['presentes'].items()):
            continue
        if any(letra in palavra_sem_acento and sum(1 for i in range(len(palavra_sem_acento)) if palavra_sem_acento[i] == letra and i not in posicoes) == 0 for letra, posicoes in memoria['letras_duplicadas'].items()):
            continue
        palavras_possiveis.append(palavra_sem_acento)

    return palavras_possiveis

def clicar_jogar_novamente(browser):
    browser.find_element(By.CSS_SELECTOR, '.bg-emerald-600').click()

def html_pagina(browser):
    return browser.page_source

def main():
    memoria = {
        'corretas': {},
        'presentes': {},
        'ausentes': set(),
        'letras_duplicadas': {}
    }
    todas_as_palavras = carregar_palavras('palavras.txt')
    browser = webdriver.Firefox()
    browser.get('https://charada.app/')

    while True:
        tentativas = ['podam', 'trens', 'fuzil', 'bucho', 'ganja']
        reiniciar_memoria(memoria)
        time.sleep(0.5)
        for linha_atual, tentativa in enumerate(tentativas):
            try:
                body = esperar_elemento(browser, 'body')
                for letra in tentativa:
                    time.sleep(0.05)
                    body.send_keys(letra)
                body.send_keys(Keys.RETURN)
                time.sleep(0.5)
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.cellAnimation'))
                )

                resultado = obter_resultado(browser, linha_atual)
                print(f"{Fore.MAGENTA}Resultado da tentativa '{tentativa}':")
                for item in resultado:
                    item['tipo'] = 'não existe na palavra' if item['tipo'] == 'ausente' else item['tipo']
                    print(f"{Fore.BLUE}Letra: {item['letra']}, Posição: {item['posicao']}, Tipo: {item['tipo']}")

                dicionario = obter_palavras_possiveis(todas_as_palavras, tentativa, resultado, memoria)
                print(f"{Fore.LIGHTBLUE_EX}Palavras possíveis: {dicionario if len(dicionario) < 10 else len(dicionario)}")

                if len(dicionario) == 1:
                    print(f"{Fore.LIGHTGREEN_EX}A palavra é: {dicionario[0]}")
                    body = esperar_elemento(browser, 'body')
                    for letra in dicionario[0]:
                        time.sleep(0.05)
                        body.send_keys(letra)
                    body.send_keys(Keys.RETURN)
                    acertou_ou_nao = html_pagina(browser)
                    if 'você acertou' in acertou_ou_nao:
                        print(f"{Fore.GREEN}Parabéns! Você acertou!")
                    else:
                        resposta_correta = puxa_dados(acertou_ou_nao, 'A palavra era: ', ' ')
                        print(f"{Fore.RED}A palavra correta era: {resposta_correta}")

                    time.sleep(0.5)
                    clicar_jogar_novamente(browser)
                    break

                elif len(dicionario) > 1 and linha_atual == 4:
                    palavra_final = dicionario[0]
                    print(f"{Fore.YELLOW}Escolhendo aleatoriamente: {palavra_final}")
                    body = esperar_elemento(browser, 'body')
                    for letra in palavra_final:
                        time.sleep(0.05)
                        body.send_keys(letra)
                    body.send_keys(Keys.RETURN)
                    acertou_ou_nao = html_pagina(browser)
                    if 'você acertou' in acertou_ou_nao:
                        print(f"{Fore.GREEN}Parabéns! Você acertou!")
                    else:
                        resposta_correta = puxa_dados(acertou_ou_nao, 'A palavra era: ', ' ')
                        print(f"{Fore.RED}A palavra correta era: {resposta_correta}")

                    time.sleep(0.5)
                    clicar_jogar_novamente(browser)
                    break

                elif len(dicionario) == 0:
                    print("Não há palavras possíveis. Encerrando...")
                    browser = webdriver.Firefox()
                    browser.get('https://charada.app/')
                    break
            except StaleElementReferenceException:
                print("Elemento ficou obsoleto, tentando novamente...")
                continue

if __name__ == '__main__':
    main()
