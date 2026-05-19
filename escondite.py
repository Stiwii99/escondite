#!/usr/bin/env python3
"""
¡Escóndete! - Juego Multijugador de Escondite
Proyecto de Programación - Primer Semestre

Requiere: pip install pygame
Ejecutar:  python escondite.py
"""

import pygame
import sys
import math
import random
import time
import array

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────
pygame.init()
AUDIO = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except Exception:
    AUDIO = False

W, H = 860, 640
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Escondete!")
clock = pygame.time.Clock()
FPS = 60

CW, CH = 700, 400              # Canvas del juego (mapa)
CANVAS_X = (W - CW) // 2
CANVAS_Y = 120
canvas = pygame.Surface((CW, CH))

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
VELOCIDAD       = 2.8
SR              = 14     # Radio buscador
HR              = 11     # Radio escondido
REVELAR_R       = 100    # Distancia para revelar al escondido
ENCONTRAR_R     = 26     # Distancia para atrapar
TIEMPO_JUEGO    = 90
TIEMPO_ESCONDER = 5

# ─────────────────────────────────────────────────────────────────────────────
# COLORES
# ─────────────────────────────────────────────────────────────────────────────
BG     = (15, 15, 26)
PANEL  = (22, 33, 62)
ROJO   = (231, 76, 60)
BLANCO = (255, 255, 255)
GRIS   = (90, 106, 138)
VERDE  = (46, 204, 113)
OSCURO = (13, 26, 48)
BORDE  = (30, 45, 82)
NEGRO  = (0, 0, 0)

COLORES_JUGADORES = [
    (231, 76,  60),
    (52,  152, 219),
    (46,  204, 113),
    (241, 196, 15),
    (155, 89,  182),
    (230, 126, 34),
]

# ─────────────────────────────────────────────────────────────────────────────
# FUENTES
# ─────────────────────────────────────────────────────────────────────────────
def cargar_fuentes():
    nombres = ["Arial", "Helvetica", "DejaVu Sans", "FreeSans", None]
    for nombre in nombres:
        try:
            return {
                'xl':   pygame.font.SysFont(nombre, 52, bold=True),
                'lg':   pygame.font.SysFont(nombre, 32, bold=True),
                'md':   pygame.font.SysFont(nombre, 22, bold=True),
                'sm':   pygame.font.SysFont(nombre, 16),
                'xs':   pygame.font.SysFont(nombre, 13),
                'mono': pygame.font.SysFont("Courier New", 17, bold=True),
            }
        except Exception:
            continue
    base = pygame.font.Font(None, 24)
    return {k: base for k in ('xl','lg','md','sm','xs','mono')}

F = cargar_fuentes()

# ─────────────────────────────────────────────────────────────────────────────
# MAPAS
# ─────────────────────────────────────────────────────────────────────────────
MAPAS = [
    {
        "nombre": "Bosque", "tipo": "forest",
        "piso": (74, 124, 47), "pared": (26, 66, 10), "acc": (47, 96, 21),
        "obs": [
            (10,10,65,55),(155,8,60,60),(280,12,60,52),(410,8,60,58),(535,10,60,54),
            (10,150,55,58),(155,147,65,58),(295,150,55,56),(428,147,60,58),(565,150,58,56),
            (10,285,63,65),(163,283,55,67),(303,285,63,65),(450,283,58,67),(571,285,55,65),
        ],
    },
    {
        "nombre": "Ciudad", "tipo": "city",
        "piso": (122, 122, 122), "pared": (42, 42, 42), "acc": (64, 64, 64),
        "obs": [
            (10,10,88,78),(160,10,88,78),(310,10,88,78),(460,10,88,78),
            (10,136,88,78),(160,136,88,78),(310,136,88,78),(460,136,88,78),
            (10,262,88,78),(160,262,88,78),(310,262,88,78),(460,262,88,78),
        ],
    },
    {
        "nombre": "Cueva", "tipo": "cave",
        "piso": (20, 33, 62), "pared": (9, 14, 30), "acc": (26, 39, 68),
        "obs": [
            (5,5,112,58),(220,5,112,58),(435,5,112,58),
            (5,150,98,72),(218,145,118,72),(455,150,98,72),
            (5,280,112,74),(222,275,108,74),(440,280,108,74),
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# MUSICA 8-BIT
# ─────────────────────────────────────────────────────────────────────────────
MELODIA = [523,659,784,1047,784,659,523,440,523,659,784,659,523,440,392,440]
_cache_tonos = {}

def generar_tono(freq):
    if not AUDIO:
        return None
    if freq in _cache_tonos:
        return _cache_tonos[freq]
    try:
        sr, ms = 22050, 175
        n = int(sr * ms / 1000)
        buf = array.array('h')
        for i in range(n):
            t = i / sr
            fade = 1.0 if i < n * 0.7 else (n - i) / (n * 0.3)
            val = 0.07 if (t * freq) % 1.0 < 0.5 else -0.07
            buf.append(int(val * fade * 32767))
        _cache_tonos[freq] = pygame.mixer.Sound(buffer=buf)
    except Exception:
        _cache_tonos[freq] = None
    return _cache_tonos[freq]

if AUDIO:
    for f_ in set(MELODIA):
        generar_tono(f_)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE DIBUJO
# ─────────────────────────────────────────────────────────────────────────────
def dtxt(sup, texto, fuente, color, pos, ancla="center"):
    s = fuente.render(str(texto), True, color)
    r = s.get_rect()
    setattr(r, ancla, pos)
    sup.blit(s, r)
    return r

def rect_r(sup, rect, color, radio=8, grosor=0, borde=None):
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    if grosor and borde:
        pygame.draw.rect(sup, borde, rect, grosor, border_radius=radio)

def boton(sup, rect, texto, fuente, bg, fg=BLANCO, radio=8):
    rect_r(sup, rect, bg, radio)
    cx, cy = rect[0]+rect[2]//2, rect[1]+rect[3]//2
    dtxt(sup, texto, fuente, fg, (cx, cy))

# ─────────────────────────────────────────────────────────────────────────────
# COLISIONES Y POSICIONES
# ─────────────────────────────────────────────────────────────────────────────
def circulo_rect(cx, cy, cr, rx, ry, rw, rh):
    nx = max(rx, min(cx, rx+rw))
    ny = max(ry, min(cy, ry+rh))
    return (cx-nx)**2 + (cy-ny)**2 < cr*cr

def pos_aleatoria(obs, r, margen=15):
    for _ in range(500):
        x = margen+r + random.random()*(CW - 2*(margen+r))
        y = margen+r + random.random()*(CH - 2*(margen+r))
        if not any(circulo_rect(x, y, r+7, ox, oy, ow, oh) for ox,oy,ow,oh in obs):
            return x, y
    return CW//2, CH//2

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
E = {
    # Pantalla actual
    "pantalla":       "menu",
    # Jugadores
    "jugadores":      ["Jugador 1", "Jugador 2"],
    "mapa":           MAPAS[0],
    "buscador_idx":   0,
    "editar_idx":     0,
    # Revelar buscador
    "rev_timer":      0.0,
    "rev_listo":      False,
    "rev_final":      0,
    # Esconderse
    "esc_timer":      float(TIEMPO_ESCONDER),
    # Juego
    "bx":             CW//2,
    "by":             CH//2,
    "escondidos":     [],
    "tiempo":         float(TIEMPO_JUEGO),
    "mensaje":        "",
    "msg_timer":      0.0,
    "teclas":         set(),
    # Musica
    "mus_beat":       0,
    "mus_ultimo":     0,
    # Resultados
    "resultados":     None,
}

# ─────────────────────────────────────────────────────────────────────────────
# INICIAR PARTIDA
# ─────────────────────────────────────────────────────────────────────────────
def iniciar_juego():
    obs = E["mapa"]["obs"]
    si  = E["buscador_idx"]
    esc = []
    for i, nombre in enumerate(E["jugadores"]):
        if i == si:
            continue
        x, y = pos_aleatoria(obs, HR)
        esc.append({
            "nombre":    nombre,
            "color":     COLORES_JUGADORES[(si + 1 + len(esc)) % len(COLORES_JUGADORES)],
            "x": x, "y": y,
            "encontrado": False,
        })
    bx, by = pos_aleatoria(obs, SR)
    E["bx"] = bx;  E["by"] = by
    E["escondidos"]  = esc
    E["tiempo"]      = float(TIEMPO_JUEGO)
    E["mensaje"]     = ""
    E["msg_timer"]   = 0.0
    E["teclas"]      = set()
    E["pantalla"]    = "juego"

# ─────────────────────────────────────────────────────────────────────────────
# EVENTOS
# ─────────────────────────────────────────────────────────────────────────────
def manejar_evento(event):
    p = E["pantalla"]

    if p == "menu":
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            E["pantalla"] = "configurar"

    elif p == "configurar":
        if event.type == pygame.KEYDOWN:
            idx = E["editar_idx"]
            k   = event.key
            if k == pygame.K_ESCAPE:
                E["pantalla"] = "menu"
            elif k == pygame.K_RETURN:
                ok = all(j.strip() for j in E["jugadores"]) and len(E["jugadores"]) >= 2
                if idx < len(E["jugadores"]) - 1:
                    E["editar_idx"] += 1
                elif ok:
                    E["pantalla"] = "elegir_mapa"
            elif k == pygame.K_TAB:
                E["editar_idx"] = (idx + 1) % len(E["jugadores"])
            elif k == pygame.K_BACKSPACE:
                E["jugadores"][idx] = E["jugadores"][idx][:-1]
            elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                if len(E["jugadores"]) < 6:
                    E["jugadores"].append(f"Jugador {len(E['jugadores'])+1}")
            elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                if len(E["jugadores"]) > 2:
                    E["jugadores"].pop()
                    E["editar_idx"] = min(E["editar_idx"], len(E["jugadores"])-1)
            else:
                c = event.unicode
                if c.isprintable() and len(E["jugadores"][idx]) < 14:
                    E["jugadores"][idx] += c

    elif p == "elegir_mapa":
        if event.type == pygame.KEYDOWN:
            if   event.key == pygame.K_1: E["mapa"] = MAPAS[0]
            elif event.key == pygame.K_2: E["mapa"] = MAPAS[1]
            elif event.key == pygame.K_3: E["mapa"] = MAPAS[2]
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                E["rev_timer"] = 0.0
                E["rev_listo"] = False
                E["rev_final"] = random.randint(0, len(E["jugadores"])-1)
                E["buscador_idx"] = 0
                E["pantalla"] = "revelar"
            elif event.key == pygame.K_ESCAPE:
                E["pantalla"] = "configurar"

    elif p == "revelar":
        if event.type == pygame.KEYDOWN and E["rev_listo"]:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                E["esc_timer"] = float(TIEMPO_ESCONDER)
                E["pantalla"]  = "esconderse"

    elif p == "juego":
        if event.type == pygame.KEYDOWN:
            E["teclas"].add(event.key)
        elif event.type == pygame.KEYUP:
            E["teclas"].discard(event.key)

    elif p == "resultados":
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                E["editar_idx"] = 0
                E["pantalla"]   = "configurar"
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                E["pantalla"]   = "menu"

# ─────────────────────────────────────────────────────────────────────────────
# ACTUALIZACIÓN LÓGICA
# ─────────────────────────────────────────────────────────────────────────────
def actualizar(dt, ms_actual):
    p = E["pantalla"]

    # Música en el menú
    if p == "menu" and AUDIO:
        if ms_actual - E["mus_ultimo"] >= 200:
            i    = E["mus_beat"] % len(MELODIA)
            tono = generar_tono(MELODIA[i])
            if tono:
                try: tono.play()
                except Exception: pass
            E["mus_beat"]   += 1
            E["mus_ultimo"]  = ms_actual

    elif p == "revelar":
        E["rev_timer"] += dt
        if not E["rev_listo"]:
            if E["rev_timer"] < 1.8:
                E["buscador_idx"] = int(E["rev_timer"] * 10) % len(E["jugadores"])
            else:
                E["buscador_idx"] = E["rev_final"]
                E["rev_listo"]    = True

    elif p == "esconderse":
        E["esc_timer"] -= dt
        if E["esc_timer"] <= 0:
            iniciar_juego()

    elif p == "juego":
        obs = E["mapa"]["obs"]
        dx = dy = 0.0
        if pygame.K_LEFT  in E["teclas"] or pygame.K_a in E["teclas"]: dx -= 1
        if pygame.K_RIGHT in E["teclas"] or pygame.K_d in E["teclas"]: dx += 1
        if pygame.K_UP    in E["teclas"] or pygame.K_w in E["teclas"]: dy -= 1
        if pygame.K_DOWN  in E["teclas"] or pygame.K_s in E["teclas"]: dy += 1
        if dx and dy:
            dx *= 0.707; dy *= 0.707

        bx, by = E["bx"], E["by"]
        nx, ny = bx + dx*VELOCIDAD, by + dy*VELOCIDAD
        if SR <= nx <= CW-SR and not any(circulo_rect(nx, by, SR, *o) for o in obs):
            E["bx"] = nx
        if SR <= ny <= CH-SR and not any(circulo_rect(E["bx"], ny, SR, *o) for o in obs):
            E["by"] = ny

        for h in E["escondidos"]:
            if h["encontrado"]: continue
            if (E["bx"]-h["x"])**2 + (E["by"]-h["y"])**2 < ENCONTRAR_R**2:
                h["encontrado"] = True
                E["mensaje"]   = f"Encontraste a {h['nombre']}!"
                E["msg_timer"] = 2.5

        if E["msg_timer"] > 0:
            E["msg_timer"] -= dt
        E["tiempo"] = max(0.0, E["tiempo"] - dt)

        enc = sum(1 for h in E["escondidos"] if h["encontrado"])
        if enc == len(E["escondidos"]) or E["tiempo"] <= 0:
            E["resultados"] = {
                "encontrados": enc,
                "total":       len(E["escondidos"]),
                "tiempo_r":    int(E["tiempo"]),
                "buscador":    E["jugadores"][E["buscador_idx"]],
                "color_b":     COLORES_JUGADORES[E["buscador_idx"] % len(COLORES_JUGADORES)],
                "escondidos":  [dict(h) for h in E["escondidos"]],
            }
            E["pantalla"] = "resultados"

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — MENU
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_menu():
    screen.fill(BG)
    dtxt(screen, "Escondete!",                         F['xl'], ROJO,  (W//2, H//2-110))
    dtxt(screen, "Juego Multijugador de Escondite",    F['sm'], GRIS,  (W//2, H//2-55))
    dtxt(screen, "2 a 6 jugadores  |  3 mapas  |  90 segundos", F['xs'], (40,55,80), (W//2, H//2-22))
    boton(screen, (W//2-95, H//2+15, 190, 50), "Jugar!  [Enter]", F['md'], ROJO)
    nota = "Musica activada :)" if AUDIO else "Sin audio (instala pygame con mixer)"
    dtxt(screen, nota, F['xs'], (50,80,110), (W//2, H//2+92))

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — CONFIGURAR JUGADORES
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_configurar():
    screen.fill(BG)
    dtxt(screen, "Quienes juegan?", F['lg'], BLANCO, (W//2, 50))
    dtxt(screen, "[Tab] cambiar campo  |  [+] agregar  |  [-] quitar  |  [Enter] continuar",
         F['xs'], GRIS, (W//2, 82))

    for i, nombre in enumerate(E["jugadores"]):
        y      = 115 + i*58
        activo = (i == E["editar_idx"])
        pygame.draw.circle(screen, COLORES_JUGADORES[i % len(COLORES_JUGADORES)], (W//2-135, y+18), 12)
        rect_r(screen, (W//2-115, y, 230, 36),
               PANEL if activo else OSCURO, 6, 1, ROJO if activo else BORDE)
        cursor = "|" if activo and int(time.time()*2) % 2 == 0 else ""
        dtxt(screen, nombre+cursor, F['sm'], BLANCO, (W//2-115+10, y+18), "midleft")

    y_btn = 125 + len(E["jugadores"])*58
    ok    = all(j.strip() for j in E["jugadores"]) and len(E["jugadores"]) >= 2
    boton(screen, (W//2-85, y_btn,    170, 42), "Continuar -->",  F['sm'], ROJO if ok else (70,30,30))
    boton(screen, (W//2-85, y_btn+52, 170, 38), "<-- Menu [Esc]", F['sm'], (50,50,70))

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — ELEGIR MAPA
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_elegir_mapa():
    screen.fill(BG)
    dtxt(screen, "Elige el mapa", F['lg'], BLANCO, (W//2, 48))

    for i, m in enumerate(MAPAS):
        x   = W//2 - 280 + i*195
        y   = H//2 - 90
        sel = E["mapa"]["nombre"] == m["nombre"]
        rect_r(screen, (x, y, 165, 165), (30,50,90) if sel else PANEL, 10, 2 if sel else 1, ROJO if sel else BORDE)
        # Mini-preview
        mini = pygame.Surface((135, 90))
        mini.fill(m["piso"])
        for obs in m["obs"][:6]:
            ox_, oy_, ow_, oh_ = obs
            pygame.draw.rect(mini, m["pared"],
                             (int(ox_*135/CW), int(oy_*90/CH), max(4, int(ow_*135/CW)), max(4, int(oh_*90/CH))))
        screen.blit(mini, (x+15, y+10))
        dtxt(screen, m["nombre"], F['sm'], BLANCO, (x+82, y+115))
        dtxt(screen, f"[{i+1}]",   F['xs'], GRIS,   (x+82, y+135))

    boton(screen, (W//2-90, H//2+92, 180, 44), "Empezar! [Enter]", F['sm'], ROJO)
    boton(screen, (W//2-90, H//2+146, 180, 38), "<-- Atras [Esc]", F['sm'], (50,50,70))

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — REVELAR BUSCADOR
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_revelar():
    screen.fill(BG)
    dtxt(screen, "Eligiendo al buscador...", F['lg'], BLANCO, (W//2, 72))
    idx   = E["buscador_idx"]
    color = COLORES_JUGADORES[idx % len(COLORES_JUGADORES)]
    rect_r(screen, (W//2-145, H//2-75, 290, 130), PANEL, 12, 1, BORDE)
    dtxt(screen, "El buscador es:",          F['xs'], GRIS,  (W//2, H//2-50))
    dtxt(screen, E["jugadores"][idx],        F['lg'], color, (W//2, H//2+5))
    if E["rev_listo"]:
        dtxt(screen, "No mires mientras se esconden!  :)", F['xs'], GRIS, (W//2, H//2+70))
        boton(screen, (W//2-115, H//2+105, 230, 44), "Entendido! [Enter]", F['sm'], ROJO)
    else:
        spin = ["|", "/", "-", "\\"][int(pygame.time.get_ticks()/100) % 4]
        dtxt(screen, spin, F['lg'], GRIS, (W//2, H//2+85))

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — ESCONDERSE (COUNTDOWN)
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_esconderse():
    screen.fill(BG)
    dtxt(screen, "Buscador no mires!  :O", F['lg'], ROJO, (W//2, 95))
    rect_r(screen, (W//2-120, H//2-85, 240, 148), PANEL, 12, 1, BORDE)
    dtxt(screen, "Escondiendose...",               F['xs'], GRIS, (W//2, H//2-60))
    dtxt(screen, str(max(0, math.ceil(E["esc_timer"]))), F['xl'], ROJO, (W//2, H//2+5))
    dtxt(screen, "segundos",                       F['xs'], GRIS, (W//2, H//2+55))

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — JUEGO (CANVAS)
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_juego():
    screen.fill(BG)
    mp  = E["mapa"]
    obs = mp["obs"]
    bx, by = E["bx"], E["by"]

    canvas.fill(mp["piso"])

    # Obstáculos con detalle por mapa
    for ox, oy, ow, oh in obs:
        pygame.draw.rect(canvas, mp["pared"], (ox, oy, ow, oh))
        pygame.draw.rect(canvas, mp["acc"],   (ox+3, oy+3, ow-6, oh-6))
        pygame.draw.rect(canvas, NEGRO,       (ox, oy, ow, oh), 1)
        if mp["tipo"] == "forest":
            cx2 = ox + ow//2
            pygame.draw.circle(canvas, (30, 77, 10),  (cx2, oy+int(oh*.44)), int(ow*.38))
            pygame.draw.circle(canvas, (58,112, 24),  (cx2, oy+int(oh*.38)), int(ow*.27))
        elif mp["tipo"] == "city":
            for wy in range(oy+9, oy+oh-9, 17):
                for wx in range(ox+9, ox+ow-9, 17):
                    pygame.draw.rect(canvas, (200, 200, 80), (wx, wy, 8, 8))

    # Radio de detección (círculo sutil)
    pygame.draw.circle(canvas, (50, 60, 90), (int(bx), int(by)), REVELAR_R, 1)

    # Escondidos con efecto niebla
    for h in E["escondidos"]:
        dist = math.hypot(bx-h["x"], by-h["y"])
        if h["encontrado"]:
            alpha = 70
        elif dist < REVELAR_R:
            ratio = 1.0 - (dist - ENCONTRAR_R) / max(1, REVELAR_R - ENCONTRAR_R)
            alpha = max(30, min(255, int(255*ratio)))
        else:
            continue  # invisible

        sf = pygame.Surface((HR*2+2, HR*2+2), pygame.SRCALPHA)
        pygame.draw.circle(sf, (*h["color"], alpha), (HR+1, HR+1), HR)
        if not h["encontrado"]:
            pygame.draw.circle(sf, (255,255,255, alpha), (HR+1, HR+1), HR, 2)
        canvas.blit(sf, (int(h["x"])-HR-1, int(h["y"])-HR-1))
        if not h["encontrado"] and dist < REVELAR_R*0.55:
            dtxt(canvas, "?", F['sm'], BLANCO, (int(h["x"]), int(h["y"])))

    # Buscador
    pygame.draw.circle(canvas, BLANCO, (int(bx), int(by)), SR+4, 2)
    sc = COLORES_JUGADORES[E["buscador_idx"] % len(COLORES_JUGADORES)]
    pygame.draw.circle(canvas, sc,     (int(bx), int(by)), SR)
    pygame.draw.circle(canvas, BLANCO, (int(bx), int(by)), SR, 2)
    dtxt(canvas, E["jugadores"][E["buscador_idx"]][0].upper(), F['sm'], BLANCO, (int(bx), int(by)))

    # HUD superior
    hud_top = pygame.Surface((CW, 30), pygame.SRCALPHA)
    hud_top.fill((0, 0, 0, 175))
    canvas.blit(hud_top, (0, 0))
    # HUD inferior
    hud_bot = pygame.Surface((CW, 22), pygame.SRCALPHA)
    hud_bot.fill((0, 0, 0, 155))
    canvas.blit(hud_bot, (0, CH-22))

    enc = sum(1 for h in E["escondidos"] if h["encontrado"])
    dtxt(canvas, f"Encontrados: {enc}/{len(E['escondidos'])}", F['xs'], VERDE, (8, 15), "midleft")

    tl    = max(0, math.ceil(E["tiempo"]))
    c_tl  = ROJO if tl < 20 else BLANCO
    dtxt(canvas, f"Tiempo: {tl}s", F['mono'], c_tl, (CW//2, 15))

    nom_b = E["jugadores"][E["buscador_idx"]]
    dtxt(canvas, f"Buscador: {nom_b}", F['xs'], GRIS, (CW-8, 15), "midright")
    dtxt(canvas, "WASD / Flechas para mover", F['xs'], (130,140,170), (CW//2, CH-11))

    # Flash de captura
    if E["mensaje"] and E["msg_timer"] > 0:
        alpha_f = min(230, int(E["msg_timer"]*120))
        fs = pygame.Surface((320, 50), pygame.SRCALPHA)
        fs.fill((0, 0, 0, alpha_f))
        pygame.draw.rect(fs, (46,204,113, alpha_f//2), (0,0,320,50), border_radius=10)
        dtxt(fs, E["mensaje"], F['md'], VERDE, (160, 25))
        canvas.blit(fs, (CW//2-160, CH//2-25))

    # Volcar canvas al screen
    screen.blit(canvas, (CANVAS_X, CANVAS_Y))
    pygame.draw.rect(screen, BORDE, (CANVAS_X-2, CANVAS_Y-2, CW+4, CH+4), 2, border_radius=8)

# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO — RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────
def dibujar_resultados():
    screen.fill(BG)
    r = E["resultados"]
    if not r: return

    gano   = r["encontrados"] == r["total"]
    titulo = "El buscador gano! :)" if gano else "Se acabo el tiempo! :("
    dtxt(screen, titulo, F['lg'], BLANCO, (W//2, 48))

    alto_panel = 200 + len(r["escondidos"]) * 42
    px, py = W//2-165, 82
    rect_r(screen, (px, py, 330, alto_panel), PANEL, 12, 1, BORDE)

    dtxt(screen, "Buscador:",    F['xs'], GRIS,       (W//2, py+20))
    dtxt(screen, r["buscador"],  F['md'], r["color_b"],(W//2, py+46))
    dtxt(screen, f"{r['encontrados']}/{r['total']} encontrados", F['lg'], BLANCO, (W//2, py+82))

    pygame.draw.line(screen, BORDE, (px+20, py+110), (px+310, py+110), 1)

    for i, h in enumerate(r["escondidos"]):
        hy = py + 120 + i*42
        pygame.draw.circle(screen, h["color"], (px+30, hy+12), 10)
        dtxt(screen, h["nombre"],                          F['sm'], BLANCO,             (px+50,  hy+12), "midleft")
        txt_e = "Atrapado" if h["encontrado"] else "Escapo"
        dtxt(screen, txt_e, F['sm'], VERDE if h["encontrado"] else ROJO, (px+310, hy+12), "midright")

    btn_y = py + alto_panel + 18
    boton(screen, (W//2-100, btn_y,    200, 44), "Jugar de nuevo [R]", F['sm'], VERDE)
    boton(screen, (W//2-100, btn_y+54, 200, 38), "Menu  [Esc]",        F['sm'], (50,50,70))

# ─────────────────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
DRAW = {
    "menu":        dibujar_menu,
    "configurar":  dibujar_configurar,
    "elegir_mapa": dibujar_elegir_mapa,
    "revelar":     dibujar_revelar,
    "esconderse":  dibujar_esconderse,
    "juego":       dibujar_juego,
    "resultados":  dibujar_resultados,
}

def main():
    corriendo = True
    while corriendo:
        ms = pygame.time.get_ticks()
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                corriendo = False
            manejar_evento(event)

        actualizar(dt, ms)
        DRAW.get(E["pantalla"], dibujar_menu)()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
