# -*- coding: utf-8 -*-
r"""test_escapes_validos.py — Ningun archivo del repo tiene un escape roto en una cadena.

Dos fallos distintos, y el peligroso es el segundo:

  1. ESCAPE INVALIDO ('\C' de SERVERHAF\COMPAC, '\All' de un flag IMAP, '\_' de una ruta).
     Python lo deja literal, asi que el VALOR es correcto — pero emite SyntaxWarning, y con
     `-W error::SyntaxWarning` ese aviso se convierte en SyntaxError. Eso no es teorico: cegaba
     el recorrido del arbol de imports del caso 7 de test_candado_destinatario.py, que dejaba
     de ver bill_payments.py y salia verde igual.

  2. ESCAPE VALIDO QUE SE COMIO UN CARACTER. Este NO AVISA. 'C:\blue5pl' vale 'C:\x08lue5pl':
     \b es un backspace y la 'b' desaparecio. El 06-sep-2026 habia tres —
     ops/reloj.py, scripts/_run_unseen.py (¡en el comando que viaja por SSH, o sea roto de
     verdad) y el docstring de scripts/rpa_viability_test.py, con un \r. Los tres se
     descubrieron POR CASUALIDAD: un escape invalido vecino en la misma cadena levanto la mano.
     Sin ese vecino habrian seguido ahi. Por eso el chequeo 2 existe aparte del 1.

Se incluyen los scratch `scripts/_*` que .gitignore mantiene fuera del repo: uno de los tres
bugs vivia justo ahi, y un comando SSH roto es igual de roto por no estar versionado.
Este docstring es RAW a proposito: habla de barras invertidas, y sin el prefijo r
las suyas propias se rompen. Este arnes se cazo a si mismo la primera vez que corrio.


    python scripts\test_escapes_validos.py
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import warnings
from pathlib import Path

def _raiz() -> Path:
    """Raiz a revisar. Tres fuentes, en orden, y ninguna adivina:

      1. --raiz RUTA        para auditar OTRO arbol sin copiar el arnes ahi.
      2. la raiz del repo   (git rev-parse --show-toplevel) — asi este archivo puede vivir
                            en scripts/, en ops/ o en la raiz misma sin que cambie que revisa.
      3. parent.parent      cuando no hay git (arbol sin versionar; el optimizador-logistico
                            es justo ese caso y sus 37 .py no los cubre ningun commit).

    El (2) existe porque este arnes ya vive en cinco repos con layouts distintos: fijar
    parent.parent obligaba a colocarlo siempre en scripts/, y el dia que alguien lo moviera
    revisaria un subarbol en vez del repo — en verde, y sin decirlo.
    """
    if "--raiz" in sys.argv:
        i = sys.argv.index("--raiz")
        if i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1]).resolve()
    aqui = Path(__file__).resolve().parent
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=aqui,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0 and r.stdout.strip():
        return Path(r.stdout.strip()).resolve()
    return aqui.parent


ROOT = _raiz()

# Codigo de TERCEROS: sus escapes rotos no los arreglamos aqui y ahogarian la senal.
# "site-packages/" y "dist-packages/" cubren cualquier venv se llame como se llame
# (".venv/" solo no basta: en el vault el arbol era "venv_test/lib/.../site-packages").
# "vendor/" es la convencion de librerias copiadas al arbol (wifi-radar/RuView/vendor).
EXCLUIR = ("graphify-out/", "node_modules/", ".venv/", "__pycache__/", "snapshot-",
           "site-packages/", "dist-packages/", "vendor/",
           "managed_components/")

# \a \b \v \f \r seguidos de letra/digito/_ = el escape se trago el inicio de un segmento.
# \n y \t quedan FUERA a proposito: son legitimos y comunes.
# Se exige ademas una barra en la misma cadena, para no marcar texto que use \r a proposito.
BS = chr(92)
# Dos niveles, medidos contra el repo entero (586 archivos, 0 falsos positivos):
#   DUROS: los que NINGUN texto de este proyecto usa a proposito. Se marcan donde sea.
#   El retorno de carro SI aparece legitimo (contenido .bat con CRLF), asi que solo se marca
#   cuando le sigue alfanumerico — la firma de haberse tragado el inicio de un segmento.
# La version estrecha exigia ademas una barra sobreviviente en la misma cadena, y por eso no
# vio el unico caso real que quedaba: la propia linea de registro de este arnes en
# run_arneses.py decia "el (backspace) no avisa" y ni el aviso ni el detector la cazaron.
DUROS = frozenset(chr(c) for c in (7, 8, 11, 12))        # a, b, v, f
CR_COMIDO = re.compile(chr(13) + "[A-Za-z0-9_]")

fallos: list[str] = []


def check(cond, etiqueta):
    print(("  OK   " if cond else "  FALLA ") + etiqueta)
    if not cond:
        fallos.append(etiqueta)


DESDE_GIT = "--desde-git" in sys.argv


def _staged():
    """Rutas .py con cambios EN EL INDICE (lo que de verdad se va a commitear)."""
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        return []
    return [l.strip() for l in r.stdout.splitlines() if l.strip().endswith(".py")]


def fuentes():
    """(ruta, codigo). Por defecto el repo entero desde disco.

    Con --desde-git, solo lo staged y leyendo del INDICE con `git show :ruta`, no del disco.
    La diferencia no es teorica: si alguien deja el defecto staged y lo arregla en el arbol
    de trabajo sin volver a hacer `git add`, mirar el disco daria verde y el defecto entraria
    al repo igual. Probado el 06-sep-2026: el hook sigue rechazando en ese escenario."""
    if DESDE_GIT:
        for rel in _staged():
            if any(x in rel for x in EXCLUIR):
                continue
            r = subprocess.run(["git", "show", ":" + rel], cwd=ROOT, capture_output=True,
                               encoding="utf-8", errors="replace", text=True)
            if r.returncode == 0:
                yield rel, r.stdout
        return
    anidados = _repos_anidados()
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if any(x in rel for x in EXCLUIR):
            continue
        if any(rel.startswith(a) for a in anidados):
            continue
        yield rel, p.read_text(encoding="utf-8", errors="replace")


def _repos_anidados() -> list[str]:
    """Prefijos de repos git ANIDADOS bajo ROOT, para no juzgar codigo ajeno.

    El vault (~/Documents/Proyectos) contiene repos completos de otros proyectos
    (portero-bot-hardware, IOCSA/envasado-liquidos-hardware). Sus .py no los commitea nadie
    desde aqui, asi que reportarlos aqui es ruido: ensucia el veredicto del vault con
    defectos que su propio gate tiene que cazar. Se detecta por la presencia de .git, no por
    una lista de nombres — una lista se queda vieja el dia que aparezca el siguiente.
    """
    fuera = []
    for g in ROOT.rglob(".git"):
        d = g.parent
        if d == ROOT:
            continue
        rel = d.relative_to(ROOT).as_posix()
        if any(x in rel + "/" for x in EXCLUIR):
            continue
        fuera.append(rel + "/")
    return fuera


def avisos_de(rel: str, src: str) -> list[tuple[int, str]]:
    """SyntaxWarning al compilar. Se compila (no ast.parse) para tener la linea REAL:
    ast.parse reporta '<unknown>:1' y eso mando media hora a buscar a ciegas."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            compile(src, rel, "exec")
        except SyntaxError:
            return []          # archivo roto: no es asunto de este arnes
    return [(x.lineno, str(x.message)) for x in w if issubclass(x.category, SyntaxWarning)]


def comidos_de(src: str) -> list[tuple[int, str]]:
    """Cadenas cuyo valor YA trae un caracter de control que se comio una letra."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            arbol = ast.parse(src)
        except SyntaxError:
            return []
    fuera = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if (DUROS & set(n.value)) or CR_COMIDO.search(n.value):
                fuera.append((n.lineno, repr(n.value)[:90]))
    return fuera


print("1. Ningun escape invalido (avisan, y escalados a error ciegan a otros arneses)")
malos = []
n_archivos = 0
for rel, src in fuentes():
    n_archivos += 1
    for ln, msg in avisos_de(rel, src):
        malos.append(f"{rel}:{ln} {msg}")
check(not malos, f"{n_archivos} archivos sin SyntaxWarning"
      + (" (solo lo staged)" if DESDE_GIT else ""))
for m in malos:
    check(False, "  " + m)

print("2. Ningun escape VALIDO comiendose una letra (este no avisa: hay que buscarlo)")
comidos = []
for rel, src in fuentes():
    for ln, val in comidos_de(src):
        comidos.append(f"{rel}:{ln} un escape valido se comio un caracter -> {val}")
check(not comidos, "ninguna cadena con control comido")
for c in comidos:
    check(False, "  " + c)

print("3. CANARIO: los dos detectores todavia disparan")
# Sin esto, un refactor que rompa el regex o el filtro de warnings deja este arnes en verde
# permanente — que es exactamente el modo de falla que el proyecto ya vio en H-01.
_canario_1 = 'x = "SERVER=SERVERHAF' + BS + 'COMPAC"\n'
_canario_2 = 'y = "C:' + BS + 'blue5pl' + BS + BS + 'HAF"\n'
check(bool(avisos_de("<canario>", _canario_1)), "detector 1 caza un escape invalido")
check(bool(comidos_de(_canario_2)), "detector 2 caza un backspace comiendose la 'b'")

print()
if fallos:
    print(f"FALLARON {len(fallos)}:")
    for f in fallos:
        print("  -", f)
    print()
    print("  Arreglo: duplicar la barra ('" + BS + BS + "C') o marcar la cadena como raw (r\"...\").")
    print("  Convencion del repo: barra duplicada — mony_contpaq_lib.py, bill_arranque_preflight.py.")
    sys.exit(1)
print("TODO EN VERDE")
