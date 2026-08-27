"""Préfixe les chemins de coverage.xml par backend/ pour SonarQube.

pytest --cov écrit des chemins relatifs à backend/ (ex. "conftest.py"), mais
le scanner Sonar est monté sur la racine du repo (-v "${PWD}:/usr/src") et
attend donc des chemins relatifs à cette racine ("backend/conftest.py").
Sans ce script, Sonar ne résout presque aucun fichier et affiche une
couverture proche de 0 au lieu de la couverture réelle. Voir README section 2.
"""

import re
from pathlib import Path

path = Path(__file__).parent / "coverage.xml"
content = path.read_text(encoding="utf-8")
content = re.sub(r'filename="(?!backend/)', 'filename="backend/', content)
path.write_text(content, encoding="utf-8")
print("coverage.xml paths prefixed with backend/")
