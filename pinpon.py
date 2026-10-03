from pygame import *
import random
import math
import json
import os
import array
from types import SimpleNamespace
'''Required classes'''

# ======================================================================
#                        CONFIGURACION GENERAL
# ======================================================================
ANCHO, ALTO = 600, 500
FPS_OBJETIVO = 60
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_DATOS = os.path.join(CARPETA, 'pong_datos.json')
VEL_MAX = 15.0          # velocidad maxima de la pelota (pixeles por frame)
ANGULO_MAX = 55         # angulo maximo de rebote en la raqueta (grados)

# niveles de la PC: velocidad (factor), frames entre decisiones, error en pixeles,
# zona muerta, si predice los rebotes y desde que x empieza a reaccionar
NIVELES_IA = [
    {'nombre': 'FACIL',   'vel': 0.55, 'reaccion': 18, 'error': 55, 'zona': 40, 'prediccion': False, 'x_min': 330},
    {'nombre': 'NORMAL',  'vel': 0.75, 'reaccion': 10, 'error': 30, 'zona': 25, 'prediccion': True,  'x_min': 200},
    {'nombre': 'DIFICIL', 'vel': 0.95, 'reaccion': 5,  'error': 14, 'zona': 12, 'prediccion': True,  'x_min': 0},
    {'nombre': 'EXPERTO', 'vel': 1.10, 'reaccion': 2,  'error': 5,  'zona': 6,  'prediccion': True,  'x_min': 0},
]
DIFICULTAD = [(n['nombre'], n['vel'], n['zona'], n['x_min']) for n in NIVELES_IA]

# ----------------------------------------------------------------------
#  Modos de juego (inspirados en Pong clasico, Breakout/Squash, Pong
#  con power-ups, Pong de hockey de aire y modos arcade de supervivencia)
# ----------------------------------------------------------------------
MODOS = {
    'CLASICO': {'desc': 'El Pong de toda la vida. Gana quien llegue primero a los puntos.',
                'powerups': False, 'acel': 0.03, 'pelotas': 1, 'pared': False, 'vidas': 0, 'record': True},
    'ACELERADO': {'desc': 'La pelota se acelera mucho con cada golpe. Reflejos al maximo.',
                  'powerups': False, 'acel': 0.10, 'pelotas': 1, 'pared': False, 'vidas': 0, 'record': True},
    'POWERUPS': {'desc': 'Aparecen bonus en la cancha: golpea la bola contra ellos para activarlos.',
                 'powerups': True, 'acel': 0.03, 'pelotas': 1, 'pared': False, 'vidas': 0, 'record': True},
    'DOBLE': {'desc': 'Dos pelotas a la vez. Cada una que se escapa es un punto para el rival.',
              'powerups': False, 'acel': 0.03, 'pelotas': 2, 'pared': False, 'vidas': 0, 'record': True},
    'CAOS': {'desc': 'Todo junto: dos pelotas, power-ups y aceleracion. Sobrevive al caos.',
             'powerups': True, 'acel': 0.06, 'pelotas': 2, 'pared': False, 'vidas': 0, 'record': True},
    'SUPERVIVENCIA': {'desc': 'Rebota contra la pared con 3 vidas. Cada 12 golpes entra otra pelota.',
                      'powerups': False, 'acel': 0.05, 'pelotas': 1, 'pared': True, 'vidas': 3, 'record': True},
    'PRACTICA': {'desc': 'Entrena contra la pared sin limite de vidas. Intenta batir tu mejor rally.',
                 'powerups': False, 'acel': 0.0, 'pelotas': 1, 'pared': True, 'vidas': 0, 'record': False},
}
ORDEN_MODOS = ['CLASICO', 'ACELERADO', 'POWERUPS', 'DOBLE', 'CAOS', 'SUPERVIVENCIA', 'PRACTICA']
MODOS_CON_RECORD = [m for m in ORDEN_MODOS if MODOS[m]['record']] + ['TORNEO']

# etapas del torneo: cada rival es mas dificil y cambia las reglas
ETAPAS_TORNEO = [
    {'rival': 'NOVATO',     'nivel': 0, 'modo': 'CLASICO',   'color': (120, 200, 120)},
    {'rival': 'AFICIONADO', 'nivel': 1, 'modo': 'POWERUPS',  'color': (100, 170, 255)},
    {'rival': 'EXPERTO',    'nivel': 2, 'modo': 'ACELERADO', 'color': (255, 170, 60)},
    {'rival': 'CAMPEON',    'nivel': 3, 'modo': 'CAOS',      'color': (255, 90, 90)},
]

# power-ups: color, letra, nombre y duracion en frames (60 frames = 1 segundo)
TIPOS_POWERUP = {
    'GRANDE':  {'color': (60, 140, 255),  'letra': 'G', 'nombre': 'RAQUETA GRANDE',  'dur': 600,
                'info': 'Tu raqueta crece 10 segundos'},
    'PEQUENA': {'color': (255, 80, 80),   'letra': 'P', 'nombre': 'RIVAL PEQUENO',   'dur': 600,
                'info': 'La raqueta rival se encoge'},
    'LENTO':   {'color': (60, 220, 220),  'letra': 'L', 'nombre': 'PELOTA LENTA',    'dur': 420,
                'info': 'Todas las pelotas van mas lento'},
    'RAPIDO':  {'color': (255, 160, 40),  'letra': 'R', 'nombre': 'PELOTA RAPIDA',   'dur': 420,
                'info': 'Todas las pelotas van mas rapido'},
    'MULTI':   {'color': (190, 90, 255),  'letra': 'M', 'nombre': 'MULTIPELOTA',     'dur': 0,
                'info': 'La pelota se divide en tres'},
    'ESCUDO':  {'color': (70, 210, 90),   'letra': 'E', 'nombre': 'ESCUDO',          'dur': 0,
                'info': 'Salva un punto en tu lado'},
    'CONGELA': {'color': (225, 235, 255), 'letra': 'C', 'nombre': 'RIVAL CONGELADO', 'dur': 100,
                'info': 'El rival no se mueve un instante'},
    'BONUS':   {'color': (255, 220, 40),  'letra': 'B', 'nombre': 'BONUS +300',      'dur': 0,
                'info': 'Suma 300 a tu puntuacion'},
}

# ----------------------------------------------------------------------
#  Temas de color
# ----------------------------------------------------------------------
TEMAS = {
    'CIELO': {'fondo': (200, 255, 255), 'fondo2': (150, 215, 240), 'linea': (255, 255, 255),
              'texto': (0, 0, 80), 'resalte': (255, 170, 0), 'panel': (20, 30, 60),
              'particula': (255, 150, 40), 'estela': (255, 255, 255),
              'j1': (60, 120, 255), 'j2': (255, 90, 90)},
    'NOCHE': {'fondo': (12, 14, 40), 'fondo2': (35, 20, 75), 'linea': (90, 100, 170),
              'texto': (230, 235, 255), 'resalte': (255, 220, 80), 'panel': (10, 10, 30),
              'particula': (120, 200, 255), 'estela': (140, 170, 255),
              'j1': (80, 160, 255), 'j2': (255, 100, 140)},
    'RETRO': {'fondo': (0, 0, 0), 'fondo2': (0, 28, 0), 'linea': (0, 140, 0),
              'texto': (80, 255, 80), 'resalte': (255, 255, 80), 'panel': (0, 20, 0),
              'particula': (80, 255, 80), 'estela': (0, 200, 0),
              'j1': (80, 255, 80), 'j2': (255, 255, 80)},
    'ATARDECER': {'fondo': (255, 190, 130), 'fondo2': (200, 90, 110), 'linea': (255, 235, 200),
                  'texto': (60, 10, 50), 'resalte': (255, 255, 160), 'panel': (60, 20, 70),
                  'particula': (255, 240, 120), 'estela': (255, 230, 180),
                  'j1': (255, 255, 255), 'j2': (90, 20, 90)},
}
ORDEN_TEMAS = list(TEMAS.keys())

AJUSTES_BASE = {
    'volumen': 6, 'tema': 'CIELO', 'particulas': True, 'sacudida': True, 'estela': True,
    'tinte': False, 'raton': False, 'puntos': 3, 'vel_pelota': 4, 'vel_raquetas': 5,
    'dificultad': 1, 'fps_visible': False, 'angulo': 0, 'angulo_listo': False, 'nombre': 'AAA',
}
STATS_BASE = {'partidas': 0, 'victorias': 0, 'derrotas': 0, 'golpes': 0, 'puntos': 0,
              'segundos': 0, 'mejor_rally': 0, 'racha': 0, 'mejor_racha': 0, 'torneos': 0}


# ======================================================================
#                        UTILIDADES GENERALES
# ======================================================================
def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def mezclar(a, b, t):
    return a + (b - a) * t


def mezclar_color(c1, c2, t):
    t = limitar(t, 0.0, 1.0)
    return (int(mezclar(c1[0], c2[0], t)), int(mezclar(c1[1], c2[1], t)), int(mezclar(c1[2], c2[2], t)))


def signo(valor):
    return (valor > 0) - (valor < 0)


def triangular(y, minimo, maximo):
    # refleja y entre dos paredes (como si la pelota rebotara en techo y suelo)
    tramo = maximo - minimo
    y = (y - minimo) % (2 * tramo)
    if y > tramo:
        y = 2 * tramo - y
    return y + minimo


def formato_tiempo(frames):
    segundos = int(frames // FPS_OBJETIVO)
    return '%d:%02d' % (segundos // 60, segundos % 60)


class Fuentes:
    cache = {}

    @classmethod
    def obtener(cls, tam):
        if tam not in cls.cache:
            cls.cache[tam] = font.Font(None, tam)
        return cls.cache[tam]


def dibujar_texto(surf, cadena, tam, color, x, y, alinear='centro', sombra=True):
    fuente = Fuentes.obtener(tam)
    img = fuente.render(str(cadena), True, color)
    caja = img.get_rect()
    if alinear == 'centro':
        caja.center = (x, y)
    elif alinear == 'izq':
        caja.midleft = (x, y)
    else:
        caja.midright = (x, y)
    if sombra:
        oscuro = fuente.render(str(cadena), True, (0, 0, 0))
        oscuro.set_alpha(90)
        surf.blit(oscuro, (caja.x + 2, caja.y + 2))
    surf.blit(img, caja)
    return caja


def panel_translucido(surf, rect, color, alpha=170, borde=None):
    rect = Rect(rect)
    capa = Surface((rect.width, rect.height), SRCALPHA)
    capa.fill((color[0], color[1], color[2], alpha))
    if borde is not None:
        draw.rect(capa, borde, capa.get_rect(), 2)
    surf.blit(capa, (rect.x, rect.y))


# vuelve transparente el fondo de una imagen (usa el color del pixel de la esquina como fondo)
def quitar_fondo(surf, tolerancia=40):
    fondo = surf.get_at((0, 0))
    if fondo.a == 0:       # la imagen ya tiene transparencia real
        return
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            c = surf.get_at((x, y))
            if abs(c.r - fondo.r) <= tolerancia and abs(c.g - fondo.g) <= tolerancia and abs(c.b - fondo.b) <= tolerancia:
                surf.set_at((x, y), (c.r, c.g, c.b, 0))


def ruta_archivo(archivo):
    if os.path.exists(archivo):
        return archivo
    return os.path.join(CARPETA, archivo)


# si falta la imagen, dibuja una de reemplazo para que el juego no se caiga
CACHE_IMG = {}


def cargar_imagen_segura(archivo, ancho, alto, tipo='raqueta'):
    clave = (archivo, ancho, alto)
    if clave in CACHE_IMG:
        return CACHE_IMG[clave]
    try:
        img = transform.scale(image.load(ruta_archivo(archivo)).convert_alpha(), (ancho, alto))
    except Exception:
        img = Surface((ancho, alto), SRCALPHA)
        if tipo == 'pelota':
            draw.ellipse(img, (250, 250, 250), img.get_rect())
            draw.ellipse(img, (220, 70, 70), img.get_rect(), 4)
        else:
            draw.ellipse(img, (235, 235, 235), img.get_rect())
            draw.ellipse(img, (90, 90, 90), img.get_rect(), 3)
    CACHE_IMG[clave] = img
    return img


# carga la imagen de la raqueta una sola vez (tamano moderado) y le quita el fondo
def cargar_base(archivo):
    try:
        img = image.load(ruta_archivo(archivo)).convert_alpha()
    except Exception:
        img = cargar_imagen_segura(archivo, 50, 150, 'raqueta').copy()
    w, h = img.get_size()
    f = min(1, 300 / max(w, h))
    img = transform.scale(img, (max(1, int(w * f)), max(1, int(h * f))))
    quitar_fondo(img)
    return img


# gira la imagen, recorta los bordes vacios y la deja de 50x150
def hacer_imagen_raqueta(base, angulo):
    rot = transform.rotate(base, angulo)
    recorte = rot.get_bounding_rect()
    if recorte.width == 0 or recorte.height == 0:
        recorte = rot.get_rect()
    rot = rot.subsurface(recorte).copy()
    return transform.scale(rot, (50, 150))


# calcula cuanto hay que girar la imagen para que su eje largo quede vertical
def angulo_auto(surf):
    pts = [(x, y) for x in range(surf.get_width()) for y in range(surf.get_height()) if surf.get_at((x, y)).a > 0]
    if len(pts) < 10:
        return 0
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - cx) ** 2 for p in pts)
    syy = sum((p[1] - cy) ** 2 for p in pts)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    theta = math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy))
    return int(round(((90 + theta + 90) % 180) - 90))


# ======================================================================
#                  DATOS GUARDADOS (ajustes, records, estadisticas)
# ======================================================================
class Datos:
    def __init__(self, archivo=ARCHIVO_DATOS):
        self.archivo = archivo
        self.ajustes = dict(AJUSTES_BASE)
        self.records = {}
        self.stats = dict(STATS_BASE)
        self.cargar()

    def cargar(self):
        try:
            with open(self.archivo, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(d, dict):
            return
        for nombre, valor in d.get('ajustes', {}).items():
            if nombre in AJUSTES_BASE and type(valor) is type(AJUSTES_BASE[nombre]):
                self.ajustes[nombre] = valor
        for nombre, valor in d.get('stats', {}).items():
            if nombre in STATS_BASE and isinstance(valor, (int, float)):
                self.stats[nombre] = valor
        recs = d.get('records', {})
        if isinstance(recs, dict):
            for modo, lista in recs.items():
                if isinstance(lista, list):
                    validos = [r for r in lista if isinstance(r, dict) and 'puntos' in r and 'nombre' in r]
                    self.records[modo] = validos[:5]
        self.validar()

    def validar(self):
        a = self.ajustes
        if a['tema'] not in TEMAS:
            a['tema'] = 'CIELO'
        a['volumen'] = limitar(a['volumen'], 0, 10)
        a['puntos'] = limitar(a['puntos'], 1, 10)
        a['vel_pelota'] = limitar(a['vel_pelota'], 1, 10)
        a['vel_raquetas'] = limitar(a['vel_raquetas'], 2, 12)
        a['dificultad'] = limitar(a['dificultad'], 0, len(NIVELES_IA) - 1)
        a['angulo'] = limitar(a['angulo'], -180, 180)
        a['nombre'] = (a['nombre'].upper() + 'AAA')[:3]

    def guardar(self):
        try:
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump({'ajustes': self.ajustes, 'records': self.records, 'stats': self.stats}, f, indent=2)
        except OSError:
            pass

    def lista_records(self, modo):
        return self.records.get(modo, [])

    def es_record(self, modo, puntos):
        lista = self.lista_records(modo)
        return puntos > 0 and (len(lista) < 5 or puntos > lista[-1]['puntos'])

    def agregar_record(self, modo, nombre, puntos):
        lista = self.records.setdefault(modo, [])
        lista.append({'nombre': nombre, 'puntos': int(puntos)})
        lista.sort(key=lambda r: r['puntos'], reverse=True)
        del lista[5:]
        self.guardar()

    def borrar_records(self):
        self.records = {}
        self.guardar()


# ======================================================================
#                SONIDOS (se generan por codigo, no hacen falta archivos)
# ======================================================================
class Sonidos:
    def __init__(self, ajustes):
        self.ajustes = ajustes
        self.activo = False
        self.efectos = {}
        try:
            if mixer.get_init() is None:
                mixer.init(22050, -16, 1, 512)
            info = mixer.get_init()
            if info is None or info[1] != -16:
                return
            self.frecuencia = info[0]
            self.canales = info[2]
            self.activo = True
            self._crear_todos()
        except Exception:
            self.activo = False

    def _onda(self, freq, dur, forma, vol, freq_fin):
        n = max(1, int(self.frecuencia * dur))
        datos = array.array('h')
        fase = 0.0
        for i in range(n):
            f = freq if freq_fin is None else freq + (freq_fin - freq) * i / n
            fase += 2 * math.pi * f / self.frecuencia
            if forma == 'seno':
                v = math.sin(fase)
            elif forma == 'cuadrada':
                v = 1.0 if math.sin(fase) >= 0 else -1.0
            elif forma == 'sierra':
                v = ((fase / (2 * math.pi)) % 1.0) * 2 - 1
            else:
                v = random.uniform(-1, 1)
            envolvente = min(1.0, i / 80.0) * (1.0 - i / n)
            muestra = int(v * envolvente * vol * 32767)
            for _ in range(self.canales):
                datos.append(muestra)
        return datos

    def _sonido(self, notas, forma='cuadrada', vol=0.25):
        total = array.array('h')
        for nota in notas:
            fin = nota[2] if len(nota) > 2 else None
            total.extend(self._onda(nota[0], nota[1], forma, vol, fin))
        return mixer.Sound(buffer=total.tobytes())

    def _crear_todos(self):
        e = self.efectos
        e['golpe'] = self._sonido([(520, 0.05), (390, 0.05)])
        e['pared'] = self._sonido([(260, 0.06)], 'cuadrada', 0.2)
        e['punto'] = self._sonido([(440, 0.08), (330, 0.08), (220, 0.16)], 'seno', 0.35)
        e['ganar'] = self._sonido([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.28)], 'seno', 0.35)
        e['perder'] = self._sonido([(392, 0.14), (330, 0.14), (262, 0.14), (196, 0.3)], 'sierra', 0.25)
        e['powerup'] = self._sonido([(500, 0.12, 1200)], 'seno', 0.35)
        e['menu'] = self._sonido([(700, 0.03)], 'cuadrada', 0.15)
        e['aceptar'] = self._sonido([(500, 0.04), (800, 0.06)], 'cuadrada', 0.2)
        e['cuenta'] = self._sonido([(440, 0.1)], 'seno', 0.3)
        e['ya'] = self._sonido([(880, 0.22)], 'seno', 0.35)
        e['escudo'] = self._sonido([(300, 0.12, 80)], 'ruido', 0.3)
        e['congela'] = self._sonido([(1400, 0.2, 300)], 'seno', 0.25)

    def reproducir(self, nombre):
        if not self.activo or nombre not in self.efectos:
            return
        volumen = self.ajustes['volumen'] / 10.0
        if volumen <= 0:
            return
        sonido = self.efectos[nombre]
        sonido.set_volume(volumen)
        sonido.play()


# ======================================================================
#                 EFECTOS VISUALES (particulas, textos, sacudida)
# ======================================================================
class Particula:
    __slots__ = ('x', 'y', 'vx', 'vy', 'vida', 'vida_max', 'color', 'tam', 'grav')

    def __init__(self, x, y, vx, vy, vida, color, tam, grav):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.vida = vida
        self.vida_max = vida
        self.color = color
        self.tam = tam
        self.grav = grav


class SistemaParticulas:
    def __init__(self, maximo=400):
        self.lista = []
        self.maximo = maximo

    def emitir(self, x, y, cantidad, color, vel=3.0, vida=30, tam=4, grav=0.0, angulo=None, apertura=360):
        for _ in range(cantidad):
            if len(self.lista) >= self.maximo:
                break
            if angulo is None:
                a = random.uniform(0, 2 * math.pi)
            else:
                a = math.radians(angulo + random.uniform(-apertura / 2.0, apertura / 2.0))
            v = vel * random.uniform(0.3, 1.0)
            self.lista.append(Particula(x, y, math.cos(a) * v, math.sin(a) * v,
                                        vida * random.uniform(0.6, 1.0), color,
                                        tam * random.uniform(0.6, 1.2), grav))

    def actualizar(self):
        vivas = []
        for p in self.lista:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.grav
            p.vx *= 0.98
            p.vida -= 1
            if p.vida > 0:
                vivas.append(p)
        self.lista = vivas

    def dibujar(self, surf):
        for p in self.lista:
            t = p.vida / p.vida_max
            radio = max(1, int(p.tam * t))
            draw.circle(surf, p.color, (int(p.x), int(p.y)), radio)


class TextosFlotantes:
    def __init__(self):
        self.lista = []

    def agregar(self, cadena, x, y, color, tam=28, vida=60):
        self.lista.append({'t': cadena, 'x': x, 'y': y, 'color': color, 'tam': tam, 'vida': vida, 'max': vida})

    def actualizar(self):
        for t in self.lista:
            t['y'] -= 0.8
            t['vida'] -= 1
        self.lista = [t for t in self.lista if t['vida'] > 0]

    def dibujar(self, surf):
        for t in self.lista:
            img = Fuentes.obtener(t['tam']).render(t['t'], True, t['color'])
            img.set_alpha(int(255 * min(1.0, t['vida'] / (t['max'] * 0.5))))
            surf.blit(img, img.get_rect(center=(int(t['x']), int(t['y']))))


class Sacudida:
    def __init__(self):
        self.magnitud = 0.0

    def disparar(self, fuerza):
        self.magnitud = max(self.magnitud, fuerza)

    def actualizar(self):
        self.magnitud *= 0.85
        if self.magnitud < 0.3:
            self.magnitud = 0.0

    def desplazamiento(self):
        if self.magnitud <= 0:
            return (0, 0)
        return (int(random.uniform(-1, 1) * self.magnitud), int(random.uniform(-1, 1) * self.magnitud))


# ======================================================================
#                              FONDO
# ======================================================================
class Fondo:
    def __init__(self, tema):
        self.fase = 0
        self.estrellas = [[random.uniform(0, ANCHO), random.uniform(0, ALTO),
                           random.uniform(0.1, 0.6), random.randint(1, 3)] for _ in range(50)]
        self.tema = TEMAS[tema]
        self.superficie = None
        self.cambiar_tema(tema)

    def cambiar_tema(self, nombre):
        self.tema = TEMAS[nombre]
        self.superficie = Surface((ANCHO, ALTO))
        for y in range(ALTO):
            color = mezclar_color(self.tema['fondo'], self.tema['fondo2'], y / float(ALTO))
            draw.line(self.superficie, color, (0, y), (ANCHO, y))

    def actualizar(self):
        self.fase += 1
        for e in self.estrellas:
            e[0] -= e[2]
            if e[0] < 0:
                e[0] = ANCHO
                e[1] = random.uniform(0, ALTO)

    def dibujar(self, surf, linea_central=True):
        surf.blit(self.superficie, (0, 0))
        color_estrella = mezclar_color(self.tema['fondo2'], self.tema['linea'], 0.6)
        for e in self.estrellas:
            draw.circle(surf, color_estrella, (int(e[0]), int(e[1])), e[3])
        if linea_central:
            desfase = (self.fase // 2) % 30
            for y in range(-30 + desfase, ALTO, 30):
                draw.rect(surf, self.tema['linea'], (ANCHO // 2 - 3, y, 6, 16))


# ======================================================================
#              INTELIGENCIA ARTIFICIAL (la PC que juega contigo)
# ======================================================================
def predecir_y(bola, x_objetivo):
    # calcula en que altura estara la pelota cuando llegue a x_objetivo (con rebotes)
    if bola.vx == 0:
        return bola.fy
    t = (x_objetivo - bola.fx) / bola.vx
    if t < 0:
        return bola.fy
    return triangular(bola.fy + bola.vy * t, 25, ALTO - 25)


class IA:
    def __init__(self, nivel):
        self.nivel = 0
        self.perfil = NIVELES_IA[0]
        self.cuenta = 0
        self.objetivo = ALTO / 2.0
        self.cambiar_nivel(nivel)

    def cambiar_nivel(self, nivel):
        self.nivel = int(limitar(nivel, 0, len(NIVELES_IA) - 1))
        self.perfil = NIVELES_IA[self.nivel]

    def _elegir_objetivo(self, raqueta, bolas, lado):
        p = self.perfil
        x_obj = raqueta.rect.left if lado == 'der' else raqueta.rect.right
        amenaza = None
        mejor = 1e9
        for b in bolas:
            viene = b.vx > 0 if lado == 'der' else b.vx < 0
            if not viene:
                continue
            distancia = abs(x_obj - b.fx)
            if distancia < mejor:
                mejor = distancia
                amenaza = b
        if amenaza is None:
            return ALTO / 2.0
        if lado == 'der' and amenaza.fx < p['x_min']:
            return ALTO / 2.0
        if lado == 'izq' and amenaza.fx > ANCHO - p['x_min']:
            return ALTO / 2.0
        y = predecir_y(amenaza, x_obj) if p['prediccion'] else amenaza.fy
        return y + random.uniform(-1, 1) * p['error']

    def decidir(self, raqueta, bolas, lado):
        # devuelve cuantos pixeles debe moverse la raqueta en este frame
        self.cuenta -= 1
        if self.cuenta <= 0:
            self.cuenta = self.perfil['reaccion']
            self.objetivo = self._elegir_objetivo(raqueta, bolas, lado)
        centro = raqueta.rect.centery
        zona = self.perfil['zona']
        paso = max(1.0, raqueta.speed * self.perfil['vel'])
        if self.objetivo < centro - zona:
            return -paso
        if self.objetivo > centro + zona:
            return paso
        return 0.0


class DemoFondo:
    """Partida automatica (PC contra PC) que se ve de fondo en los menus."""

    def __init__(self):
        self.r1 = SimpleNamespace(rect=Rect(30, 175, 50, 150), speed=4.5, fy=175.0)
        self.r2 = SimpleNamespace(rect=Rect(520, 175, 50, 150), speed=4.5, fy=175.0)
        self.ia1 = IA(1)
        self.ia2 = IA(1)
        self.bola = SimpleNamespace(fx=300.0, fy=250.0, vx=0.0, vy=0.0)
        self.estela = []
        self.sacar(random.choice([-1, 1]))

    def sacar(self, direccion):
        b = self.bola
        b.fx, b.fy = ANCHO / 2.0, ALTO / 2.0
        angulo = math.radians(random.uniform(-30, 30))
        b.vx = direccion * 5.0 * math.cos(angulo)
        b.vy = 5.0 * math.sin(angulo)
        self.estela = []

    def _mover(self, r, dy):
        r.fy = limitar(r.fy + dy, 5, ALTO - 155)
        r.rect.y = int(r.fy)

    def actualizar(self):
        b = self.bola
        b.fx += b.vx
        b.fy += b.vy
        if b.fy < 14:
            b.fy = 14
            b.vy = abs(b.vy)
        if b.fy > ALTO - 14:
            b.fy = ALTO - 14
            b.vy = -abs(b.vy)
        self._mover(self.r1, self.ia1.decidir(self.r1, [b], 'izq'))
        self._mover(self.r2, self.ia2.decidir(self.r2, [b], 'der'))
        for r, d in ((self.r1, 1), (self.r2, -1)):
            if b.vx * d < 0 and r.rect.left - 14 < b.fx < r.rect.right + 14 and abs(b.fy - r.rect.centery) < 85:
                b.vx = abs(b.vx) * d * 1.02
                b.vy += (b.fy - r.rect.centery) * 0.04
        if b.fx < -20:
            self.sacar(-1)
        elif b.fx > ANCHO + 20:
            self.sacar(1)
        self.estela.append((b.fx, b.fy))
        self.estela = self.estela[-12:]

    def dibujar(self, surf, tema):
        for i, (ex, ey) in enumerate(self.estela):
            t = (i + 1) / float(len(self.estela))
            draw.circle(surf, mezclar_color(tema['fondo2'], tema['estela'], t * 0.7), (int(ex), int(ey)), int(4 + 8 * t))
        draw.rect(surf, tema['j1'], self.r1.rect)
        draw.rect(surf, tema['j2'], self.r2.rect)
        draw.circle(surf, tema['texto'], (int(self.bola.fx), int(self.bola.fy)), 12)


# ======================================================================
#                          CLASES DE OBJETOS
# ======================================================================
#clase padre para los objetos
class GameSprite(sprite.Sprite):
   def __init__(self, player_image, player_x, player_y, player_speed, wight, height, transparent=False):
       super().__init__()
       if isinstance(player_image, Surface):
           self.image = transform.scale(player_image, (wight, height))
       else:
           tipo = 'pelota' if 'pelota' in player_image else 'raqueta'
           self.image = cargar_imagen_segura(player_image, wight, height, tipo) #por ejemplo. 55,55 - parámetros
       if transparent:
           self.image = self.image.copy()
           quitar_fondo(self.image)
       self.speed = player_speed
       self.rect = self.image.get_rect()
       self.rect.x = player_x
       self.rect.y = player_y


   def reset(self, superficie=None):
       destino = superficie if superficie is not None else window
       destino.blit(self.image, (self.rect.x, self.rect.y))


class Player(GameSprite):
    def update_l(self):
        keys= key.get_pressed()
        if keys[K_w] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < ALTO - self.rect.height - 5:
            self.rect.y += self.speed
    def update_right(self):
        keys= key.get_pressed()
        if keys[K_UP] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_DOWN] and self.rect.y < ALTO - self.rect.height - 5:
            self.rect.y += self.speed


class Raqueta(Player):
    """Raqueta con movimiento suave, cambio de tamano, congelamiento y escudo."""

    def __init__(self, imagen, x, y, velocidad, lado, ancho=50, alto=150):
        super().__init__(imagen, x, y, velocidad, ancho, alto)
        self.lado = lado
        self.imagen_base = imagen
        self.alto_base = alto
        self.alto_objetivo = alto
        self.fy = float(y)
        self.vy = 0.0
        self.congelada = 0
        self.destello = 0
        self.escudo = False

    def mover(self, dy):
        antes = self.fy
        if self.congelada > 0:
            dy = 0.0
        self.fy = limitar(self.fy + dy, 5, ALTO - self.rect.height - 5)
        self.rect.y = int(self.fy)
        self.vy = self.fy - antes

    def mover_control(self, arriba, abajo):
        dy = 0.0
        if arriba:
            dy -= self.speed
        if abajo:
            dy += self.speed
        self.mover(dy)

    def seguir_raton(self, y_objetivo):
        paso = self.speed * 2.2
        self.mover(limitar(y_objetivo - self.rect.centery, -paso, paso))

    def cambiar_alto(self, alto):
        alto = int(limitar(alto, 40, 300))
        centro = self.rect.centery
        self.rect.height = alto
        self.image = transform.scale(self.imagen_base, (self.rect.width, alto))
        self.rect.centery = centro
        self.fy = float(limitar(self.rect.y, 5, ALTO - alto - 5))
        self.rect.y = int(self.fy)

    def cambiar_imagen(self, imagen):
        self.imagen_base = imagen
        self.image = transform.scale(imagen, (self.rect.width, self.rect.height))

    def actualizar_estado(self):
        if self.congelada > 0:
            self.congelada -= 1
        if self.destello > 0:
            self.destello -= 1
        if abs(self.rect.height - self.alto_objetivo) >= 1:
            nuevo = int(round(mezclar(self.rect.height, self.alto_objetivo, 0.12)))
            if nuevo == self.rect.height:
                nuevo += 1 if self.alto_objetivo > nuevo else -1
            self.cambiar_alto(nuevo)

    def dibujar(self, surf, tema):
        if self.escudo:
            x = 6 if self.lado == 'izq' else ANCHO - 6
            draw.line(surf, TIPOS_POWERUP['ESCUDO']['color'], (x, 0), (x, ALTO), 4)
        surf.blit(self.image, (self.rect.x, self.rect.y))
        if self.congelada > 0:
            panel_translucido(surf, self.rect, TIPOS_POWERUP['CONGELA']['color'], 110)
        if self.destello > 0:
            draw.rect(surf, tema['resalte'], self.rect, 3)


class Pelota(GameSprite):
    """Pelota con fisica propia: velocidad, giro (efecto), estela y rotacion."""

    def __init__(self, x, y, tam=50):
        super().__init__('pelota.png', int(x), int(y), 0, tam, tam)
        self.tam = tam
        self.fx = float(x)
        self.fy = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.giro = 0.0
        self.escala = 1.0
        self.ultimo = 0          # 0 nadie, 1 jugador izquierdo, 2 jugador derecho
        self.estela = []
        self.angulo_vis = 0.0
        self.caja = Rect(0, 0, tam - 14, tam - 14)
        self.sincronizar()

    def sincronizar(self):
        self.rect.center = (int(self.fx), int(self.fy))
        self.caja.center = (int(self.fx), int(self.fy))

    @property
    def velocidad(self):
        return math.hypot(self.vx, self.vy)

    def fijar_velocidad(self, v):
        actual = self.velocidad
        if actual == 0:
            self.vx = v
            return
        k = v / actual
        self.vx *= k
        self.vy *= k

    def corregir_angulo(self, minimo=0.4):
        # evita que la pelota quede casi vertical (muy aburrido)
        v = self.velocidad
        if v == 0:
            return
        if abs(self.vx) < minimo * v:
            horizontal = (signo(self.vx) or 1) * minimo * v
            vertical = math.sqrt(max(0.0, v * v - horizontal * horizontal))
            self.vx = horizontal
            self.vy = (signo(self.vy) or 1) * vertical

    def lanzar(self, direccion, velocidad, apertura=28):
        angulo = math.radians(random.uniform(-apertura, apertura))
        self.vx = direccion * velocidad * math.cos(angulo)
        self.vy = velocidad * math.sin(angulo)
        self.giro = 0.0

    def actualizar(self):
        self.estela.append((self.fx, self.fy))
        self.estela = self.estela[-10:]
        self.vy += self.giro * 0.05
        self.giro *= 0.985
        self.fx += self.vx * self.escala
        self.fy += self.vy * self.escala
        self.angulo_vis = (self.angulo_vis - self.vx * 3 - self.giro * 4) % 360

    def dibujar(self, surf, tema, con_estela=True):
        if con_estela:
            n = len(self.estela)
            for i, (ex, ey) in enumerate(self.estela):
                t = (i + 1) / float(n)
                color = mezclar_color(tema['fondo2'], tema['estela'], t * 0.75)
                draw.circle(surf, color, (int(ex), int(ey)), max(2, int(self.tam * 0.38 * t)))
        girada = transform.rotate(self.image, self.angulo_vis)
        surf.blit(girada, girada.get_rect(center=(int(self.fx), int(self.fy))))


class PowerUp:
    def __init__(self, tipo, x, y):
        self.tipo = tipo
        self.x = x
        self.y = y
        self.vida = 900
        self.fase = random.uniform(0, 6.28)
        self.radio = 18
        self.rect = Rect(int(x - 18), int(y - 18), 36, 36)

    def actualizar(self):
        self.vida -= 1
        self.fase += 0.1
        self.rect.center = (int(self.x), int(self.y + math.sin(self.fase) * 4))

    def dibujar(self, surf, tema):
        if self.vida < 180 and (self.vida // 8) % 2 == 0:
            return
        dibujar_icono_powerup(surf, self.tipo, self.rect.centerx, self.rect.centery, self.radio, tema)


def dibujar_icono_powerup(surf, tipo, x, y, radio, tema):
    info = TIPOS_POWERUP[tipo]
    draw.circle(surf, info['color'], (x, y), radio)
    draw.circle(surf, tema['texto'], (x, y), radio, 2)
    dibujar_texto(surf, info['letra'], int(radio * 1.4), (255, 255, 255), x, y, sombra=True)


# ======================================================================
#                       INTERFAZ: MENUS Y PANELES
# ======================================================================
def partir_lineas(cadena, tam, ancho_max):
    fuente = Fuentes.obtener(tam)
    lineas = []
    actual = ''
    for palabra in cadena.split():
        prueba = (actual + ' ' + palabra).strip()
        if fuente.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


class ItemMenu:
    def __init__(self, texto, accion=None, obtener=None, cambiar=None, activo=None, separador=False):
        self.texto = texto
        self.accion = accion
        self.obtener = obtener
        self.cambiar = cambiar
        self.activo = activo
        self.separador = separador

    @property
    def etiqueta(self):
        return self.texto() if callable(self.texto) else self.texto

    def habilitado(self):
        return self.activo() if self.activo else True

    def seleccionable(self):
        return (not self.separador) and self.habilitado()


class MenuLista:
    """Lista vertical de opciones: acciones, valores que cambian con izq/der y scroll."""

    def __init__(self, app, items, x, y, ancho=380, alto_item=34, visibles=9, tam=30):
        self.app = app
        self.items = items
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto_item = alto_item
        self.visibles = visibles
        self.tam = tam
        self.indice = 0
        self.inicio = 0
        for i, it in enumerate(items):
            if it.seleccionable():
                self.indice = i
                break

    def mover(self, d):
        n = len(self.items)
        i = self.indice
        for _ in range(n):
            i = (i + d) % n
            if self.items[i].seleccionable():
                break
        if i != self.indice:
            self.indice = i
            self.app.sonidos.reproducir('menu')
        self.ajustar_scroll()

    def ajustar_scroll(self):
        if self.indice < self.inicio:
            self.inicio = self.indice
        elif self.indice >= self.inicio + self.visibles:
            self.inicio = self.indice - self.visibles + 1

    def activar(self, delta=0):
        it = self.items[self.indice]
        if not it.seleccionable():
            return
        if delta != 0:
            if it.cambiar:
                it.cambiar(delta)
                self.app.sonidos.reproducir('menu')
        elif it.accion:
            self.app.sonidos.reproducir('aceptar')
            it.accion()
        elif it.cambiar:
            it.cambiar(1)
            self.app.sonidos.reproducir('menu')

    def _item_en(self, pos):
        fin = min(len(self.items), self.inicio + self.visibles)
        for i in range(self.inicio, fin):
            cy = self.y + (i - self.inicio) * self.alto_item
            caja = Rect(self.x - self.ancho // 2, cy - self.alto_item // 2, self.ancho, self.alto_item)
            if caja.collidepoint(pos) and self.items[i].seleccionable():
                return i
        return None

    def evento(self, ev):
        if ev.type == KEYDOWN:
            if ev.key in (K_UP, K_w):
                self.mover(-1)
            elif ev.key in (K_DOWN, K_s):
                self.mover(1)
            elif ev.key in (K_LEFT, K_a):
                self.activar(-1)
            elif ev.key in (K_RIGHT, K_d):
                self.activar(1)
            elif ev.key in (K_RETURN, K_SPACE, K_KP_ENTER):
                self.activar(0)
        elif ev.type == MOUSEMOTION:
            i = self._item_en(ev.pos)
            if i is not None and i != self.indice:
                self.indice = i
        elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
            i = self._item_en(ev.pos)
            if i is not None:
                self.indice = i
                it = self.items[i]
                if it.cambiar and not it.accion:
                    self.activar(1 if ev.pos[0] >= self.x else -1)
                else:
                    self.activar(0)

    def dibujar(self, surf, tema):
        fin = min(len(self.items), self.inicio + self.visibles)
        for i in range(self.inicio, fin):
            it = self.items[i]
            cy = self.y + (i - self.inicio) * self.alto_item
            if it.separador:
                dibujar_texto(surf, it.etiqueta, int(self.tam * 0.7), tema['resalte'], self.x, cy)
                continue
            caja = Rect(self.x - self.ancho // 2, cy - self.alto_item // 2 + 2, self.ancho, self.alto_item - 4)
            color = tema['texto']
            if not it.habilitado():
                color = mezclar_color(tema['texto'], tema['fondo'], 0.65)
            if i == self.indice:
                panel_translucido(surf, caja, mezclar_color(tema['fondo'], tema['resalte'], 0.4), 210, tema['resalte'])
                dibujar_texto(surf, '>', self.tam, tema['resalte'], caja.x - 16, cy, sombra=False)
            dibujar_texto(surf, it.etiqueta, self.tam, color, caja.x + 14, cy, 'izq', sombra=False)
            if it.obtener:
                valor = str(it.obtener())
                if it.cambiar and i == self.indice and it.habilitado():
                    valor = '< ' + valor + ' >'
                dibujar_texto(surf, valor, self.tam, color, caja.right - 14, cy, 'der', sombra=False)
        if self.inicio > 0:
            draw.polygon(surf, tema['resalte'], [(self.x, self.y - self.alto_item + 2),
                                                 (self.x - 8, self.y - self.alto_item + 14),
                                                 (self.x + 8, self.y - self.alto_item + 14)])
        if fin < len(self.items):
            base = self.y + (self.visibles - 1) * self.alto_item + self.alto_item // 2 + 6
            draw.polygon(surf, tema['resalte'], [(self.x, base + 12), (self.x - 8, base), (self.x + 8, base)])


class CentroComandos:
    """Panel de comandos dentro de la partida (se abre con TAB).

    Cada comando es un diccionario con: nombre, valor (funcion), cambiar (funcion con -1/+1)
    y ejecutar (funcion). Flechas arriba/abajo eligen, izquierda/derecha cambian el valor
    y ENTER ejecuta.
    """

    def __init__(self, comandos):
        self.comandos = comandos
        self.visible = False
        self.indice = 0
        self.inicio = 0
        self.visibles = 11
        self.log = ['Centro de comandos listo']
        self.panel = Surface((380, 420), SRCALPHA)

    def decir(self, mensaje):
        self.log.append(mensaje)
        self.log = self.log[-5:]

    def alternar(self):
        self.visible = not self.visible
        self.decir('Panel abierto' if self.visible else 'Panel cerrado')

    def mover(self, d):
        self.indice = (self.indice + d) % len(self.comandos)
        if self.indice < self.inicio:
            self.inicio = self.indice
        elif self.indice >= self.inicio + self.visibles:
            self.inicio = self.indice - self.visibles + 1

    def manejar(self, ev):
        if ev.type != KEYDOWN:
            return
        cmd = self.comandos[self.indice]
        if ev.key == K_UP:
            self.mover(-1)
        elif ev.key == K_DOWN:
            self.mover(1)
        elif ev.key == K_LEFT and cmd.get('cambiar'):
            cmd['cambiar'](-1)
        elif ev.key == K_RIGHT and cmd.get('cambiar'):
            cmd['cambiar'](1)
        elif ev.key in (K_RETURN, K_SPACE, K_KP_ENTER):
            if cmd.get('ejecutar'):
                cmd['ejecutar']()
            elif cmd.get('cambiar'):
                cmd['cambiar'](1)
        elif ev.key == K_ESCAPE:
            self.alternar()

    def dibujar(self, surf):
        if not self.visible:
            return
        self.panel.fill((20, 30, 60, 225))
        draw.rect(self.panel, (120, 200, 255), self.panel.get_rect(), 3)
        titulo = Fuentes.obtener(32).render('CENTRO DE COMANDOS', True, (255, 255, 255))
        self.panel.blit(titulo, (50, 12))
        fin = min(len(self.comandos), self.inicio + self.visibles)
        for i in range(self.inicio, fin):
            cmd = self.comandos[i]
            fila = i - self.inicio
            elegido = (i == self.indice)
            color = (255, 220, 80) if elegido else (200, 220, 255)
            if elegido:
                draw.rect(self.panel, (60, 90, 150), (10, 50 + fila * 25, 360, 24))
            self.panel.blit(Fuentes.obtener(26).render(cmd['nombre'], True, color), (20, 53 + fila * 25))
            if cmd.get('valor'):
                valor = '< ' + str(cmd['valor']()) + ' >'
                self.panel.blit(Fuentes.obtener(26).render(valor, True, color), (235, 53 + fila * 25))
        if self.inicio > 0:
            self.panel.blit(Fuentes.obtener(20).render('^', True, (255, 220, 80)), (360, 36))
        if fin < len(self.comandos):
            self.panel.blit(Fuentes.obtener(20).render('v', True, (255, 220, 80)), (360, 326))
        draw.line(self.panel, (120, 200, 255), (10, 336), (370, 336), 1)
        for n, linea in enumerate(self.log):
            self.panel.blit(Fuentes.obtener(20).render('> ' + linea, True, (150, 255, 150)), (15, 342 + n * 14))
        surf.blit(self.panel, (110, 40))


# ======================================================================
#                              ESCENAS
# ======================================================================
class Escena:
    def __init__(self, app):
        self.app = app

    def entrar(self, **datos):
        pass

    def evento(self, ev):
        pass

    def actualizar(self):
        pass

    def dibujar(self, surf):
        pass

    def actualizar_fondo(self):
        self.app.fondo.actualizar()
        self.app.demo.actualizar()

    def fondo_menu(self, surf, atenuar=True):
        self.app.fondo.dibujar(surf, linea_central=False)
        self.app.demo.dibujar(surf, self.app.tema)
        if atenuar:
            panel_translucido(surf, Rect(0, 0, ANCHO, ALTO), self.app.tema['fondo'], 135)

    def titulo(self, surf, cadena, subtitulo=None):
        dibujar_texto(surf, cadena, 54, self.app.tema['texto'], ANCHO // 2, 42)
        if subtitulo:
            dibujar_texto(surf, subtitulo, 24, self.app.tema['resalte'], ANCHO // 2, 80)


class EscenaTitulo(Escena):
    def entrar(self, **datos):
        self.t = 0

    def evento(self, ev):
        if ev.type == KEYDOWN:
            if ev.key == K_ESCAPE:
                self.app.salir()
            else:
                self.app.sonidos.reproducir('aceptar')
                self.app.ir_a('menu')
        elif ev.type == MOUSEBUTTONDOWN:
            self.app.sonidos.reproducir('aceptar')
            self.app.ir_a('menu')

    def actualizar(self):
        self.t += 1
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        self.fondo_menu(surf, atenuar=False)
        cadena = 'PING PONG'
        letras = [Fuentes.obtener(96).render(c, True, mezclar_color(tema['texto'], tema['resalte'], i / 8.0))
                  for i, c in enumerate(cadena)]
        total = sum(l.get_width() for l in letras)
        x = (ANCHO - total) // 2
        for i, l in enumerate(letras):
            y = 150 + math.sin(self.t * 0.08 + i * 0.6) * 10
            sombra = Fuentes.obtener(96).render(cadena[i], True, (0, 0, 0))
            sombra.set_alpha(80)
            surf.blit(sombra, (x + 4, int(y) + 4))
            surf.blit(l, (x, int(y)))
            x += l.get_width()
        dibujar_texto(surf, 'CENTRO DE COMANDOS EDITION', 28, tema['texto'], ANCHO // 2, 225)
        if (self.t // 30) % 2 == 0:
            dibujar_texto(surf, 'PRESIONA ENTER', 34, tema['resalte'], ANCHO // 2, 360)
        st = self.app.datos.stats
        dibujar_texto(surf, 'Partidas: %d   Victorias: %d   Mejor rally: %d' % (st['partidas'], st['victorias'], st['mejor_rally']),
                      22, tema['texto'], ANCHO // 2, 460)


class EscenaMenu(Escena):
    def entrar(self, **datos):
        a = self.app
        self.menu = MenuLista(a, [
            ItemMenu('JUGAR', accion=self.jugar_rapido),
            ItemMenu('MODOS DE JUEGO', accion=lambda: a.ir_a('seleccion')),
            ItemMenu('TORNEO', accion=lambda: a.ir_a('torneo')),
            ItemMenu('PRACTICA', accion=self.practica),
            ItemMenu('RECORDS Y ESTADISTICAS', accion=lambda: a.ir_a('records')),
            ItemMenu('OPCIONES', accion=lambda: a.ir_a('opciones')),
            ItemMenu('CONTROLES Y AYUDA', accion=lambda: a.ir_a('controles')),
            ItemMenu('SALIR', accion=a.salir),
        ], ANCHO // 2, 150, ancho=400, alto_item=42, visibles=8, tam=32)

    def jugar_rapido(self):
        self.app.ir_a('juego', cfg=self.app.crear_cfg('CLASICO', 'PC'))

    def practica(self):
        self.app.ir_a('juego', cfg=self.app.crear_cfg('PRACTICA', 'PARED'))

    def evento(self, ev):
        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
            self.app.ir_a('titulo')
        else:
            self.menu.evento(ev)

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        self.fondo_menu(surf)
        self.titulo(surf, 'MENU PRINCIPAL')
        self.menu.dibujar(surf, self.app.tema)


class EscenaSeleccion(Escena):
    def entrar(self, modo=None, **datos):
        a = self.app.ajustes
        self.modo = modo if modo in MODOS else getattr(self, 'modo', 'CLASICO')
        self.jugadores = getattr(self, 'jugadores', 1)
        self.menu = MenuLista(self.app, [
            ItemMenu('MODO', obtener=lambda: self.modo, cambiar=self.cambiar_modo),
            ItemMenu('JUGADORES', obtener=lambda: '1 JUGADOR' if self.jugadores == 1 else '2 JUGADORES',
                     cambiar=self.cambiar_jugadores, activo=lambda: not MODOS[self.modo]['pared']),
            ItemMenu('DIFICULTAD PC', obtener=lambda: NIVELES_IA[a['dificultad']]['nombre'],
                     cambiar=self.cambiar_dificultad,
                     activo=lambda: self.jugadores == 1 and not MODOS[self.modo]['pared']),
            ItemMenu('PUNTOS PARA GANAR', obtener=lambda: a['puntos'], cambiar=self.cambiar_puntos,
                     activo=lambda: not MODOS[self.modo]['pared']),
            ItemMenu('COMENZAR', accion=self.comenzar),
            ItemMenu('VOLVER', accion=lambda: self.app.ir_a('menu')),
        ], ANCHO // 2, 130, ancho=420, alto_item=38, visibles=6, tam=30)

    def cambiar_modo(self, d):
        i = (ORDEN_MODOS.index(self.modo) + d) % len(ORDEN_MODOS)
        self.modo = ORDEN_MODOS[i]

    def cambiar_jugadores(self, d):
        self.jugadores = 2 if self.jugadores == 1 else 1

    def cambiar_dificultad(self, d):
        a = self.app.ajustes
        a['dificultad'] = (a['dificultad'] + d) % len(NIVELES_IA)

    def cambiar_puntos(self, d):
        a = self.app.ajustes
        a['puntos'] = int(limitar(a['puntos'] + d, 1, 10))

    def comenzar(self):
        if MODOS[self.modo]['pared']:
            rival = 'PARED'
        else:
            rival = 'PC' if self.jugadores == 1 else 'HUMANO'
        self.app.ir_a('juego', cfg=self.app.crear_cfg(self.modo, rival))

    def evento(self, ev):
        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
            self.app.ir_a('menu')
        else:
            self.menu.evento(ev)

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        self.fondo_menu(surf)
        self.titulo(surf, 'MODOS DE JUEGO')
        self.menu.dibujar(surf, tema)
        reglas = MODOS[self.modo]
        caja = Rect(60, 335, ANCHO - 120, 140)
        panel_translucido(surf, caja, tema['panel'], 190, tema['resalte'])
        y = caja.y + 22
        for linea in partir_lineas(reglas['desc'], 24, caja.width - 30):
            dibujar_texto(surf, linea, 24, (255, 255, 255), caja.x + 15, y, 'izq', sombra=False)
            y += 24
        datos = ['Power-ups: ' + ('SI' if reglas['powerups'] else 'NO'),
                 'Pelotas: %d' % reglas['pelotas'],
                 'Aceleracion: %d%%' % int(reglas['acel'] * 100)]
        if reglas['vidas']:
            datos.append('Vidas: %d' % reglas['vidas'])
        if reglas['pared']:
            datos.append('Rival: PARED')
        dibujar_texto(surf, '   '.join(datos), 21, tema['resalte'], caja.x + 15, caja.bottom - 18, 'izq', sombra=False)


class EscenaOpciones(Escena):
    def entrar(self, **datos):
        a = self.app.ajustes
        self.confirmar = False
        sino = lambda clave: (lambda: 'SI' if a[clave] else 'NO')

        def alternar(clave):
            def f(d):
                a[clave] = not a[clave]
            return f

        def numero(clave, minimo, maximo, paso=1, extra=None):
            def f(d):
                a[clave] = int(limitar(a[clave] + d * paso, minimo, maximo))
                if extra:
                    extra()
            return f

        self.menu = MenuLista(self.app, [
            ItemMenu('VOLUMEN', obtener=lambda: a['volumen'],
                     cambiar=numero('volumen', 0, 10, 1, lambda: self.app.sonidos.reproducir('golpe'))),
            ItemMenu('TEMA', obtener=lambda: a['tema'], cambiar=self.cambiar_tema),
            ItemMenu('PARTICULAS', obtener=sino('particulas'), cambiar=alternar('particulas')),
            ItemMenu('SACUDIDA DE PANTALLA', obtener=sino('sacudida'), cambiar=alternar('sacudida')),
            ItemMenu('ESTELA DE LA PELOTA', obtener=sino('estela'), cambiar=alternar('estela')),
            ItemMenu('COLOREAR RAQUETAS', obtener=sino('tinte'), cambiar=self.cambiar_tinte),
            ItemMenu('CONTROL CON RATON', obtener=sino('raton'), cambiar=alternar('raton')),
            ItemMenu('VELOCIDAD PELOTA', obtener=lambda: a['vel_pelota'], cambiar=numero('vel_pelota', 1, 10)),
            ItemMenu('VELOCIDAD RAQUETAS', obtener=lambda: a['vel_raquetas'], cambiar=numero('vel_raquetas', 2, 12)),
            ItemMenu('DIFICULTAD PC', obtener=lambda: NIVELES_IA[a['dificultad']]['nombre'],
                     cambiar=numero('dificultad', 0, len(NIVELES_IA) - 1)),
            ItemMenu('PUNTOS PARA GANAR', obtener=lambda: a['puntos'], cambiar=numero('puntos', 1, 10)),
            ItemMenu('ANGULO RAQUETAS', obtener=lambda: str(a['angulo']) + ' grados', cambiar=self.cambiar_angulo),
            ItemMenu('ENDEREZAR RAQUETAS (AUTO)', accion=self.enderezar),
            ItemMenu('MOSTRAR FPS', obtener=sino('fps_visible'), cambiar=alternar('fps_visible')),
            ItemMenu(lambda: 'PULSA OTRA VEZ PARA CONFIRMAR' if self.confirmar else 'BORRAR RECORDS',
                     accion=self.borrar),
            ItemMenu('VOLVER', accion=self.volver),
        ], ANCHO // 2, 130, ancho=460, alto_item=34, visibles=10, tam=26)

    def cambiar_tema(self, d):
        a = self.app.ajustes
        i = (ORDEN_TEMAS.index(a['tema']) + d) % len(ORDEN_TEMAS)
        a['tema'] = ORDEN_TEMAS[i]
        self.app.fondo.cambiar_tema(a['tema'])

    def cambiar_tinte(self, d):
        a = self.app.ajustes
        a['tinte'] = not a['tinte']

    def cambiar_angulo(self, d):
        a = self.app.ajustes
        a['angulo'] = (a['angulo'] + 5 * d + 180) % 360 - 180
        self.app.reconstruir_raquetas()

    def enderezar(self):
        self.app.ajustes['angulo'] = angulo_auto(self.app.base_raqueta)
        self.app.reconstruir_raquetas()

    def borrar(self):
        if self.confirmar:
            self.app.datos.borrar_records()
            self.confirmar = False
        else:
            self.confirmar = True

    def volver(self):
        self.app.datos.guardar()
        self.app.ir_a('menu')

    def evento(self, ev):
        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
            self.volver()
        else:
            if ev.type == KEYDOWN and ev.key in (K_UP, K_DOWN):
                self.confirmar = False
            self.menu.evento(ev)

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        self.fondo_menu(surf)
        self.titulo(surf, 'OPCIONES')
        self.menu.dibujar(surf, tema)
        vista = self.app.img_raqueta
        surf.blit(transform.scale(vista, (25, 75)), (20, 200))
        surf.blit(transform.scale(vista, (25, 75)), (ANCHO - 45, 200))


class EscenaControles(Escena):
    def entrar(self, **datos):
        self.pagina = 0
        self.total = 3

    def evento(self, ev):
        if ev.type == KEYDOWN:
            if ev.key in (K_ESCAPE, K_RETURN):
                self.app.ir_a('menu')
            elif ev.key in (K_RIGHT, K_d):
                self.pagina = (self.pagina + 1) % self.total
                self.app.sonidos.reproducir('menu')
            elif ev.key in (K_LEFT, K_a):
                self.pagina = (self.pagina - 1) % self.total
                self.app.sonidos.reproducir('menu')
        elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
            self.pagina = (self.pagina + 1) % self.total

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        self.fondo_menu(surf)
        nombres = ['CONTROLES', 'POWER-UPS', 'MODOS']
        self.titulo(surf, nombres[self.pagina], 'pagina %d de %d  (izquierda / derecha)' % (self.pagina + 1, self.total))
        caja = Rect(40, 105, ANCHO - 80, 350)
        panel_translucido(surf, caja, tema['panel'], 195, tema['resalte'])
        blanco = (255, 255, 255)
        if self.pagina == 0:
            lineas = [('Jugador izquierdo', 'W / S'), ('Jugador derecho', 'Flechas arriba / abajo'),
                      ('Contra la PC', 'W / S o flechas'), ('Control con raton', 'activalo en Opciones'),
                      ('Centro de comandos', 'TAB'), ('Pausa', 'P o ESC'),
                      ('Cambiar 2 JUG / VS PC', 'M'), ('Menus', 'flechas + ENTER o raton')]
            for i, (a, b) in enumerate(lineas):
                y = caja.y + 32 + i * 38
                dibujar_texto(surf, a, 28, tema['resalte'], caja.x + 20, y, 'izq', sombra=False)
                dibujar_texto(surf, b, 26, blanco, caja.right - 20, y, 'der', sombra=False)
        elif self.pagina == 1:
            for i, tipo in enumerate(TIPOS_POWERUP):
                info = TIPOS_POWERUP[tipo]
                y = caja.y + 30 + i * 41
                dibujar_icono_powerup(surf, tipo, caja.x + 36, y, 15, tema)
                dibujar_texto(surf, info['nombre'], 24, tema['resalte'], caja.x + 66, y, 'izq', sombra=False)
                dibujar_texto(surf, info['info'], 20, blanco, caja.x + 66 + 190, y, 'izq', sombra=False)
        else:
            y = caja.y + 20
            for modo in ORDEN_MODOS:
                dibujar_texto(surf, modo, 24, tema['resalte'], caja.x + 15, y, 'izq', sombra=False)
                y += 20
                for linea in partir_lineas(MODOS[modo]['desc'], 18, caja.width - 40):
                    dibujar_texto(surf, linea, 18, blanco, caja.x + 25, y, 'izq', sombra=False)
                    y += 16
                y += 6


class EscenaRecords(Escena):
    def entrar(self, **datos):
        self.pagina = 0

    def evento(self, ev):
        total = len(MODOS_CON_RECORD) + 1
        if ev.type == KEYDOWN:
            if ev.key in (K_ESCAPE, K_RETURN):
                self.app.ir_a('menu')
            elif ev.key in (K_RIGHT, K_d):
                self.pagina = (self.pagina + 1) % total
                self.app.sonidos.reproducir('menu')
            elif ev.key in (K_LEFT, K_a):
                self.pagina = (self.pagina - 1) % total
                self.app.sonidos.reproducir('menu')
        elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
            self.pagina = (self.pagina + 1) % total

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        self.fondo_menu(surf)
        caja = Rect(60, 105, ANCHO - 120, 350)
        panel_translucido(surf, caja, tema['panel'], 195, tema['resalte'])
        blanco = (255, 255, 255)
        if self.pagina < len(MODOS_CON_RECORD):
            modo = MODOS_CON_RECORD[self.pagina]
            self.titulo(surf, 'RECORDS', modo + '   (izquierda / derecha)')
            lista = self.app.datos.lista_records(modo)
            for i in range(5):
                y = caja.y + 50 + i * 55
                if i < len(lista):
                    dibujar_texto(surf, '%d.' % (i + 1), 36, tema['resalte'], caja.x + 30, y, 'izq', sombra=False)
                    dibujar_texto(surf, lista[i]['nombre'], 36, blanco, caja.x + 100, y, 'izq', sombra=False)
                    dibujar_texto(surf, str(lista[i]['puntos']), 36, blanco, caja.right - 30, y, 'der', sombra=False)
                else:
                    dibujar_texto(surf, '%d.  ---' % (i + 1), 32, (150, 150, 170), caja.x + 30, y, 'izq', sombra=False)
        else:
            self.titulo(surf, 'ESTADISTICAS', '(izquierda / derecha)')
            st = self.app.datos.stats
            filas = [('Partidas jugadas', st['partidas']), ('Victorias', st['victorias']),
                     ('Derrotas', st['derrotas']), ('Golpes totales', st['golpes']),
                     ('Puntos marcados', st['puntos']), ('Mejor rally', st['mejor_rally']),
                     ('Mejor racha de victorias', st['mejor_racha']), ('Torneos ganados', st['torneos']),
                     ('Tiempo jugado', formato_tiempo(st['segundos'] * FPS_OBJETIVO))]
            for i, (nombre, valor) in enumerate(filas):
                y = caja.y + 28 + i * 36
                dibujar_texto(surf, nombre, 26, tema['resalte'], caja.x + 25, y, 'izq', sombra=False)
                dibujar_texto(surf, str(valor), 26, blanco, caja.right - 25, y, 'der', sombra=False)
        dibujar_texto(surf, 'ESC: volver', 22, tema['texto'], ANCHO // 2, 478)


class EscenaTorneo(Escena):
    def entrar(self, ver=False, **datos):
        if not ver or self.app.torneo is None:
            self.app.torneo = {'etapa': 0, 'puntos': 0, 'estado': 'activo'}
        t = self.app.torneo
        if t['estado'] == 'activo':
            items = [ItemMenu('JUGAR RONDA %d' % (t['etapa'] + 1), accion=self.jugar),
                     ItemMenu('ABANDONAR TORNEO', accion=lambda: self.app.ir_a('menu'))]
        else:
            items = [ItemMenu('NUEVO TORNEO', accion=lambda: self.app.ir_a('torneo')),
                     ItemMenu('MENU PRINCIPAL', accion=lambda: self.app.ir_a('menu'))]
        self.menu = MenuLista(self.app, items, ANCHO // 2, 415, ancho=360, alto_item=40, visibles=2, tam=30)

    def jugar(self):
        t = self.app.torneo
        etapa = ETAPAS_TORNEO[t['etapa']]
        cfg = self.app.crear_cfg(etapa['modo'], 'PC', nivel=etapa['nivel'],
                                 puntos=max(3, self.app.ajustes['puntos']), torneo=True, etapa=t['etapa'])
        self.app.ir_a('juego', cfg=cfg)

    def evento(self, ev):
        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
            self.app.ir_a('menu')
        else:
            self.menu.evento(ev)

    def actualizar(self):
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        t = self.app.torneo
        self.fondo_menu(surf)
        subtitulo = {'activo': 'Gana las 4 rondas para ser campeon', 'perdido': 'ELIMINADO',
                     'campeon': 'CAMPEON DEL TORNEO!'}[t['estado']]
        self.titulo(surf, 'TORNEO', subtitulo)
        for i, etapa in enumerate(ETAPAS_TORNEO):
            y = 135 + i * 62
            caja = Rect(60, y - 25, ANCHO - 120, 54)
            if i < t['etapa'] or t['estado'] == 'campeon':
                estado, color = 'GANADA', (120, 230, 120)
            elif i == t['etapa'] and t['estado'] == 'perdido':
                estado, color = 'PERDIDA', (255, 110, 110)
            elif i == t['etapa']:
                estado, color = 'EN CURSO', tema['resalte']
            else:
                estado, color = 'PENDIENTE', (160, 160, 180)
            panel_translucido(surf, caja, tema['panel'], 190, color)
            draw.rect(surf, etapa['color'], (caja.x + 8, caja.y + 8, 8, caja.height - 16))
            dibujar_texto(surf, 'RONDA %d: %s' % (i + 1, etapa['rival']), 28, (255, 255, 255), caja.x + 28, y - 8, 'izq', sombra=False)
            dibujar_texto(surf, '%s - %s' % (etapa['modo'], NIVELES_IA[etapa['nivel']]['nombre']), 20, (200, 210, 230),
                          caja.x + 28, y + 14, 'izq', sombra=False)
            dibujar_texto(surf, estado, 26, color, caja.right - 15, y, 'der', sombra=False)
        dibujar_texto(surf, 'Puntos del torneo: %d' % t['puntos'], 26, tema['texto'], ANCHO // 2, 385)
        self.menu.dibujar(surf, tema)


# ======================================================================
#                         ESCENA DE JUEGO (la partida)
# ======================================================================
class EscenaJuego(Escena):
    def entrar(self, cfg=None, **datos):
        a = self.app.ajustes
        self.cfg = dict(cfg) if cfg else self.app.crear_cfg('CLASICO', 'PC')
        self.reglas = MODOS[self.cfg['modo']]
        self.pared_activa = self.reglas['pared']
        self.lienzo = Surface((ANCHO, ALTO))
        self.particulas = SistemaParticulas()
        self.textos = TextosFlotantes()
        self.sacudida = Sacudida()
        self.r1 = Raqueta(self.app.imagen_raqueta(1), 30, 175, a['vel_raquetas'], 'izq')
        self.r2 = None
        self.ia = None
        if not self.pared_activa:
            self.r2 = Raqueta(self.app.imagen_raqueta(2), 520, 175, a['vel_raquetas'], 'der')
            if self.cfg['rival'] == 'PC':
                self.ia = IA(self.cfg['nivel'])
        self.pared = Rect(ANCHO - 14, 0, 14, ALTO)
        self.centro = CentroComandos(self.crear_comandos())
        self.menu_pausa = MenuLista(self.app, [
            ItemMenu('REANUDAR', accion=self.alternar_pausa),
            ItemMenu('CENTRO DE COMANDOS', accion=self.abrir_centro),
            ItemMenu('REINICIAR PARTIDA', accion=self.cmd_reiniciar),
            ItemMenu('SALIR AL MENU', accion=self.salir_menu),
        ], ANCHO // 2, 200, ancho=380, alto_item=46, visibles=4, tam=30)
        self.reiniciar()

    # ------------------------------------------------------------------
    #  Estado de la partida
    # ------------------------------------------------------------------
    def reiniciar(self):
        self.puntos = [0, 0]
        self.vidas = self.reglas['vidas']
        self.golpes = 0
        self.rally = 0
        self.mejor_rally = 0
        self.fallos = 0
        self.bonus = 0
        self.frames = 0
        self.bolas = []
        self.powerups = []
        self.efectos = []
        self.escala_global = 1.0
        self.t_powerup = random.randint(300, 600)
        for r in (self.r1, self.r2):
            if r is not None:
                r.alto_objetivo = r.alto_base
                r.cambiar_alto(r.alto_base)
                r.fy = 175.0
                r.rect.y = 175
                r.congelada = 0
                r.escudo = False
        self.pausado = False
        self.estado = 'cuenta'
        self.contador = 0
        self.dir_saque = random.choice([-1, 1])
        self.mensaje = ''
        self.mensaje_t = 0
        self.texto_fin = ''
        self.victoria = False
        self.t_fin = 0

    def velocidad_base(self):
        v = self.app.ajustes['vel_pelota'] * 1.2
        if self.cfg['modo'] == 'PRACTICA':
            v *= 0.85
        return v

    def sacar(self):
        n = self.reglas['pelotas']
        for i in range(n):
            y = ALTO / 2.0 if n == 1 else ALTO / 2.0 + (-60 if i % 2 == 0 else 60)
            b = Pelota(ANCHO / 2.0, y)
            direccion = self.dir_saque if i % 2 == 0 else -self.dir_saque
            if self.pared_activa:
                direccion = 1
            b.lanzar(direccion, self.velocidad_base())
            self.bolas.append(b)
        self.rally = 0

    def agregar_bola(self, desde_pared=False):
        if len(self.bolas) >= 5:
            return False
        if desde_pared:
            b = Pelota(ANCHO - 90, random.randint(80, ALTO - 80))
            b.lanzar(-1, max(self.velocidad_base(), 5.0))
        else:
            b = Pelota(ANCHO / 2.0, ALTO / 2.0)
            b.lanzar(random.choice([-1, 1]), self.velocidad_base())
        self.bolas.append(b)
        return True

    def chispas(self, x, y, cantidad, color, **kw):
        if self.app.ajustes['particulas']:
            self.particulas.emitir(x, y, cantidad, color, **kw)

    def temblar(self, fuerza):
        if self.app.ajustes['sacudida']:
            self.sacudida.disparar(fuerza)

    def decir(self, cadena, frames=70):
        self.mensaje = cadena
        self.mensaje_t = frames

    # ------------------------------------------------------------------
    #  Comandos del panel (TAB)
    # ------------------------------------------------------------------
    def crear_comandos(self):
        a = self.app.ajustes

        def numerico(clave, minimo, maximo, etiqueta, extra=None):
            def cambiar(d):
                a[clave] = int(limitar(a[clave] + d, minimo, maximo))
                if extra:
                    extra()
                self.centro.decir('%s = %s' % (etiqueta, a[clave]))
            return cambiar

        def alternar(clave, etiqueta):
            def cambiar(d):
                a[clave] = not a[clave]
                self.centro.decir('%s: %s' % (etiqueta, 'si' if a[clave] else 'no'))
            return cambiar

        return [
            {'nombre': 'Pausar / reanudar', 'valor': lambda: 'PAUSADO' if self.pausado else 'JUGANDO',
             'ejecutar': self.cmd_pausa},
            {'nombre': 'Modo de juego', 'valor': lambda: 'VS PC' if self.ia else (
                'PARED' if self.pared_activa else '2 JUG'),
             'cambiar': self.cmd_modo, 'ejecutar': self.cmd_modo},
            {'nombre': 'Dificultad PC', 'valor': lambda: NIVELES_IA[a['dificultad']]['nombre'],
             'cambiar': self.cmd_dificultad},
            {'nombre': 'Velocidad pelota', 'valor': lambda: a['vel_pelota'],
             'cambiar': numerico('vel_pelota', 1, 10, 'Velocidad pelota')},
            {'nombre': 'Velocidad raquetas', 'valor': lambda: a['vel_raquetas'],
             'cambiar': numerico('vel_raquetas', 2, 12, 'Velocidad raquetas')},
            {'nombre': 'Angulo raquetas', 'valor': lambda: str(a['angulo']) + '°', 'cambiar': self.cmd_angulo},
            {'nombre': 'Enderezar auto', 'ejecutar': self.cmd_enderezar},
            {'nombre': 'Puntos para ganar', 'valor': lambda: self.cfg['puntos'], 'cambiar': self.cmd_puntos},
            {'nombre': 'Tema', 'valor': lambda: a['tema'], 'cambiar': self.cmd_tema},
            {'nombre': 'Volumen', 'valor': lambda: a['volumen'],
             'cambiar': numerico('volumen', 0, 10, 'Volumen', lambda: self.app.sonidos.reproducir('golpe'))},
            {'nombre': 'Particulas', 'valor': lambda: 'SI' if a['particulas'] else 'NO',
             'cambiar': alternar('particulas', 'Particulas')},
            {'nombre': 'Mostrar FPS', 'valor': lambda: 'SI' if a['fps_visible'] else 'NO',
             'cambiar': alternar('fps_visible', 'FPS visibles')},
            {'nombre': 'Lanzar power-up', 'ejecutar': self.cmd_powerup},
            {'nombre': 'Anadir pelota', 'ejecutar': self.cmd_anadir_pelota},
            {'nombre': 'Reiniciar pelota', 'ejecutar': self.cmd_reiniciar_pelota},
            {'nombre': 'Reiniciar partida', 'ejecutar': self.cmd_reiniciar},
            {'nombre': 'Salir al menu', 'ejecutar': self.salir_menu},
            {'nombre': 'Cerrar centro', 'ejecutar': self.centro_cerrar},
        ]

    def cmd_pausa(self):
        self.pausado = not self.pausado
        self.centro.decir('Juego pausado' if self.pausado else 'Juego reanudado')

    def cmd_modo(self, d=1):
        if self.pared_activa or self.cfg['torneo']:
            self.centro.decir('Modo fijo en esta partida')
            return
        if self.ia is not None:
            self.ia = None
            self.cfg['rival'] = 'HUMANO'
        else:
            self.ia = IA(self.app.ajustes['dificultad'])
            self.cfg['rival'] = 'PC'
        self.reiniciar()
        self.centro.decir('Modo: ' + ('VS PC' if self.ia else '2 JUG'))

    def cmd_dificultad(self, d):
        a = self.app.ajustes
        a['dificultad'] = (a['dificultad'] + d) % len(NIVELES_IA)
        self.cfg['nivel'] = a['dificultad']
        if self.ia is not None:
            self.ia.cambiar_nivel(a['dificultad'])
        self.centro.decir('Dificultad PC = ' + NIVELES_IA[a['dificultad']]['nombre'])

    def cmd_angulo(self, d):
        a = self.app.ajustes
        a['angulo'] = (a['angulo'] + 5 * d + 180) % 360 - 180
        self.refrescar_imagenes()
        self.centro.decir('Angulo raquetas = %d' % a['angulo'])

    def cmd_enderezar(self):
        self.app.ajustes['angulo'] = angulo_auto(self.app.base_raqueta)
        self.refrescar_imagenes()
        self.centro.decir('Enderezado auto: %d grados' % self.app.ajustes['angulo'])

    def refrescar_imagenes(self):
        self.app.reconstruir_raquetas()
        self.r1.cambiar_imagen(self.app.imagen_raqueta(1))
        if self.r2 is not None:
            self.r2.cambiar_imagen(self.app.imagen_raqueta(2))

    def cmd_puntos(self, d):
        self.cfg['puntos'] = int(limitar(self.cfg['puntos'] + d, 1, 10))
        self.app.ajustes['puntos'] = self.cfg['puntos']
        self.centro.decir('Puntos para ganar = %d' % self.cfg['puntos'])

    def cmd_tema(self, d):
        a = self.app.ajustes
        a['tema'] = ORDEN_TEMAS[(ORDEN_TEMAS.index(a['tema']) + d) % len(ORDEN_TEMAS)]
        self.app.fondo.cambiar_tema(a['tema'])
        self.centro.decir('Tema: ' + a['tema'])

    def cmd_powerup(self):
        self.crear_powerup()
        self.centro.decir('Power-up lanzado')

    def cmd_anadir_pelota(self):
        if self.estado != 'juego':
            self.centro.decir('Espera a que empiece el punto')
        elif self.agregar_bola():
            self.centro.decir('Pelota anadida')
        else:
            self.centro.decir('Ya hay demasiadas pelotas')

    def cmd_reiniciar_pelota(self):
        self.bolas = []
        self.estado = 'cuenta'
        self.contador = 0
        self.centro.decir('Pelota reiniciada')

    def cmd_reiniciar(self):
        self.reiniciar()
        self.centro.decir('Partida reiniciada')

    def centro_cerrar(self):
        self.centro.visible = False

    def abrir_centro(self):
        self.centro.visible = True
        self.centro.decir('Panel abierto')

    def alternar_pausa(self):
        self.pausado = not self.pausado
        self.app.sonidos.reproducir('menu')

    def salir_menu(self):
        self.app.datos.guardar()
        self.app.ir_a('menu')

    # ------------------------------------------------------------------
    #  Eventos y actualizacion
    # ------------------------------------------------------------------
    def evento(self, ev):
        if self.estado == 'fin':
            return
        if ev.type == KEYDOWN and ev.key == K_TAB:
            self.centro.alternar()
            return
        if self.centro.visible:
            self.centro.manejar(ev)
            return
        if self.pausado:
            if ev.type == KEYDOWN and ev.key in (K_ESCAPE, K_p):
                self.alternar_pausa()
            else:
                self.menu_pausa.evento(ev)
            return
        if ev.type == KEYDOWN:
            if ev.key in (K_ESCAPE, K_p):
                self.alternar_pausa()
            elif ev.key == K_m:
                self.cmd_modo()

    def controlar_raquetas(self):
        a = self.app.ajustes
        teclas = key.get_pressed()
        if a['raton']:
            self.r1.seguir_raton(mouse.get_pos()[1])
        else:
            arriba = teclas[K_w] or (self.ia is not None and teclas[K_UP])
            abajo = teclas[K_s] or (self.ia is not None and teclas[K_DOWN])
            self.r1.mover_control(arriba, abajo)
        if self.r2 is not None:
            if self.ia is not None:
                self.r2.mover(self.ia.decidir(self.r2, self.bolas, 'der'))
            else:
                self.r2.mover_control(teclas[K_UP], teclas[K_DOWN])

    def actualizar(self):
        self.app.fondo.actualizar()
        if self.centro.visible or self.pausado:
            return
        self.particulas.actualizar()
        self.textos.actualizar()
        self.sacudida.actualizar()
        if self.mensaje_t > 0:
            self.mensaje_t -= 1
        a = self.app.ajustes
        for r in (self.r1, self.r2):
            if r is not None:
                r.speed = a['vel_raquetas']
                r.actualizar_estado()
        if self.estado == 'fin':
            self.t_fin -= 1
            if self.t_fin <= 0:
                self.salir_a_fin()
            return
        self.controlar_raquetas()
        if self.estado == 'cuenta':
            if self.contador % 40 == 0 and self.contador < 120:
                self.app.sonidos.reproducir('cuenta')
            self.contador += 1
            if self.contador >= 120:
                self.app.sonidos.reproducir('ya')
                self.sacar()
                self.estado = 'juego'
        elif self.estado == 'juego':
            self.frames += 1
            self.mover_bolas()
            self.actualizar_powerups()
            self.actualizar_efectos()

    # ------------------------------------------------------------------
    #  Fisica de la pelota
    # ------------------------------------------------------------------
    def mover_bolas(self):
        for b in list(self.bolas):
            b.escala = self.escala_global
            b.actualizar()
            minimo = b.tam / 2.0
            maximo = ALTO - b.tam / 2.0
            if b.fy < minimo:
                b.fy = minimo + (minimo - b.fy)
                b.vy = abs(b.vy)
                self.efecto_pared(b, minimo)
            elif b.fy > maximo:
                b.fy = maximo - (b.fy - maximo)
                b.vy = -abs(b.vy)
                self.efecto_pared(b, ALTO)
            b.sincronizar()
            self.rebote_raqueta(b, self.r1)
            if self.r2 is not None:
                self.rebote_raqueta(b, self.r2)
            if self.pared_activa:
                self.rebote_pared(b)
            self.revisar_salida(b)
            if self.estado == 'fin':
                return
        if not self.bolas and self.estado == 'juego':
            self.estado = 'cuenta'
            self.contador = 0

    def efecto_pared(self, b, y):
        self.app.sonidos.reproducir('pared')
        self.chispas(b.fx, y, 6, self.app.tema['particula'], vel=2.5, vida=18, tam=3)
        self.temblar(1.0)

    def rebote_pared(self, b):
        borde = self.pared.left - b.caja.width / 2.0
        if b.vx > 0 and b.fx >= borde:
            b.fx = borde
            b.vx = -abs(b.vx)
            b.sincronizar()
            self.app.sonidos.reproducir('pared')
            self.chispas(self.pared.left, b.fy, 10, self.app.tema['particula'], vel=3.5, vida=22, tam=3,
                         angulo=180, apertura=120)
            self.temblar(1.5)

    def rebote_raqueta(self, b, r):
        if not b.caja.colliderect(r.rect):
            return False
        izq = (r.lado == 'izq')
        if izq and (b.vx >= 0 or b.fx < r.rect.left):
            return False
        if (not izq) and (b.vx <= 0 or b.fx > r.rect.right):
            return False
        # el angulo depende de en que parte de la raqueta pega la pelota (como el Pong original)
        rel = limitar((b.fy - r.rect.centery) / (r.rect.height / 2.0), -1.0, 1.0)
        angulo = rel * math.radians(ANGULO_MAX)
        velocidad = min(VEL_MAX, b.velocidad * (1.0 + self.reglas['acel']) + 0.05)
        direccion = 1 if izq else -1
        b.vx = direccion * velocidad * math.cos(angulo)
        b.vy = velocidad * math.sin(angulo) + r.vy * 0.35      # la raqueta en movimiento da efecto
        b.fijar_velocidad(velocidad)
        b.corregir_angulo()
        b.giro = limitar(r.vy * 0.25, -3.0, 3.0)
        mitad = b.caja.width / 2.0
        b.fx = (r.rect.right + mitad + 1) if izq else (r.rect.left - mitad - 1)
        b.sincronizar()
        b.ultimo = 1 if izq else 2
        r.destello = 8
        self.rally += 1
        self.mejor_rally = max(self.mejor_rally, self.rally)
        self.app.sonidos.reproducir('golpe')
        color = self.app.tema['j1'] if izq else self.app.tema['j2']
        self.chispas(b.fx, b.fy, 12, color, vel=4.0, vida=24, tam=4, angulo=0 if izq else 180, apertura=140)
        self.temblar(1.5 + velocidad * 0.15)
        if izq:
            self.golpes += 1
            if self.cfg['modo'] == 'SUPERVIVENCIA' and self.golpes % 12 == 0 and self.agregar_bola(True):
                self.textos.agregar('OTRA PELOTA!', ANCHO / 2, 140, self.app.tema['resalte'], 34, 70)
        if self.rally % 5 == 0:
            self.textos.agregar('COMBO x%d' % self.rally, b.fx, b.fy - 30, self.app.tema['resalte'], 30, 60)
        return True

    def revisar_salida(self, b):
        if b.fx < 10 and b.vx < 0 and self.r1.escudo:
            self.usar_escudo(self.r1, b, 14)
        elif self.r2 is not None and b.fx > ANCHO - 10 and b.vx > 0 and self.r2.escudo:
            self.usar_escudo(self.r2, b, ANCHO - 14)
        if b.fx < -b.tam / 2.0:
            self.bolas.remove(b)
            if self.pared_activa:
                self.fallo(b)
            else:
                self.anotar(2, b)
        elif b.fx > ANCHO + b.tam / 2.0:
            self.bolas.remove(b)
            self.anotar(1, b)

    def usar_escudo(self, raqueta, b, x):
        raqueta.escudo = False
        b.vx = -b.vx
        b.fx = x
        b.sincronizar()
        self.app.sonidos.reproducir('escudo')
        self.chispas(x, b.fy, 25, TIPOS_POWERUP['ESCUDO']['color'], vel=5, vida=30, tam=4)
        self.temblar(5)
        self.textos.agregar('ESCUDO!', x + (60 if raqueta.lado == 'izq' else -60), b.fy,
                            TIPOS_POWERUP['ESCUDO']['color'], 30, 50)

    # ------------------------------------------------------------------
    #  Puntos, vidas y fin de la partida
    # ------------------------------------------------------------------
    def anotar(self, para, b):
        self.puntos[para - 1] += 1
        self.rally = 0
        x = 20 if para == 2 else ANCHO - 20
        self.app.sonidos.reproducir('punto')
        self.temblar(7)
        self.chispas(x, b.fy, 40, self.app.tema['particula'], vel=6, vida=45, tam=5)
        if para == 1:
            nombre = 'J1'
        else:
            nombre = 'PC' if self.ia is not None else 'J2'
        self.decir('PUNTO %s' % nombre, 60)
        self.dir_saque = 1 if para == 1 else -1
        meta = self.cfg['puntos']
        if self.puntos[0] >= meta:
            self.terminar(True)
        elif self.puntos[1] >= meta:
            self.terminar(False)

    def fallo(self, b):
        self.fallos += 1
        self.rally = 0
        self.app.sonidos.reproducir('punto')
        self.temblar(6)
        self.chispas(20, b.fy, 30, self.app.tema['particula'], vel=5, vida=40, tam=4)
        if self.vidas:
            self.vidas -= 1
            self.decir('TE QUEDAN %d VIDAS' % self.vidas if self.vidas else 'SIN VIDAS', 60)
            if self.vidas <= 0:
                self.terminar(False)
        else:
            self.decir('FALLASTE', 50)

    def terminar(self, victoria):
        self.estado = 'fin'
        self.t_fin = 110
        self.victoria = victoria
        if self.pared_activa:
            self.texto_fin = 'FIN DEL JUEGO'
        elif self.ia is not None:
            self.texto_fin = 'GANASTE!' if victoria else 'PERDISTE'
        else:
            self.texto_fin = 'GANA J1' if victoria else 'GANA J2'
        gana_algo = victoria or self.ia is None
        self.app.sonidos.reproducir('ganar' if gana_algo else 'perder')
        self.temblar(10)
        if gana_algo and not self.pared_activa:
            self.chispas(ANCHO / 2, ALTO / 2, 80, self.app.tema['resalte'], vel=7, vida=70, tam=5, grav=0.1)
        self.bolas = []

    def calcular_puntuacion(self):
        base = self.golpes * 10 + self.puntos[0] * 100 + self.mejor_rally * 15 + self.bonus
        if self.victoria and not self.pared_activa:
            base += 300
        multiplicador = 1.0 + 0.25 * self.cfg['nivel'] if self.cfg['rival'] == 'PC' else 1.0
        return int(base * multiplicador)

    def salir_a_fin(self):
        res = {
            'cfg': self.cfg, 'victoria': self.victoria, 'puntos': tuple(self.puntos),
            'golpes': self.golpes, 'mejor_rally': self.mejor_rally, 'frames': self.frames,
            'puntuacion': self.calcular_puntuacion(), 'fallos': self.fallos,
            'registra': self.reglas['record'] and self.cfg['rival'] != 'HUMANO',
            'cuenta_resultado': (not self.pared_activa) and self.cfg['rival'] == 'PC',
            'texto': self.texto_fin,
        }
        self.app.ir_a('fin', res=res)

    # ------------------------------------------------------------------
    #  Power-ups
    # ------------------------------------------------------------------
    def crear_powerup(self, tipo=None):
        tipo = tipo or random.choice(list(TIPOS_POWERUP.keys()))
        self.powerups.append(PowerUp(tipo, random.randint(200, 400), random.randint(70, 430)))

    def actualizar_powerups(self):
        if self.reglas['powerups']:
            self.t_powerup -= 1
            if self.t_powerup <= 0:
                self.t_powerup = random.randint(420, 780)
                if len(self.powerups) < 2:
                    self.crear_powerup()
        for p in list(self.powerups):
            p.actualizar()
            if p.vida <= 0:
                self.powerups.remove(p)
                continue
            for b in self.bolas:
                if b.ultimo and p.rect.colliderect(b.caja):
                    self.recoger(p, b)
                    self.powerups.remove(p)
                    break

    def recoger(self, p, b):
        info = TIPOS_POWERUP[p.tipo]
        self.aplicar_powerup(p.tipo, b.ultimo, b)
        self.app.sonidos.reproducir('powerup')
        self.chispas(p.x, p.y, 30, info['color'], vel=5, vida=35, tam=4)
        self.textos.agregar(info['nombre'], p.x, p.y - 20, info['color'], 28, 80)

    def registrar_efecto(self, tipo, lado, duracion):
        for e in self.efectos:
            if e['tipo'] == tipo and e['lado'] == lado:
                e['resta'] = duracion
                e['total'] = duracion
                return
        self.efectos.append({'tipo': tipo, 'lado': lado, 'resta': duracion, 'total': duracion})

    def aplicar_powerup(self, tipo, lado, bola):
        propia = self.r1 if lado == 1 else (self.r2 or self.r1)
        rival = self.r2 if lado == 1 else self.r1
        if rival is propia:
            rival = None
        dur = TIPOS_POWERUP[tipo]['dur']
        if tipo == 'GRANDE':
            self.registrar_efecto(tipo, lado, dur)
        elif tipo == 'PEQUENA' and rival is not None:
            self.registrar_efecto(tipo, 2 if lado == 1 else 1, dur)
        elif tipo in ('LENTO', 'RAPIDO'):
            self.registrar_efecto(tipo, 0, dur)
        elif tipo == 'MULTI':
            for giro in (-25, 25):
                if len(self.bolas) >= 5:
                    break
                nueva = Pelota(bola.fx, bola.fy)
                ang = math.radians(giro)
                nueva.vx = bola.vx * math.cos(ang) - bola.vy * math.sin(ang)
                nueva.vy = bola.vx * math.sin(ang) + bola.vy * math.cos(ang)
                nueva.ultimo = lado
                self.bolas.append(nueva)
        elif tipo == 'ESCUDO':
            propia.escudo = True
        elif tipo == 'CONGELA' and rival is not None:
            rival.congelada = dur
            self.app.sonidos.reproducir('congela')
        elif tipo == 'BONUS' and lado == 1:
            self.bonus += 300

    def actualizar_efectos(self):
        escala = 1.0
        ajustes_alto = {1: 0, 2: 0}
        for e in list(self.efectos):
            e['resta'] -= 1
            if e['resta'] <= 0:
                self.efectos.remove(e)
                continue
            if e['tipo'] == 'LENTO':
                escala *= 0.65
            elif e['tipo'] == 'RAPIDO':
                escala *= 1.4
            elif e['tipo'] == 'GRANDE':
                ajustes_alto[e['lado']] += 70
            elif e['tipo'] == 'PEQUENA':
                ajustes_alto[e['lado']] -= 60
        self.escala_global = escala
        for lado, r in ((1, self.r1), (2, self.r2)):
            if r is not None:
                r.alto_objetivo = int(limitar(r.alto_base + ajustes_alto[lado], 70, 260))

    # ------------------------------------------------------------------
    #  Dibujo
    # ------------------------------------------------------------------
    def dibujar_pared(self, surf):
        tema = self.app.tema
        draw.rect(surf, tema['texto'], self.pared)
        for y in range(0, ALTO, 24):
            draw.line(surf, tema['fondo2'], (self.pared.left, y), (ANCHO, y), 2)

    def dibujar_hud(self, surf):
        tema = self.app.tema
        a = self.app.ajustes
        if not self.pared_activa:
            dibujar_texto(surf, str(self.puntos[0]), 64, tema['j1'], ANCHO // 2 - 60, 50)
            dibujar_texto(surf, '-', 48, tema['texto'], ANCHO // 2, 50)
            dibujar_texto(surf, str(self.puntos[1]), 64, tema['j2'], ANCHO // 2 + 60, 50)
            dibujar_texto(surf, 'J1', 22, tema['j1'], 40, 20)
            dibujar_texto(surf, 'PC' if self.ia is not None else 'J2', 22, tema['j2'], ANCHO - 40, 20)
            dibujar_texto(surf, 'META %d' % self.cfg['puntos'], 18, tema['texto'], ANCHO // 2, 90)
        else:
            dibujar_texto(surf, 'GOLPES %d' % self.golpes, 40, tema['texto'], ANCHO // 2, 35)
            if self.reglas['vidas']:
                for i in range(self.vidas):
                    draw.circle(surf, (230, 60, 80), (ANCHO - 60 - i * 26, 25), 9)
                    draw.circle(surf, (255, 255, 255), (ANCHO - 60 - i * 26, 25), 9, 2)
            else:
                dibujar_texto(surf, 'FALLOS %d' % self.fallos, 22, tema['texto'], 70, 20)
        if self.rally >= 2:
            dibujar_texto(surf, 'RALLY %d' % self.rally, 24, tema['resalte'], ANCHO // 2, 112)
        if a['fps_visible']:
            dibujar_texto(surf, 'FPS: %d' % int(self.app.reloj.get_fps()), 20, (0, 120, 0), 10, 48, 'izq')
        # iconos de efectos activos
        contadores = {0: 0, 1: 0, 2: 0}
        for e in self.efectos:
            lado = e['lado']
            n = contadores[lado]
            contadores[lado] += 1
            if lado == 2:
                x = ANCHO - 30 - n * 36
            elif lado == 1:
                x = 30 + n * 36
            else:
                x = ANCHO // 2 - 18 + n * 36
            y = ALTO - 50
            dibujar_icono_powerup(surf, e['tipo'], x, y, 11, tema)
            ancho = int(28 * e['resta'] / float(e['total']))
            draw.rect(surf, TIPOS_POWERUP[e['tipo']]['color'], (x - 14, y + 15, ancho, 4))
        dibujar_texto(surf, self.cfg['modo'], 20, tema['texto'], 10, ALTO - 14, 'izq')
        if self.ia is not None:
            etiqueta = 'VS PC - ' + NIVELES_IA[self.ia.nivel]['nombre']
        else:
            etiqueta = 'PARED' if self.pared_activa else '2 JUGADORES'
        dibujar_texto(surf, etiqueta, 20, tema['texto'], ANCHO - 10, ALTO - 14, 'der')
        dibujar_texto(surf, 'TAB: comandos | P: pausa | M: modo', 18, tema['texto'], ANCHO // 2, ALTO - 14)

    def dibujar_estado(self, surf):
        tema = self.app.tema
        if self.estado == 'cuenta' and self.contador < 120:
            numero = 3 - self.contador // 40
            tam = 120 + (40 - self.contador % 40)
            dibujar_texto(surf, str(numero), tam, tema['resalte'], ANCHO // 2, ALTO // 2)
        if self.mensaje_t > 0 and self.estado != 'fin':
            dibujar_texto(surf, self.mensaje, 40, tema['resalte'], ANCHO // 2, 150)
        if self.estado == 'fin':
            dibujar_texto(surf, self.texto_fin, 64, tema['resalte'], ANCHO // 2, ALTO // 2)

    def dibujar(self, surf):
        tema = self.app.tema
        a = self.app.ajustes
        lienzo = self.lienzo
        self.app.fondo.dibujar(lienzo)
        if self.pared_activa:
            self.dibujar_pared(lienzo)
        for p in self.powerups:
            p.dibujar(lienzo, tema)
        for b in self.bolas:
            b.dibujar(lienzo, tema, a['estela'])
        self.r1.dibujar(lienzo, tema)
        if self.r2 is not None:
            self.r2.dibujar(lienzo, tema)
        self.particulas.dibujar(lienzo)
        self.textos.dibujar(lienzo)
        self.dibujar_hud(lienzo)
        self.dibujar_estado(lienzo)
        surf.fill(tema['fondo'])
        if a['sacudida']:
            surf.blit(lienzo, self.sacudida.desplazamiento())
        else:
            surf.blit(lienzo, (0, 0))
        if self.pausado and not self.centro.visible:
            panel_translucido(surf, Rect(0, 0, ANCHO, ALTO), (0, 0, 0), 150)
            dibujar_texto(surf, 'PAUSA', 64, (255, 255, 255), ANCHO // 2, 110)
            self.menu_pausa.dibujar(surf, {'texto': (255, 255, 255), 'fondo': (20, 30, 60),
                                           'resalte': tema['resalte']})
        self.centro.dibujar(surf)


# ======================================================================
#                      ESCENA DE FIN DE PARTIDA
# ======================================================================
class EscenaFin(Escena):
    def entrar(self, res=None, **datos):
        self.res = res
        a = self.app.ajustes
        cfg = res['cfg']
        self.t = 0
        self.actualizar_stats()
        self.modo_record = None
        self.puntos_record = 0
        if cfg.get('torneo'):
            t = self.app.torneo
            t['puntos'] += res['puntuacion']
            if res['victoria']:
                t['puntos'] += 500
                t['etapa'] += 1
                if t['etapa'] >= len(ETAPAS_TORNEO):
                    t['estado'] = 'campeon'
                    self.app.datos.stats['torneos'] += 1
                    self.app.datos.guardar()
            else:
                t['estado'] = 'perdido'
            if t['estado'] != 'activo':
                self.modo_record = 'TORNEO'
                self.puntos_record = t['puntos']
        elif res['registra']:
            self.modo_record = cfg['modo']
            self.puntos_record = res['puntuacion']
        self.es_record = bool(self.modo_record) and self.app.datos.es_record(self.modo_record, self.puntos_record)
        self.letras = [c if 'A' <= c <= 'Z' else 'A' for c in a['nombre']]
        self.pos = 0
        self.registrado = not self.es_record
        self.armar_menu()

    def actualizar_stats(self):
        st = self.app.datos.stats
        res = self.res
        st['partidas'] += 1
        st['golpes'] += res['golpes']
        st['puntos'] += res['puntos'][0]
        st['segundos'] += res['frames'] // FPS_OBJETIVO
        st['mejor_rally'] = max(st['mejor_rally'], res['mejor_rally'])
        if res['cuenta_resultado']:
            if res['victoria']:
                st['victorias'] += 1
                st['racha'] += 1
                st['mejor_racha'] = max(st['mejor_racha'], st['racha'])
            else:
                st['derrotas'] += 1
                st['racha'] = 0
        self.app.datos.guardar()

    def armar_menu(self):
        cfg = self.res['cfg']
        a = self.app
        if cfg.get('torneo'):
            if a.torneo['estado'] == 'activo':
                items = [ItemMenu('SIGUIENTE RONDA', accion=lambda: a.ir_a('torneo', ver=True)),
                         ItemMenu('MENU PRINCIPAL', accion=lambda: a.ir_a('menu'))]
            else:
                items = [ItemMenu('VER TORNEO', accion=lambda: a.ir_a('torneo', ver=True)),
                         ItemMenu('MENU PRINCIPAL', accion=lambda: a.ir_a('menu'))]
        else:
            items = [ItemMenu('REVANCHA', accion=lambda: a.ir_a('juego', cfg=cfg)),
                     ItemMenu('CAMBIAR MODO', accion=lambda: a.ir_a('seleccion', modo=cfg['modo'])),
                     ItemMenu('MENU PRINCIPAL', accion=lambda: a.ir_a('menu'))]
        self.menu = MenuLista(a, items, ANCHO // 2, 410, ancho=380, alto_item=40, visibles=3, tam=30)

    def cambiar_letra(self, d):
        c = (ord(self.letras[self.pos]) - 65 + d) % 26
        self.letras[self.pos] = chr(65 + c)

    def confirmar_nombre(self):
        nombre = ''.join(self.letras)
        self.app.ajustes['nombre'] = nombre
        self.app.datos.agregar_record(self.modo_record, nombre, self.puntos_record)
        self.registrado = True
        self.app.sonidos.reproducir('aceptar')

    def evento(self, ev):
        if not self.registrado:
            if ev.type == KEYDOWN:
                if ev.key in (K_RETURN, K_KP_ENTER):
                    self.confirmar_nombre()
                elif ev.key == K_LEFT or ev.key == K_BACKSPACE:
                    self.pos = max(0, self.pos - 1)
                elif ev.key == K_RIGHT:
                    self.pos = min(2, self.pos + 1)
                elif ev.key == K_UP:
                    self.cambiar_letra(1)
                elif ev.key == K_DOWN:
                    self.cambiar_letra(-1)
                elif ev.unicode and ev.unicode.isascii() and ev.unicode.isalpha():
                    self.letras[self.pos] = ev.unicode.upper()
                    self.pos = min(2, self.pos + 1)
            return
        if ev.type == KEYDOWN and ev.key == K_ESCAPE:
            self.app.ir_a('menu')
        else:
            self.menu.evento(ev)

    def actualizar(self):
        self.t += 1
        self.actualizar_fondo()

    def dibujar(self, surf):
        tema = self.app.tema
        res = self.res
        self.fondo_menu(surf)
        self.titulo(surf, res['texto'], 'Modo: ' + res['cfg']['modo'])
        caja = Rect(110, 105, ANCHO - 220, 200)
        panel_translucido(surf, caja, tema['panel'], 200, tema['resalte'])
        filas = [('Marcador', '%d - %d' % res['puntos']), ('Golpes', res['golpes']),
                 ('Mejor rally', res['mejor_rally']), ('Tiempo', formato_tiempo(res['frames'])),
                 ('PUNTUACION', res['puntuacion'])]
        for i, (nombre, valor) in enumerate(filas):
            y = caja.y + 28 + i * 36
            color = tema['resalte'] if i == len(filas) - 1 else (255, 255, 255)
            dibujar_texto(surf, nombre, 28, color, caja.x + 20, y, 'izq', sombra=False)
            dibujar_texto(surf, str(valor), 28, color, caja.right - 20, y, 'der', sombra=False)
        if not self.registrado:
            dibujar_texto(surf, 'NUEVO RECORD! ESCRIBE TUS INICIALES', 26, tema['resalte'], ANCHO // 2, 335)
            for i, letra in enumerate(self.letras):
                x = ANCHO // 2 - 60 + i * 60
                caja_letra = Rect(x - 22, 355, 44, 56)
                activa = (i == self.pos) and (self.t // 15) % 2 == 0
                panel_translucido(surf, caja_letra, tema['panel'], 220, tema['resalte'] if activa else (150, 150, 170))
                dibujar_texto(surf, letra, 48, (255, 255, 255), x, 383, sombra=False)
            dibujar_texto(surf, 'flechas o teclado - ENTER para guardar', 20, tema['texto'], ANCHO // 2, 440)
        else:
            if self.es_record:
                dibujar_texto(surf, 'RECORD GUARDADO', 24, tema['resalte'], ANCHO // 2, 335)
            self.menu.dibujar(surf, tema)


# ======================================================================
#                    APLICACION (ventana, escenas y bucle)
# ======================================================================
window = None      # ventana principal (la usa GameSprite.reset)


class App:
    def __init__(self):
        global window
        try:
            mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        init()
        window = display.set_mode((ANCHO, ALTO))
        display.set_caption('Ping Pong - TAB para el centro de comandos')
        self.pantalla = window
        self.reloj = time.Clock()
        self.datos = Datos()
        self.ajustes = self.datos.ajustes
        self.sonidos = Sonidos(self.ajustes)
        self.base_raqueta = cargar_base('racket.png')
        if not self.ajustes['angulo_listo']:
            # la primera vez, endereza las raquetas automaticamente
            self.ajustes['angulo'] = angulo_auto(self.base_raqueta)
            self.ajustes['angulo_listo'] = True
            self.datos.guardar()
        self.cache_tinte = {}
        self.img_raqueta = None
        self.reconstruir_raquetas()
        self.fondo = Fondo(self.ajustes['tema'])
        self.demo = DemoFondo()
        self.torneo = None
        self.corriendo = True
        self.pendiente = None
        self.fade_dir = 0
        self.fade_alpha = 0
        self.velo = Surface((ANCHO, ALTO))
        self.velo.fill((0, 0, 0))
        self.escenas = {
            'titulo': EscenaTitulo(self), 'menu': EscenaMenu(self), 'seleccion': EscenaSeleccion(self),
            'opciones': EscenaOpciones(self), 'controles': EscenaControles(self),
            'records': EscenaRecords(self), 'torneo': EscenaTorneo(self),
            'juego': EscenaJuego(self), 'fin': EscenaFin(self),
        }
        self.actual = self.escenas['titulo']
        self.actual.entrar()

    @property
    def tema(self):
        return TEMAS.get(self.ajustes['tema'], TEMAS['CIELO'])

    def crear_cfg(self, modo, rival, nivel=None, puntos=None, torneo=False, etapa=0):
        a = self.ajustes
        return {'modo': modo, 'rival': rival,
                'nivel': a['dificultad'] if nivel is None else nivel,
                'puntos': a['puntos'] if puntos is None else puntos,
                'torneo': torneo, 'etapa': etapa}

    def reconstruir_raquetas(self):
        # aplica el angulo actual y guarda una copia PNG con fondo transparente
        self.img_raqueta = hacer_imagen_raqueta(self.base_raqueta, self.ajustes['angulo'])
        self.cache_tinte = {}
        try:
            image.save(self.img_raqueta, os.path.join(CARPETA, 'racket_transparente.png'))
        except Exception:
            pass

    def imagen_raqueta(self, jugador):
        if not self.ajustes['tinte']:
            return self.img_raqueta
        clave = (jugador, self.ajustes['tema'])
        if clave not in self.cache_tinte:
            color = mezclar_color((255, 255, 255), self.tema['j1' if jugador == 1 else 'j2'], 0.7)
            img = self.img_raqueta.copy()
            img.fill(color, special_flags=BLEND_RGB_MULT)
            self.cache_tinte[clave] = img
        return self.cache_tinte[clave]

    def ir_a(self, nombre, **datos):
        if self.fade_dir != 0:
            return
        self.pendiente = (nombre, datos)
        self.fade_dir = 1

    def salir(self):
        self.corriendo = False

    def avanzar_fade(self):
        if self.fade_dir == 1:
            self.fade_alpha = min(255, self.fade_alpha + 30)
            if self.fade_alpha >= 255:
                nombre, datos = self.pendiente
                self.pendiente = None
                self.actual = self.escenas[nombre]
                self.actual.entrar(**datos)
                self.fade_dir = -1
        elif self.fade_dir == -1:
            self.fade_alpha = max(0, self.fade_alpha - 30)
            if self.fade_alpha <= 0:
                self.fade_dir = 0

    def ejecutar(self):
        while self.corriendo:
            for ev in event.get():
                if ev.type == QUIT:
                    self.corriendo = False
                elif self.fade_dir == 0:
                    self.actual.evento(ev)
            self.actual.actualizar()
            self.avanzar_fade()
            self.actual.dibujar(self.pantalla)
            if self.fade_alpha > 0:
                self.velo.set_alpha(self.fade_alpha)
                self.pantalla.blit(self.velo, (0, 0))
            display.update()
            self.reloj.tick(FPS_OBJETIVO)
        self.datos.guardar()
        quit()


if __name__ == '__main__':
    App().ejecutar()