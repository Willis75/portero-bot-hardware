# Cómo continuar en Claude Code

Todo el trabajo está en esta carpeta. Para seguir desde Claude Code:

## 1. Instalar Claude Code (si no lo tienes)
```bash
npm install -g @anthropic-ai/claude-code
```
(Requiere Node.js. Detalles: https://docs.claude.com/en/docs/claude-code)

## 2. Abrir el proyecto
Abre una terminal en esta carpeta y lanza Claude Code:
```bash
cd C:\Users\wumni\Documents\Proyectos\portero-bot-hardware
claude
```
Claude Code leerá automáticamente el archivo `CLAUDE.md` y tendrá todo el contexto
del proyecto (qué es, qué se hizo, qué falta).

## 3. Primer mensaje sugerido
Pega algo así para arrancar:

> Lee CLAUDE.md. Quiero terminar el rediseño del PCB en KiCad.
> Primero instala kicad-cli y corre el ERC sobre kicad/portero-bot-v2.kicad_sch
> para verificar la conectividad. Luego ayúdame con los pendientes 2–6 del CLAUDE.md.

## 4. Regenerar el esquemático (si haces cambios)
```bash
pip install kiutils openpyxl python-docx
python3 scripts/10_parse_edif.py
python3 scripts/20_build_master.py
python3 scripts/30_gen_schematic.py
```

## 5. Verificar de verdad la conectividad (lo que aquí no se pudo)
Claude Code puede instalar KiCad en tu máquina y correr:
```bash
kicad-cli sch erc kicad/portero-bot-v2.kicad_sch        # chequeo eléctrico
kicad-cli sch export netlist kicad/portero-bot-v2.kicad_sch   # exportar netlist
```

## Nota
- No hay una "exportación" automática del historial de este chat a Claude Code;
  lo que se transfiere es el proyecto (estos archivos), que es lo que importa.
- El `CLAUDE.md` cumple esa función: le da a Claude Code el contexto para continuar
  justo donde lo dejamos.
- Para guardar el avance en git:
  ```bash
  git add .
  git commit -m "Migración Flux→KiCad: esquemático reconstruido + scripts + revisión"
  ```
