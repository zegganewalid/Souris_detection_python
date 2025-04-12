# Application de Contrôle par Gestes de Main

## Description
Cette application vous permet d'utiliser les gestes de votre main pour ouvrir rapidement différentes applications sur votre ordinateur. Une petite fenêtre affiche le flux de votre webcam, détecte vos gestes et exécute les actions correspondantes.

## Fonctionnalités
- Interface simple avec une petite fenêtre de caméra
- Détection de 5 gestes différents pour contrôler l'ordinateur:
  - ✌️ V-SIGN: Ouvre le navigateur web
  - 👍 LIKE: Ouvre le bloc-notes
  - 👌 OK: Ouvre la calculatrice
  - 🤙 CALL: Ouvre le client email
  - 👋 WAVE: Ferme l'application active

## Prérequis
- Python 3.7 ou supérieur
- Une webcam fonctionnelle
- Les bibliothèques Python nécessaires (voir Installation)

## Installation

### 1. Installer les dépendances
```bash
pip install opencv-python mediapipe numpy pyautogui
```

### 2. Télécharger le fichier
Téléchargez le fichier `hand_controller_app.py`.

## Utilisation

### Lancement de l'application
```bash
python hand_controller_app.py
```

### Interface
1. L'application démarre avec une fenêtre principale affichant les commandes disponibles
2. Cliquez sur le bouton "Démarrer" pour activer la webcam
3. Une petite fenêtre s'ouvrira avec le flux vidéo de votre webcam
4. Faites les gestes avec votre main pour exécuter les commandes
5. Pour arrêter, cliquez sur "Arrêter" ou appuyez sur la touche ESC dans la fenêtre vidéo

### Gestes disponibles
- **✌️ V-SIGN** (index et majeur levés): Ouvre votre navigateur web
- **👍 LIKE** (pouce levé): Ouvre le bloc-notes
- **👌 OK** (pouce et index formant un cercle): Ouvre la calculatrice
- **🤙 CALL** (pouce et auriculaire levés): Ouvre votre client email
- **👋 WAVE** (main ouverte avec doigts écartés): Ferme l'application active

## Personnalisation

Vous pouvez facilement modifier les applications associées à chaque geste en éditant la section suivante dans le code:

```python
self.applications = {
    "✌️ V-SIGN": {"name": "Navigateur", "command": self.open_browser},
    "👍 LIKE": {"name": "Bloc-notes", "command": self.open_notepad},
    "👌 OK": {"name": "Calculatrice", "command": self.open_calculator},
    "🤙 CALL": {"name": "E-mail", "command": self.open_email},
    "👋 WAVE": {"name": "Fermer App", "command": self.close_current_app}
}
```

## Dépannage

### La webcam ne démarre pas
- Vérifiez que votre webcam fonctionne avec d'autres applications
- Assurez-vous qu'aucune autre application n'utilise déjà la webcam

### La détection des gestes ne fonctionne pas correctement
- Assurez-vous d'avoir un bon éclairage
- Tenez votre main à environ 30-60 cm de la caméra
- Faites des gestes clairs et précis
- Évitez les arrière-plans complexes ou similaires à la couleur de votre peau

## Remarques
- Pour de meilleures performances, utilisez cette application dans un environnement bien éclairé
- Gardez votre main dans le champ de vision de la caméra
- Si l'application devient lente, essayez de réduire la résolution de la caméra en modifiant les valeurs dans le code
