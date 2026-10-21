"""
ROCK BLASTER - jogo controlado por gestos (OpenCV + MediaPipe)

MENU:
  - Leve a mira (palma da mao) ate o botao JOGAR e FECHE A MAO.
  - Alternativas: clicar no botao com o mouse ou tecla ENTER.

JOGO (uma mao):
  - MIRA ........ centro da palma da mao (a mira segue a mao)
  - TIRO ........ FECHAR a mao (transicao aberta -> fechada)
  - SUPER BOMBA . tecla ESPACO (so funciona com a barra de energia cheia)

OBJETOS:
  - Pedra ....... 1 tiro
  - Diamante .... azul e brilhante, 2 tiros, vale mais pontos e energia
  - Jade ........ pedra verde (1 tiro): ao explodir recupera 1 vida (so aparece se
                  faltar vida; se cair no chao, nada acontece)
  - Bomba ....... a partir do nivel 4: NAO atire! Estourar uma bomba custa 1 vida
                  (se ela cair no chao, nada acontece)

Outras teclas: P = pausa | R = reiniciar | M = menu | H = landmarks | ESC = sair
Mouse: move = mira (quando nao ha mao) | clique = tiro

Dependencias: pip install mediapipe==0.10.21 opencv-python numpy
"""
import math
import random
import time
from collections import Counter, deque

import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

L, A = 960, 540            # tamanho da janela do jogo
JANELA = "Rock Blaster"
FONTE = cv2.FONT_HERSHEY_SIMPLEX

NIVEL_BOMBAS = 3           # indice do nivel em que as bombas comecam (= "Nivel 4")
VIDAS_MAX = 5
NIVEL_JADE = 1             # a jade comeca a aparecer a partir do "Nivel 2"
BOTAO_PLAY = (L // 2 - 140, 290, L // 2 + 140, 360)
BOTAO_NOVO = (L // 2 - 170, A // 2 + 75, L // 2 + 170, A // 2 + 140)


# ----------------------------------------------------------------------
# Reconhecimento de gestos (regras do exercicio, com suavizacao temporal)
# ----------------------------------------------------------------------
def distancia(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def contar_dedos(hand):
    lm = hand.landmark
    n = 0
    for ponta, art in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if lm[ponta].y < lm[art].y:
            n += 1
    if distancia(lm[4], lm[5]) > distancia(lm[3], lm[5]) * 1.15:
        n += 1
    return n


def estado_mao(hand):
    n = contar_dedos(hand)
    if n >= 4:
        return "aberta"
    if n <= 1:
        return "fechada"
    return "parcial"


def centro_palma(hand):
    lm = hand.landmark
    ids = [0, 5, 9, 13, 17]
    return (sum(lm[i].x for i in ids) / len(ids),
            sum(lm[i].y for i in ids) / len(ids))


# ----------------------------------------------------------------------
# Utilitarios de desenho
# ----------------------------------------------------------------------
def dentro(rect, p):
    x0, y0, x1, y1 = rect
    return x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def brilho(img, x, y, raio, cor, alpha):
    """Halo luminoso (circulo translucido) desenhado so na regiao de interesse."""
    x0, y0 = max(0, int(x - raio) - 2), max(0, int(y - raio) - 2)
    x1, y1 = min(L, int(x + raio) + 3), min(A, int(y + raio) + 3)
    if x1 <= x0 or y1 <= y0:
        return
    roi = img[y0:y1, x0:x1]
    over = roi.copy()
    cv2.circle(over, (int(x) - x0, int(y) - y0), int(raio), cor, -1, cv2.LINE_AA)
    roi[:] = cv2.addWeighted(over, alpha, roi, 1 - alpha, 0)


def estrela(img, x, y, tam, cor=(255, 255, 255)):
    """Estrelinha de brilho (efeito de reflexo no diamante)."""
    x, y, t = int(x), int(y), max(2, int(tam))
    cv2.line(img, (x - t, y), (x + t, y), cor, 2, cv2.LINE_AA)
    cv2.line(img, (x, y - t), (x, y + t), cor, 2, cv2.LINE_AA)
    d = int(t * 0.55)
    cv2.line(img, (x - d, y - d), (x + d, y + d), cor, 1, cv2.LINE_AA)
    cv2.line(img, (x - d, y + d), (x + d, y - d), cor, 1, cv2.LINE_AA)


def centralizado(img, txt, y, escala, cor, esp=3, desl=0):
    (w, _), _ = cv2.getTextSize(txt, FONTE, escala, esp)
    cv2.putText(img, txt, ((L - w) // 2 + desl, y + desl), FONTE, escala, cor,
                esp, cv2.LINE_AA)


def desenhar_botao(img, rect, txt, hover):
    x0, y0, x1, y1 = rect
    if hover:                       # botao "cresce" quando a mira esta sobre ele
        x0, y0, x1, y1 = x0 - 8, y0 - 5, x1 + 8, y1 + 5
    cor = (70, 210, 70) if hover else (40, 140, 40)
    cv2.rectangle(img, (x0 + 4, y0 + 4), (x1 + 4, y1 + 4), (0, 0, 0), -1)   # sombra
    cv2.rectangle(img, (x0, y0), (x1, y1), cor, -1)
    cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), 3, cv2.LINE_AA)
    escala = 1.3
    (w, h), _ = cv2.getTextSize(txt, FONTE, escala, 3)
    cv2.putText(img, txt, ((x0 + x1 - w) // 2, (y0 + y1 + h) // 2), FONTE,
                escala, (255, 255, 255), 3, cv2.LINE_AA)


def desenhar_mira(img, x, y, estado):
    cor = {"aberta": (0, 255, 0), "fechada": (0, 0, 255),
           "parcial": (0, 220, 255)}.get(estado, (255, 255, 255))
    x, y = int(x), int(y)
    cv2.circle(img, (x, y), 24, cor, 2, cv2.LINE_AA)
    cv2.line(img, (x - 34, y), (x - 10, y), cor, 2)
    cv2.line(img, (x + 10, y), (x + 34, y), cor, 2)
    cv2.line(img, (x, y - 34), (x, y - 10), cor, 2)
    cv2.line(img, (x, y + 10), (x, y + 34), cor, 2)


# ----------------------------------------------------------------------
# Objetos do jogo
# Transformacoes: translacao (queda), rotacao (giro) e escala (cresce ao
# 'se aproximar' do jogador).
# ----------------------------------------------------------------------
class Objeto:
    tipo = "pedra"

    def __init__(self, nivel, raio=(26, 48), giro=1.6, vida=1):
        self.r = random.uniform(*raio)
        self.x = random.uniform(self.r, L - self.r)
        self.y = -self.r
        self.vy = random.uniform(55, 85) + nivel * 7
        self.vx = random.uniform(-30, 30)
        self.ang = random.uniform(0, 2 * math.pi)
        self.giro = random.uniform(-giro, giro)
        self.vida = self.vida_max = vida
        self.flash = 0.0
        self.tempo = random.uniform(0, 6)

    def escala(self):
        return 0.6 + 0.8 * min(1.0, max(0.0, self.y / A))

    def raio(self):
        return self.r * self.escala()

    def atualizar(self, dt):
        self.y += self.vy * dt
        self.x += self.vx * dt
        self.ang += self.giro * dt
        self.tempo += dt
        if self.x < self.r or self.x > L - self.r:
            self.vx = -self.vx
        self.flash = max(0.0, self.flash - dt)

    def rotacao(self):
        c, s = math.cos(self.ang), math.sin(self.ang)
        return np.array([[c, -s], [s, c]])


class Pedra(Objeto):
    tipo = "pedra"

    def __init__(self, nivel):
        super().__init__(nivel, (26, 48), 1.6, 1)
        n = 9
        self.base = np.array([
            [math.cos(2 * math.pi * i / n) * f, math.sin(2 * math.pi * i / n) * f]
            for i, f in ((i, random.uniform(0.75, 1.1)) for i in range(n))
        ])

    def desenhar(self, img):
        pts = (self.base * self.raio()) @ self.rotacao().T + np.array([self.x, self.y])
        pts = pts.astype(np.int32)
        cor = (235, 235, 255) if self.flash > 0 else (70, 95, 125)
        cv2.fillPoly(img, [pts], cor)
        cv2.polylines(img, [pts], True, (30, 40, 55), 2, cv2.LINE_AA)


class Diamante(Objeto):
    """Diamante azul e brilhante: resistente (2 tiros), vale mais."""
    tipo = "diamante"
    # coroa (0,1), cintura (4,2) e ponta inferior (3)
    BASE = [[-0.55, -0.6], [0.55, -0.6], [1.0, -0.15], [0.0, 1.05], [-1.0, -0.15]]

    def __init__(self, nivel):
        super().__init__(nivel, (30, 44), 0.9, 2)
        self.base = np.array(self.BASE)

    def desenhar(self, img):
        R = self.raio()
        rot = self.rotacao()
        centro = np.array([self.x, self.y])

        def T(p):
            return (np.array(p, dtype=float) * R) @ rot.T + centro

        p0, p1, p2, p3, p4 = T(self.base)
        cc = T([0.0, -0.15])

        # halo azul pulsante
        brilho(img, self.x, self.y, R * 1.7, (255, 170, 40),
               0.24 + 0.10 * math.sin(self.tempo * 4))

        facetas = [
            ([p0, p1, cc], (255, 235, 170)),   # mesa (mais clara)
            ([p0, p4, cc], (255, 185, 80)),
            ([p1, p2, cc], (235, 135, 25)),
            ([p4, cc, p3], (245, 150, 40)),
            ([p2, cc, p3], (175, 75, 10)),     # lado mais escuro
        ]
        for pts, cor in facetas:
            if self.flash > 0:                 # clareia ao levar tiro
                cor = tuple(min(255, k + 110) for k in cor)
            poligono = np.array(pts).astype(np.int32)
            cv2.fillPoly(img, [poligono], cor)
            cv2.polylines(img, [poligono], True, (255, 230, 180), 1, cv2.LINE_AA)
        contorno = np.array([p0, p1, p2, p3, p4]).astype(np.int32)
        cv2.polylines(img, [contorno], True, (255, 245, 220), 2, cv2.LINE_AA)

        if self.vida < self.vida_max:          # rachadura = feedback de dano
            trinca = np.array([(p0 + p1) / 2, cc + (p4 - cc) * 0.5,
                               (p3 + p2) / 2]).astype(np.int32)
            cv2.polylines(img, [trinca], False, (255, 255, 255), 2, cv2.LINE_AA)

        # reflexos que piscam
        b = math.sin(self.tempo * 5)
        if b > 0.55:
            estrela(img, p0[0], p0[1], R * 0.45 * b)
        b2 = math.sin(self.tempo * 4 + 2)
        if b2 > 0.6:
            estrela(img, p2[0], p2[1], R * 0.35 * b2)


class Jade(Objeto):
    """Pedra de jade verde: ao explodir, recupera 1 vida."""
    tipo = "jade"

    def __init__(self, nivel):
        super().__init__(nivel, (28, 40), 1.0, 1)
        n = 10
        self.base = np.array([
            [math.cos(2 * math.pi * i / n) * f, math.sin(2 * math.pi * i / n) * f]
            for i, f in ((i, random.uniform(0.9, 1.05)) for i in range(n))
        ])

    def desenhar(self, img):
        R = self.raio()
        centro = np.array([self.x, self.y])
        rot = self.rotacao()
        brilho(img, self.x, self.y, R * 1.6, (90, 230, 100),
               0.22 + 0.10 * math.sin(self.tempo * 4))
        ext = ((self.base * R) @ rot.T + centro).astype(np.int32)
        inte = ((self.base * R * 0.62) @ rot.T + centro).astype(np.int32)
        cor_ext, cor_int = (60, 160, 50), (130, 225, 120)
        if self.flash > 0:
            cor_ext, cor_int = (200, 255, 200), (255, 255, 255)
        cv2.fillPoly(img, [ext], cor_ext)
        cv2.fillPoly(img, [inte], cor_int)
        cv2.polylines(img, [ext], True, (30, 100, 30), 2, cv2.LINE_AA)
        cv2.polylines(img, [inte], True, (90, 190, 90), 1, cv2.LINE_AA)
        # "+" branco no centro indica cura
        t = max(3, int(R * 0.32))
        x, y = int(self.x), int(self.y)
        cv2.line(img, (x - t, y), (x + t, y), (255, 255, 255), 3, cv2.LINE_AA)
        cv2.line(img, (x, y - t), (x, y + t), (255, 255, 255), 3, cv2.LINE_AA)
        # reflexo
        b = math.sin(self.tempo * 4)
        if b > 0.6:
            estrela(img, x - R * 0.45, y - R * 0.5, R * 0.3 * b, (230, 255, 230))


class Bomba(Objeto):
    """Bomba: NAO atire. Se for estourada, o jogador perde 1 vida."""
    tipo = "bomba"

    def __init__(self, nivel):
        super().__init__(nivel, (24, 32), 0.0, 1)
        self.vx = random.uniform(-15, 15)

    def desenhar(self, img):
        x, y, r = int(self.x), int(self.y), max(6, int(self.raio()))
        pulso = math.sin(self.tempo * 8)
        brilho(img, x, y, r * 1.6, (0, 0, 255), 0.22 + 0.12 * pulso)
        cv2.circle(img, (x, y), r, (35, 35, 35), -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), r, (110, 110, 110), 2, cv2.LINE_AA)
        cv2.circle(img, (x - r // 3, y - r // 3), max(2, r // 5), (130, 130, 130), -1)
        # pavio com faisca
        ponta = (x + r // 2, y - r - r // 2)
        cv2.line(img, (x + r // 5, y - r + 2), ponta, (60, 110, 160), 3, cv2.LINE_AA)
        cv2.circle(img, ponta, random.randint(3, 6), (0, random.randint(140, 220), 255), -1)
        # anel vermelho piscando + "!" de alerta
        if pulso > 0:
            cv2.circle(img, (x, y), r + 7, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "!", (x - int(r * 0.2), y + int(r * 0.35)), FONTE,
                    r / 28, (0, 0, 255), 3, cv2.LINE_AA)


class Jogo:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.objetos = []
        self.particulas = []   # [x, y, vx, vy, vida, cor]
        self.aneis = []        # [x, y, tempo, cor]
        self.textos = []       # [x, y, tempo, texto, cor]
        self.aviso = None      # [tempo, texto]
        self.avisou_bombas = False
        self.pontos = 0
        self.vidas = VIDAS_MAX
        self.energia = 0.0
        self.combo = 0
        self.nivel = 0
        self.t_spawn = 0.0
        self.shake = 0.0
        self.fim = False

    # -- efeitos ------------------------------------------------------
    def explosao(self, x, y, n=22, cor=(0, 170, 255)):
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(60, 280)
            self.particulas.append([x, y, math.cos(a) * v, math.sin(a) * v,
                                    random.uniform(0.3, 0.8), cor])

    def perder_vida(self, x, y):
        self.vidas -= 1
        self.combo = 0
        self.shake = 0.5
        self.textos.append([x, y, 1.0, "-1 VIDA", (60, 60, 255)])
        if self.vidas <= 0:
            self.fim = True

    # -- acoes do jogador ---------------------------------------------
    def disparar(self, x, y):
        self.aneis.append([x, y, 0.0, (0, 255, 255)])
        alvo, melhor = None, 1e9
        for p in self.objetos:
            d = math.hypot(p.x - x, p.y - y)
            if d < p.raio() * 1.25 and d < melhor:
                alvo, melhor = p, d
        if alvo is None:
            self.combo = 0
            return

        if alvo.tipo == "bomba":               # estourou uma bomba: perde vida
            self.objetos.remove(alvo)
            self.explosao(alvo.x, alvo.y, 45, (0, 0, 255))
            self.explosao(alvo.x, alvo.y, 25, (0, 160, 255))
            self.perder_vida(alvo.x, alvo.y)
            return

        if alvo.tipo == "jade":                # jade: recupera 1 vida
            self.objetos.remove(alvo)
            self.combo += 1
            self.pontos += 20
            self.explosao(alvo.x, alvo.y, 35, (90, 230, 100))
            if self.vidas < VIDAS_MAX:
                self.vidas += 1
                self.textos.append([alvo.x, alvo.y, 1.0, "+1 VIDA", (90, 230, 100)])
            else:
                self.textos.append([alvo.x, alvo.y, 0.8, "+20", (90, 230, 100)])
            return

        alvo.vida -= 1
        alvo.flash = 0.12
        cor_hit = (255, 200, 90) if alvo.tipo == "diamante" else (200, 220, 255)
        self.explosao(alvo.x, alvo.y, 8, cor_hit)
        if alvo.vida <= 0:
            self.objetos.remove(alvo)
            self.combo += 1
            diamante = alvo.tipo == "diamante"
            ganho = (30 if diamante else 10) * min(self.combo, 5)
            self.pontos += ganho
            self.energia = min(100.0, self.energia + (30 if diamante else 14))
            self.explosao(alvo.x, alvo.y, 40 if diamante else 26,
                          (255, 180, 60) if diamante else (0, 170, 255))
            self.textos.append([alvo.x, alvo.y, 0.8, f"+{ganho}",
                                (255, 220, 120) if diamante else (0, 255, 255)])

    def bomba(self):
        for p in self.objetos:
            if p.tipo == "bomba":              # bombas somem sem pontos nem penalidade
                self.explosao(p.x, p.y, 15, (120, 120, 120))
            elif p.tipo == "jade":             # jade some sem curar
                self.explosao(p.x, p.y, 15, (90, 230, 100))
            else:
                self.pontos += 30 if p.tipo == "diamante" else 10
                self.explosao(p.x, p.y, 20, (255, 120, 0))
        self.objetos.clear()
        self.energia = 0.0
        self.shake = 0.4
        self.aneis.append([L // 2, A // 2, 0.0, (255, 160, 0)])

    # -- atualizacao --------------------------------------------------
    def novo_objeto(self):
        p_bomba = 0.0
        if self.nivel >= NIVEL_BOMBAS:
            p_bomba = min(0.12 + 0.04 * (self.nivel - NIVEL_BOMBAS), 0.30)
        # jade so aparece se o jogador precisa de vida
        p_jade = 0.10 if (self.nivel >= NIVEL_JADE and self.vidas < VIDAS_MAX) else 0.0
        x = random.random()
        if x < p_bomba:
            return Bomba(self.nivel)
        if x < p_bomba + p_jade:
            return Jade(self.nivel)
        if x < p_bomba + p_jade + 0.18:
            return Diamante(self.nivel)
        return Pedra(self.nivel)

    def atualizar(self, dt):
        if self.fim:
            return
        self.nivel = self.pontos // 150
        if self.nivel >= NIVEL_BOMBAS and not self.avisou_bombas:
            self.avisou_bombas = True
            self.aviso = [3.0, "CUIDADO: BOMBAS! NAO ATIRE NELAS!"]

        self.t_spawn -= dt
        if self.t_spawn <= 0:
            self.objetos.append(self.novo_objeto())
            self.t_spawn = max(0.5, 1.6 - self.nivel * 0.12)

        for p in self.objetos[:]:
            p.atualizar(dt)
            if p.y - p.raio() > A:
                self.objetos.remove(p)
                if p.tipo in ("bomba", "jade"):  # cair no chao: sem penalidade
                    continue
                self.explosao(p.x, A - 10, 18, (0, 0, 255))
                self.perder_vida(p.x, A - 50)

        for q in self.particulas[:]:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[4] -= dt
            if q[4] <= 0:
                self.particulas.remove(q)
        for r in self.aneis[:]:
            r[2] += dt
            if r[2] > 0.5:
                self.aneis.remove(r)
        for t in self.textos[:]:
            t[1] -= 40 * dt
            t[2] -= dt
            if t[2] <= 0:
                self.textos.remove(t)
        if self.aviso:
            self.aviso[0] -= dt
            if self.aviso[0] <= 0:
                self.aviso = None
        self.shake = max(0.0, self.shake - dt)

    # -- desenho ------------------------------------------------------
    def desenhar(self, img):
        for p in self.objetos:
            p.desenhar(img)
        for q in self.particulas:
            cv2.circle(img, (int(q[0]), int(q[1])), max(1, int(q[4] * 6)), q[5], -1)
        for x, y, t, cor in self.aneis:
            cv2.circle(img, (int(x), int(y)), int(10 + t * 220), cor, 2, cv2.LINE_AA)
        for x, y, t, txt, cor in self.textos:
            cv2.putText(img, txt, (int(x), int(y)), FONTE, 0.8, cor, 2, cv2.LINE_AA)
        if self.aviso and int(self.aviso[0] * 4) % 2 == 0:   # texto piscando
            centralizado(img, self.aviso[1], 150, 1.0, (0, 0, 255), 3)

    def hud(self, img, estado, dedos):
        cv2.putText(img, f"Pontos: {self.pontos}", (20, 35), FONTE, 0.9, (255, 255, 255), 2)
        cv2.putText(img, f"Nivel: {self.nivel + 1}", (20, 68), FONTE, 0.6, (200, 200, 200), 2)
        if self.combo > 1:
            cv2.putText(img, f"Combo x{min(self.combo, 5)}", (20, 98), FONTE, 0.7, (0, 255, 255), 2)
        for i in range(self.vidas):
            cv2.circle(img, (L - 30 - i * 32, 30), 11, (60, 60, 255), -1)
        # barra de energia
        cv2.rectangle(img, (L - 220, 55), (L - 20, 75), (80, 80, 80), 2)
        cheia = self.energia >= 100
        cv2.rectangle(img, (L - 218, 57),
                      (L - 218 + int(196 * self.energia / 100), 73),
                      (0, 200, 255) if cheia else (255, 160, 0), -1)
        if cheia:
            cv2.putText(img, "BOMBA PRONTA: tecle ESPACO", (L - 300, 98),
                        FONTE, 0.55, (0, 255, 255), 2)
        txt = f"Mao: {estado}" + (f" ({dedos} dedos)" if dedos is not None else "")
        cv2.putText(img, txt, (20, A - 15), FONTE, 0.6, (0, 255, 0), 2)
        cv2.putText(img, "Feche a mao = tiro | ESPACO = bomba | nao atire nas bombas | P pausa",
                    (L - 640, A - 15), FONTE, 0.5, (200, 200, 200), 1)


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def novo_deco(inicial=False):
    o = random.choice([Pedra, Pedra, Diamante, Jade])(0)
    if inicial:
        o.y = random.uniform(-40, A)
    return o


def desenhar_menu(img, hover):
    centralizado(img, "ROCK BLASTER", 150, 2.4, (0, 0, 0), 8, desl=4)       # sombra
    centralizado(img, "ROCK BLASTER", 150, 2.4, (0, 200, 255), 5)
    centralizado(img, "Destrua as rochas com as maos!", 205, 0.9, (255, 255, 255), 2)
    desenhar_botao(img, BOTAO_PLAY, "JOGAR", hover)
    if hover:
        centralizado(img, "FECHE A MAO PARA COMECAR!", 400, 0.8, (0, 255, 255), 2)
    else:
        centralizado(img, "Leve a mira ate o botao", 400, 0.7, (230, 230, 230), 2)
    centralizado(img, "(clique do mouse ou ENTER tambem iniciam)", 428, 0.5, (170, 170, 170), 1)
    centralizado(img, "Mao = mira | Fechar a mao = tiro | ESPACO = super bomba (barra cheia)",
                 470, 0.55, (255, 255, 255), 1)
    centralizado(img, "Diamantes azuis: 2 tiros e valem mais | Nivel 4+: NAO atire nas bombas!",
                 498, 0.55, (255, 200, 120), 1)
    centralizado(img, "Jade verde: estoure para recuperar 1 vida",
                 522, 0.55, (130, 230, 130), 1)


def cb_mouse(evento, x, y, flags, ctrl):
    ctrl["mouse"] = (x, y)
    if evento == cv2.EVENT_LBUTTONDOWN:
        ctrl["clique"] = True


# ----------------------------------------------------------------------
def main():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Nao foi possivel acessar a webcam.")
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, L)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, A)

    ctrl = {"mouse": (L // 2, A // 2), "clique": False}
    cv2.namedWindow(JANELA)
    cv2.setMouseCallback(JANELA, cb_mouse, ctrl)

    jogo = Jogo()
    tela = "menu"                      # "menu" | "jogando"
    deco = [novo_deco(True) for _ in range(7)]   # objetos decorativos do menu
    historico = deque(maxlen=5)        # ultimos estados (suavizacao)
    pos_hist = deque(maxlen=4)         # posicoes da mira (acao usa a mais antiga)
    estavel = anterior = "nao detectada"
    mira = np.array([L / 2, A / 2])
    cooldown = 0.0
    pausado = False
    mostrar_landmarks = True
    tecla_bomba = tecla_enter = False
    t_ant = time.time()

    with mp_hands.Hands(max_num_hands=1,
                        min_detection_confidence=0.6,
                        min_tracking_confidence=0.5) as maos:
        while True:
            ok, frame = cam.read()
            if not ok:
                break
            agora = time.time()
            dt = min(agora - t_ant, 0.1)
            t_ant = agora

            frame = cv2.flip(frame, 1)                 # efeito espelho
            frame = cv2.resize(frame, (L, A))
            res = maos.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = cv2.convertScaleAbs(frame, alpha=0.45 if tela == "menu" else 0.65, beta=0)

            dedos = None
            hand = None
            mao_ok = bool(res.multi_hand_landmarks)

            if mao_ok:
                hand = res.multi_hand_landmarks[0]
                dedos = contar_dedos(hand)
                historico.append(estado_mao(hand))
                estado, cont = Counter(historico).most_common(1)[0]
                if cont >= 3:
                    estavel = estado
                cx, cy = centro_palma(hand)
                alvo = np.array([cx * L, cy * A])
                mira += (alvo - mira) * 0.5            # suaviza a mira
                pos_hist.append(mira.copy())
            else:
                historico.clear()
                estavel = "nao detectada"
                mira = np.array(ctrl["mouse"], dtype=float)
                pos_hist.clear()

            # "fechou" = transicao para mao fechada (gesto de tiro / clique)
            fechou = mao_ok and estavel == "fechada" and anterior != "fechada"
            ponto_acao = pos_hist[0] if (fechou and pos_hist) else mira
            cooldown = max(0.0, cooldown - dt)

            # ---------------------------- MENU ----------------------------
            if tela == "menu":
                for o in deco[:]:
                    o.atualizar(dt)
                    if o.y - o.raio() > A:
                        deco.remove(o)
                if len(deco) < 7 and random.random() < dt * 2:
                    deco.append(novo_deco())
                for o in deco:
                    o.desenhar(img)

                hover = dentro(BOTAO_PLAY, mira)
                clicou = ((fechou and dentro(BOTAO_PLAY, ponto_acao))
                          or (ctrl["clique"] and dentro(BOTAO_PLAY, ctrl["mouse"]))
                          or tecla_enter)
                desenhar_menu(img, hover)
                if clicou:
                    jogo.reiniciar()
                    tela = "jogando"
                    pausado = False
                    cooldown = 0.5                     # evita tiro logo ao iniciar

            # ---------------------------- JOGO ----------------------------
            else:
                if not pausado and not jogo.fim:
                    disparo, ponto = False, mira
                    if fechou:
                        disparo, ponto = True, ponto_acao
                    if ctrl["clique"]:
                        disparo = True
                    if disparo and cooldown <= 0:
                        jogo.disparar(float(ponto[0]), float(ponto[1]))
                        cooldown = 0.25

                    # super bomba: tecla ESPACO (exige energia cheia)
                    if tecla_bomba:
                        if jogo.energia >= 100:
                            jogo.bomba()
                        else:
                            jogo.textos.append([mira[0], mira[1], 0.8,
                                                "Energia insuficiente", (255, 255, 255)])
                    jogo.atualizar(dt)

                jogo.desenhar(img)
                jogo.hud(img, estavel, dedos)

                if jogo.shake > 0:   # tremor de tela (translacao aleatoria)
                    dx, dy = random.randint(-6, 6), random.randint(-6, 6)
                    M = np.float32([[1, 0, dx], [0, 1, dy]])
                    img = cv2.warpAffine(img, M, (L, A))

                if pausado:
                    centralizado(img, "PAUSADO", A // 2, 1.8, (255, 255, 255))
                if jogo.fim:
                    centralizado(img, "FIM DE JOGO", A // 2 - 30, 1.8, (0, 0, 255))
                    centralizado(img, f"Pontos: {jogo.pontos}", A // 2 + 25, 0.9, (255, 255, 255), 2)
                    desenhar_botao(img, BOTAO_NOVO, "JOGAR DE NOVO", dentro(BOTAO_NOVO, mira))
                    centralizado(img, "(feche a mao sobre o botao | R reinicia | M menu)",
                                 A // 2 + 175, 0.55, (200, 200, 200), 1)
                    if ((fechou and dentro(BOTAO_NOVO, ponto_acao))
                            or (ctrl["clique"] and dentro(BOTAO_NOVO, ctrl["mouse"]))):
                        jogo.reiniciar()
                        cooldown = 0.5

            # mao e mira por cima de tudo
            if hand is not None and mostrar_landmarks:
                mp_drawing.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)
            desenhar_mira(img, mira[0], mira[1], estavel)

            anterior = estavel
            ctrl["clique"] = False
            tecla_bomba = tecla_enter = False

            cv2.imshow(JANELA, img)
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break
            elif k in (ord("p"), ord("P")) and tela == "jogando":
                pausado = not pausado
            elif k in (ord("r"), ord("R")) and tela == "jogando":
                jogo.reiniciar()
                pausado = False
            elif k in (ord("m"), ord("M")):
                tela = "menu"
                pausado = False
            elif k in (ord("h"), ord("H")):
                mostrar_landmarks = not mostrar_landmarks
            elif k == 13:
                tecla_enter = True
            elif k == 32:
                tecla_bomba = True

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
