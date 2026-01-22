from pathlib import Path

VISITAS_FILE = Path("data/visitas.txt")

if VISITAS_FILE.exists():
    visitas = int(VISITAS_FILE.read_text())
else:
    visitas = 0

visitas += 1
VISITAS_FILE.write_text(str(visitas))

st.sidebar.metric("👀 Total de acessos", visitas)
