
import pygame
import time
import random
import heapq
import json

## Inicializando o Pygame ##
pygame.init()

## mixer ##
pygame.mixer.init()

try:
    pygame.mixer.music.load("8-bit-arcade-138828.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Could not load or play music: {e}")


## Definindo cores ##
branco = (255, 255, 255)
preto = (0, 0, 0)
vermelho = (213, 50, 80)
verde = (0, 255, 0)
azul = (50, 153, 213)

## Definindo a largura e altura da tela ##
## aumentei a tela para poder ver todas mensagens ##
largura = 500
altura = 500

## Criando a tela ##
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption('Snake Game')

## Definindo o relógio (FPS) ##
relogio = pygame.time.Clock()

## Definindo o tamanho da cobra e a velocidade do jogo ##
tamanho_bloco = 10
velocidade = 30 ### é alterada durante a dificuldade, mas resolvemos manter aqui por segurança ###

## Fontes para o jogo ##
font_style = pygame.font.SysFont("impact", 25)
font_score = pygame.font.SysFont("impact", 35)

global_dificuldade_selecionada = "medio"


#######################################################################################################################

def bubbleSort(ranking):
    ranking = ranking.copy()
    n = len(ranking)
    for k in range(n - 1):
        noUpdated = True
        for i in range(n - k - 1):
            if ranking[i]["pontos"] < ranking[i + 1]["pontos"]:  ## ordena do maior para o menor, considerando que usamos ele em um dict##
                ranking[i], ranking[i + 1] = ranking[i + 1], ranking[i]
                noUpdated = False
        if noUpdated:
            break
    return ranking

def gerenciar_ranking(nova_pontuacao, dificuldade_do_jogo,modo_auto=False):
    ranking_filepath = "ranking.txt"  ## Caminho do arquivo do ranking ##

    if modo_auto:
        dificuldade_do_jogo = "auto"

    try:
        with open(ranking_filepath, "r") as file:
            ranking = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        ranking = []


    ### adiciona a nova pontuação se for valida (pontuaçao > 0) ###
    if nova_pontuacao > 0:
        nova_entrada = {"pontos": nova_pontuacao, "dificuldade": dificuldade_do_jogo}
        ranking.append(nova_entrada)

        ## Ordena o ranking por pontos (do maior para o menor) ##
        ranking = bubbleSort(ranking)
        ## mantem apenas as 10 melhores pontuações (ou quantas desejar) ##
        ranking = ranking[:10]

        with open(ranking_filepath, "w") as file:
            json.dump(ranking, file)

    return ranking


def mostrar_ranking():
    ranking_filepath = "ranking.txt"  ## caminho do arquivo do ranking ##
    ranking_aberto = True

    ranking = []
    try:
        with open(ranking_filepath, "r") as file:
            ranking = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        ranking = []

    while ranking_aberto:
        tela.fill(azul)
        mensagem("RANKING", preto, largura / 2, altura / 4 - 50)

        if not ranking:
            mensagem("Nenhuma pontuação registrada ainda!", preto, largura / 2, altura / 2)
        else:
            y_offset = altura / 4
            for i, entrada in enumerate(ranking):
                ## formata a string para exibir a posiçao,  os pontos e a dificuldade ##
                ranking_str = f"{i + 1}. Pontos: {entrada['pontos']} - Dificuldade: {entrada['dificuldade'].capitalize()}"
                mensagem(ranking_str, preto, largura / 2, y_offset + i * 30)
                if i >= 9:
                    break

        mensagem("Pressione ESC para Voltar ao Menu Principal", preto, largura / 2, altura - 50)
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ranking_aberto = False

#######################################################################################################################

def construir_grafo(grid_largura, grid_altura, tamanho_bloco, obstaculos):
    grafo = {}
    for x in range(0, grid_largura, tamanho_bloco):
        for y in range(0, grid_altura, tamanho_bloco):
            no = (x, y)
            if [x, y] in obstaculos:
                continue  ### verifica se o nó é um obstáculo  e ignora ele ###

            vizinhos = [] ## arrestas de valores dos vizinhos do nó ##
            for dx, dy in [(-tamanho_bloco, 0), (tamanho_bloco, 0), (0, -tamanho_bloco), (0, tamanho_bloco)]:
                vizinho = (x + dx, y + dy)
                if (0 <= vizinho[0] < grid_largura and
                    0 <= vizinho[1] < grid_altura and
                    [vizinho[0], vizinho[1]] not in obstaculos):
                    vizinhos.append(vizinho)

            grafo[no] = vizinhos
    return grafo


def dijkstra_grafo(grafo, inicio, objetivo):
    fronteira = []
    heapq.heappush(fronteira, (0, inicio))
    inicio_grafo = {inicio: None}
    custo_acum = {inicio: 0}

    while fronteira:
        _, atual = heapq.heappop(fronteira)

        if atual == objetivo: ## para quando chegar ao destino ##
            break

        for vizinho in grafo.get(atual, []):
            novo_custo = custo_acum[atual] + 1
            if vizinho not in custo_acum or novo_custo < custo_acum[vizinho]:
                custo_acum[vizinho] = novo_custo
                heapq.heappush(fronteira, (novo_custo, vizinho))
                inicio_grafo[vizinho] = atual

    if objetivo not in inicio_grafo:
        return []

    # Reconstrução do caminho
    caminho = []
    atual = objetivo
    while atual != inicio:
        caminho.append(atual)
        atual = inicio_grafo[atual]
    caminho.reverse()
    return caminho



# Função para desenhar a cobra
def dificuldade(dific, paredes, comprimento_cobra):
    global velocidade

    if dific == "automatico":
        dific = "dificil"

    if dific == "muito facil":
        velocidade = 10 + (comprimento_cobra // 10)
    elif dific == "facil":
        velocidade = 10 + (comprimento_cobra // 10)
        for i in range(60, 130, tamanho_bloco):
            paredes.append([i, 60])
            paredes.append([i, altura - 60])

            paredes.append([largura - i, 60])
            paredes.append([largura - i, altura - 60])

            paredes.append([60, i])
            paredes.append([largura - 60, i])
            paredes.append([60, altura - i])
            paredes.append([largura - 60, altura - i])
    elif dific == "medio":
        velocidade = 10 + (comprimento_cobra // 5)
        for i in range(60, 130, tamanho_bloco):
            paredes.append([i, 60])
            paredes.append([i, altura - 60])
            paredes.append([largura - i, 60])
            paredes.append([largura - i, altura - 60])
            paredes.append([60, i])
            paredes.append([largura - 60, i])
            paredes.append([60, altura - i])
            paredes.append([largura - 60, altura - i])
        for i in range(200, 300, tamanho_bloco):
            paredes.append([i, 130])
            paredes.append([i, altura - 130])

            paredes.append([130, i])
            paredes.append([largura - 130, i])
    elif dific == "dificil":
        velocidade = 15 + (comprimento_cobra // 5)
        for i in range(60, 130, tamanho_bloco):
            paredes.append([i, 60])
            paredes.append([i, altura - 60])
            paredes.append([largura - i, 60])
            paredes.append([largura - i, altura - 60])
            paredes.append([60, i])
            paredes.append([largura - 60, i])
            paredes.append([60, altura - i])
            paredes.append([largura - 60, altura - i])
        for i in range(200, 300, tamanho_bloco):
            paredes.append([i, 130])
            paredes.append([i, altura - 130])

            paredes.append([130, i])
            paredes.append([largura - 130, i])
        for i in range(0, 30, tamanho_bloco):
            paredes.append([200, i])
            paredes.append([300, i])

            paredes.append([200, altura - i])
            paredes.append([300, altura - i])

            paredes.append([i, 200])
            paredes.append([i, 300])
            paredes.append([largura - i, 200])
            paredes.append([largura - i, 300])
    else:
        print(f"Dificuldade inválida '{dific}'. Usando padrão (médio).")
        velocidade = 10 + (comprimento_cobra // 5)
        for i in range(60, 130, tamanho_bloco):
            paredes.append([i, 60])
            paredes.append([i, altura - 60])
            paredes.append([largura - i, 60])
            paredes.append([largura - i, altura - 60])
            paredes.append([60, i])
            paredes.append([largura - 60, i])
            paredes.append([60, altura - i])
            paredes.append([largura - 60, altura - i])
        for i in range(200, 300, tamanho_bloco):
            paredes.append([i, 130])
            paredes.append([i, altura - 130])
            paredes.append([130, i])
            paredes.append([largura - 130, i])


def nossa_cobra(tamanho_bloco, lista_cobra):
    for x in lista_cobra:
        pygame.draw.rect(tela, verde, [x[0], x[1], tamanho_bloco, tamanho_bloco])


# Função para exibir mensagens na tela
def mensagem(msg, cor, x_pos, y_pos):
    mesg = font_style.render(msg, True, cor)
    text_rect = mesg.get_rect(center=(x_pos, y_pos))
    tela.blit(mesg, text_rect)


# Função para mostrar o score p/ o jogador, dps adicionar o tempo talvez
def nosso_placar(pontos):
    valor = font_score.render("Pontos: " + str(pontos), True, preto)
    tela.blit(valor, [10, 10])


def desenhar_paredes(paredes):
    for bloco in paredes:
        pygame.draw.rect(tela, preto, [bloco[0], bloco[1], tamanho_bloco, tamanho_bloco])


def spawn_maca(paredes, lista_cobra):
    while True:
        x = round(random.randrange(0, largura - tamanho_bloco) / 10.0) * 10.0
        y = round(random.randrange(0, altura - tamanho_bloco) / 10.0) * 10.0

        if [x, y] not in paredes and [x, y] not in lista_cobra:
            return x, y


def menu_principal():
    menu_aberto = True
    while menu_aberto:
        tela.fill(azul)

        mensagem("Escolha a Dificuldade:", preto, largura / 2, altura / 4)
        mensagem("1 - Muito Fácil", preto, largura / 2, altura / 4 + 50)
        mensagem("2 - Fácil", preto, largura / 2, altura / 4 + 100)
        mensagem("3 - Médio", preto, largura / 2, altura / 4 + 150)
        mensagem("4 - Difícil", preto, largura / 2, altura / 4 + 200)
        mensagem("5 - Automatico", preto, largura / 2, altura / 4 + 250)
        mensagem("Pressione 'Q' para Sair", preto, largura / 2, altura / 4 + 300)

        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    return "muito facil"
                elif evento.key == pygame.K_2:
                    return "facil"
                elif evento.key == pygame.K_3:
                    return "medio"
                elif evento.key == pygame.K_4:
                    return "dificil"
                elif evento.key == pygame.K_5:
                    return "automatico"
                elif evento.key == pygame.K_q:
                    pygame.quit()
                    quit()

    return "medio"


def pausar_jogo():
    pausado = True
    while pausado:
        tela.fill(azul)
        mensagem("PAUSADO", preto, largura / 2, altura / 2 - 50)
        mensagem("Pressione P para Continuar ou Q para Sair", preto, largura / 2, altura / 2 + 20)
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_p:
                    pausado = False
                elif evento.key == pygame.K_q:
                    pygame.quit()
                    quit()
        relogio.tick(5)
    return False


def jogo(dificuldade_selecionada):
    ############### Variaveis gerais do jogo ###############
    game_over = False
    game_close = False
    paused = False

    modo_auto = False

    x1 = largura / 2
    y1 = altura / 2

    if dificuldade_selecionada == "automatico":
        modo_auto = True

    caminho_auto = []
    indice_caminho = 0

    pode_mudar = True

    x1_mudar = 0
    y1_mudar = 0

    paredes = []
    lista_cobra = []
    global comprimento_cobra
    comprimento_cobra = 1

    # Parede ao redor do mapa
    for x in range(0, largura, tamanho_bloco):
        paredes.append([x, 0])
        paredes.append([x, altura - tamanho_bloco])

    for y in range(0, altura, tamanho_bloco):
        paredes.append([0, y])
        paredes.append([largura - tamanho_bloco, y])

    dificuldade(dificuldade_selecionada, paredes, comprimento_cobra)

    grafo_global = construir_grafo(largura, altura, tamanho_bloco, paredes)

    maca_x, maca_y = spawn_maca(paredes, lista_cobra)

    ##########           laço principal do jogo         ###########
    while not game_over:

        if game_close and not game_over:
            gerenciar_ranking(comprimento_cobra - 1, dificuldade_selecionada,modo_auto)

        while game_close:

            tela.fill(azul)
            mensagem("Você perdeu!", vermelho, largura / 2, altura / 2 - 90)
            mensagem("Pressione C para Continuar", preto, largura / 2, altura / 2 - 10)
            mensagem("Pressione M para Menu", vermelho, largura / 2, altura / 2 + 30)
            mensagem("Pressione 'R' para Ranking", preto, largura / 2, altura / 2 + 70)
            mensagem("Pressione Q para Sair", vermelho, largura / 2, altura / 2 + 110)
            nosso_placar(comprimento_cobra - 1)
            pygame.display.update()



            for evento in pygame.event.get():
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if evento.key == pygame.K_c:
                        game_close = False
                        jogo(dificuldade_selecionada)
                        return
                    if evento.key == pygame.K_m:
                        game_close = False
                        global global_dificuldade_selecionada
                        global_dificuldade_selecionada = menu_principal()
                        jogo(global_dificuldade_selecionada)
                        return
                    if evento.key == pygame.K_r:
                        mostrar_ranking()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                game_over = True
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_p:
                    paused = not paused
                    if paused:
                        paused = pausar_jogo()

            if paused == False:
                if evento.type == pygame.K_q:
                    pygame.quit()
                    quit()
                if evento.type == pygame.KEYDOWN:
                    if pode_mudar and not modo_auto:
                        if evento.key == pygame.K_LEFT:
                            if x1_mudar == tamanho_bloco:
                                continue
                            x1_mudar = -tamanho_bloco
                            y1_mudar = 0
                            pode_mudar = False
                        elif evento.key == pygame.K_RIGHT:
                            if x1_mudar == -tamanho_bloco:
                                continue
                            x1_mudar = tamanho_bloco
                            y1_mudar = 0
                            pode_mudar = False
                        elif evento.key == pygame.K_UP:
                            if y1_mudar == tamanho_bloco:
                                continue
                            y1_mudar = -tamanho_bloco
                            x1_mudar = 0
                            pode_mudar = False
                        elif evento.key == pygame.K_DOWN:
                            if y1_mudar == -tamanho_bloco:
                                continue
                            y1_mudar = tamanho_bloco
                            x1_mudar = 0
                            pode_mudar = False

        if x1 < 0 or x1 >= largura or y1 < 0 or y1 >= altura:
            game_close = True


        
        if not modo_auto:
            x1 += x1_mudar
            y1 += y1_mudar


        if modo_auto:
            if not caminho_auto or indice_caminho >= len(caminho_auto):
                obstaculos = lista_cobra[:-1] + paredes
                grafo_atual = construir_grafo(largura, altura, tamanho_bloco, obstaculos)
                caminho_auto = dijkstra_grafo(grafo_atual, (int(x1), int(y1)), (int(maca_x), int(maca_y)))
                indice_caminho = 0

            if caminho_auto:
                x1, y1 = caminho_auto[indice_caminho]
                indice_caminho += 1

        pode_mudar = True

        tela.fill(azul)
        desenhar_paredes(paredes)
        pygame.draw.rect(tela, vermelho, [maca_x, maca_y, tamanho_bloco, tamanho_bloco])

        lista_cabeça = []
        lista_cabeça.append(x1)
        lista_cabeça.append(y1)
        lista_cobra.append(lista_cabeça)

        if len(lista_cobra) > comprimento_cobra:
            del lista_cobra[0]

        # Verifica se a cabeça da cobra colidiu com ela mesma ou com as paredes
        for x in lista_cobra[:-1]:
            if x == lista_cabeça:
                game_close = True

        for parede in paredes:
            if parede == lista_cabeça:
                game_close = True

        nossa_cobra(tamanho_bloco, lista_cobra)
        nosso_placar(comprimento_cobra - 1)
        pygame.display.update()

        # Colisão com a comida
        if x1 == maca_x and y1 == maca_y:
            maca_x, maca_y = spawn_maca(paredes, lista_cobra)
            comprimento_cobra += 1

            if modo_auto:
                obstaculos = lista_cobra[:-1] + paredes
                grafo_atual = construir_grafo(largura, altura, tamanho_bloco, obstaculos)
                caminho_auto = dijkstra_grafo(grafo_atual, (int(x1), int(y1)), (int(maca_x), int(maca_y)))
                indice_caminho = 0

        relogio.tick(velocidade)

    # Move pygame.quit() and quit() outside the main game loop
    pygame.quit()
    quit()


global_dificuldade_selecionada = "medio"
dificuldade_escolhida_do_menu = menu_principal()

if dificuldade_escolhida_do_menu:
    global_dificuldade_selecionada = dificuldade_escolhida_do_menu

jogo(global_dificuldade_selecionada)