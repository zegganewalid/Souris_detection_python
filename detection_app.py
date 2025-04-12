import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog
import threading

class HandControllerApp:
    """
    Application qui utilise les gestes de la main pour contrôler l'ordinateur
    et lancer des applications.
    """
    def __init__(self):
        # Configuration pour la détection des mains
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,                  # Une seule main à la fois
            min_detection_confidence=0.7,     # Confiance en la détection
            min_tracking_confidence=0.7       # Confiance en le suivi
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Variables pour le suivi du mouvement et des gestes
        self.prev_hand_x, self.prev_hand_y = 0, 0
        self.smoothing = 6  # Plus élevé = plus fluide mais moins réactif
        self.gesture_cooldown = 0  # Temps d'attente entre les gestes
        self.cooldown_duration = 1.0  # Durée du cooldown en secondes
        
        # État de l'application
        self.is_running = True
        self.show_cursor = True
        
        # Dictionnaire des applications à lancer
        self.applications = {
            "✌️ V-SIGN": {"name": "Navigateur", "command": self.open_browser},
            "👍 LIKE": {"name": "Bloc-notes", "command": self.open_notepad},
            "👌 OK": {"name": "Calculatrice", "command": self.open_calculator},
            "🤙 CALL": {"name": "E-mail", "command": self.open_email},
            "👋 WAVE": {"name": "Fermer App", "command": self.close_current_app}
        }
        
        # Créer l'interface utilisateur
        self.create_ui()
    
    def create_ui(self):
        """
        Crée l'interface utilisateur avec la liste des applications configurées
        """
        # Créer la fenêtre principale
        self.root = tk.Tk()
        self.root.title("Contrôle par Gestes")
        self.root.geometry("300x400")
        self.root.resizable(False, False)
        
        # Style et apparence
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use('clam')
        
        # Titre
        title_label = tk.Label(self.root, text="Contrôle par Gestes", 
                              font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Frame pour les instructions
        instruction_frame = tk.Frame(self.root, bg="#f0f0f0")
        instruction_frame.pack(fill="x", padx=10, pady=5)
        
        instruction_label = tk.Label(instruction_frame, 
                                   text="Utilisez ces gestes pour contrôler votre ordinateur:",
                                   font=("Arial", 10), bg="#f0f0f0", justify="left", wraplength=280)
        instruction_label.pack(anchor="w")
        
        # Liste des gestes configurés
        gesture_frame = tk.Frame(self.root, bg="white", padx=10, pady=10, bd=1, relief="solid")
        gesture_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for gesture, app_info in self.applications.items():
            gesture_row = tk.Frame(gesture_frame, bg="white")
            gesture_row.pack(fill="x", pady=5)
            
            gesture_label = tk.Label(gesture_row, text=gesture, font=("Arial", 12), 
                                   bg="white", width=10, anchor="w")
            gesture_label.pack(side="left")
            
            app_label = tk.Label(gesture_row, text=app_info["name"], font=("Arial", 12), 
                               bg="white")
            app_label.pack(side="left", padx=10)
        
        # Boutons de contrôle
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = tk.Button(control_frame, text="Démarrer", command=self.start_camera,
                                    bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                    width=10, height=2)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(control_frame, text="Arrêter", command=self.stop_camera,
                                   bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                   width=10, height=2, state="disabled")
        self.stop_button.pack(side="right", padx=5)
        
        # Configurer la fermeture de l'application
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Aucune caméra active au démarrage
        self.cap = None
        self.camera_thread = None
    
    def on_closing(self):
        """
        Gère la fermeture propre de l'application
        """
        self.is_running = False
        # Attendre que le thread de la caméra se termine
        if self.camera_thread is not None and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        # Libérer les ressources
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Fermer la fenêtre Tkinter
        self.root.destroy()
    
    def start_camera(self):
        """
        Démarre la caméra dans un thread séparé
        """
        self.is_running = True
        
        # Initialiser la capture vidéo
        self.cap = cv2.VideoCapture(0)
        # Définir une résolution modérée
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Mettre à jour l'état des boutons
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Lancer le traitement de la caméra dans un thread séparé
        self.camera_thread = threading.Thread(target=self.process_camera)
        self.camera_thread.daemon = True
        self.camera_thread.start()
    
    def stop_camera(self):
        """
        Arrête la caméra
        """
        self.is_running = False
        
        # Attendre que le thread de la caméra se termine
        if self.camera_thread is not None:
            self.camera_thread.join(timeout=1.0)
        
        # Libérer les ressources
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Mettre à jour l'état des boutons
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def process_camera(self):
        """
        Traite les images de la caméra et détecte les gestes de la main
        """
        # Créer une fenêtre pour afficher le flux vidéo
        cv2.namedWindow("Hand Controller", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Hand Controller", 400, 300)
        
        while self.is_running and self.cap.isOpened():
            success, img = self.cap.read()
            if not success:
                print("Échec de la capture d'image")
                break
                
            # Redimensionner l'image pour un traitement plus rapide
            img = cv2.resize(img, (640, 480))
            
            # Inverser l'image horizontalement pour créer un effet miroir
            img = cv2.flip(img, 1)
            
            # Convertir l'image en RGB pour MediaPipe
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Traiter l'image avec MediaPipe
            results = self.hands.process(img_rgb)
            
            # Créer une image de fond pour les annotations
            img_copy = img.copy()
            
            # Si des mains sont détectées
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]  # Première main détectée
                
                # Dessiner les points clés de la main
                self.mp_drawing.draw_landmarks(
                    img_copy, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                # Détecter les gestes
                gesture = self.detect_gesture(hand_landmarks)
                
                # Vérifier le temps écoulé depuis le dernier geste
                current_time = time.time()
                if gesture and current_time - self.gesture_cooldown > self.cooldown_duration:
                    # Exécuter l'action associée au geste
                    if gesture in self.applications:
                        self.applications[gesture]["command"]()
                        # Afficher le nom du geste et l'action
                        gesture_text = f"{gesture} → {self.applications[gesture]['name']}"
                        cv2.putText(img_copy, gesture_text, (20, 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Mettre à jour le cooldown
                        self.gesture_cooldown = current_time
            
            # Ajouter du texte pour indiquer comment quitter
            cv2.putText(img_copy, "ESC pour quitter", (20, img_copy.shape[0] - 20),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Afficher l'image
            cv2.imshow("Hand Controller", img_copy)
            
            # Sortir si ESC est pressé
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
        
        # Nettoyer les ressources
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Mettre à jour l'état des boutons
        self.root.after(0, lambda: self.start_button.config(state="normal"))
        self.root.after(0, lambda: self.stop_button.config(state="disabled"))
    
    def detect_gesture(self, hand_landmarks):
        """
        Détecte les gestes spécifiques de la main
        
        Args:
            hand_landmarks: Points clés de la main détectés par MediaPipe
            
        Returns:
            String: Le geste détecté ou None
        """
        landmarks = hand_landmarks.landmark
        
        # Points des doigts
        thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]
        
        # Points intermédiaires des doigts
        thumb_ip = landmarks[self.mp_hands.HandLandmark.THUMB_IP]
        index_pip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_pip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_pip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_pip = landmarks[self.mp_hands.HandLandmark.PINKY_PIP]
        
        # Base des doigts (pour vérifier s'ils sont pliés)
        index_mcp = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        middle_mcp = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        ring_mcp = landmarks[self.mp_hands.HandLandmark.RING_FINGER_MCP]
        pinky_mcp = landmarks[self.mp_hands.HandLandmark.PINKY_MCP]
        
        # Point du poignet
        wrist = landmarks[self.mp_hands.HandLandmark.WRIST]
        
        # Calculer la distance entre le pouce et l'index pour le geste "OK"
        thumb_index_distance = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2 + 
            (thumb_tip.z - index_tip.z)**2
        )
        
        # Vérifier si un doigt est tendu (plus haut que son articulation)
        index_is_up = index_tip.y < index_pip.y
        middle_is_up = middle_tip.y < middle_pip.y
        ring_is_up = ring_tip.y < ring_pip.y
        pinky_is_up = pinky_tip.y < pinky_pip.y
        thumb_is_up = thumb_tip.y < thumb_ip.y
        
        # Geste V (index et majeur tendus, autres doigts fermés)
        if (index_is_up and middle_is_up and 
            not ring_is_up and not pinky_is_up):
            return "✌️ V-SIGN"
        
        # Geste "pouce en l'air" (Like)
        if (thumb_is_up and 
            not index_is_up and not middle_is_up and 
            not ring_is_up and not pinky_is_up):
            return "👍 LIKE"
        
        # Geste "OK" (pouce et index formant un cercle)
        if (thumb_index_distance < 0.05 and 
            middle_is_up and ring_is_up and pinky_is_up):
            return "👌 OK"
        
        # Geste "téléphone" (pouce et auriculaire tendus, autres fermés)
        if (thumb_is_up and not index_is_up and 
            not middle_is_up and not ring_is_up and pinky_is_up):
            return "🤙 CALL"
        
        # Geste "salut" (tous les doigts tendus et écartés)
        if (thumb_is_up and index_is_up and middle_is_up and 
            ring_is_up and pinky_is_up and 
            index_tip.x - pinky_tip.x > 0.2):  # Vérifier l'écartement
            return "👋 WAVE"
        
        return None
    
    # Méthodes pour lancer les applications
    def open_browser(self):
        """Ouvre le navigateur par défaut"""
        try:
            if os.name == 'nt':  # Windows
                os.system('start "" "http://www.google.com"')
            elif os.name == 'posix':  # macOS ou Linux
                os.system('open http://www.google.com')
        except Exception as e:
            print(f"Erreur lors de l'ouverture du navigateur: {e}")
    
    def open_notepad(self):
        """Ouvre le bloc-notes ou un éditeur de texte"""
        try:
            if os.name == 'nt':  # Windows
                os.system('start notepad')
            elif os.name == 'posix':  # macOS ou Linux
                if os.path.exists('/Applications/TextEdit.app'):  # macOS
                    os.system('open -a TextEdit')
                else:  # Linux
                    os.system('gedit')  # ou 'nano', 'vim', etc.
        except Exception as e:
            print(f"Erreur lors de l'ouverture du bloc-notes: {e}")
    
    def open_calculator(self):
        """Ouvre la calculatrice"""
        try:
            if os.name == 'nt':  # Windows
                os.system('start calc')
            elif os.name == 'posix':  # macOS ou Linux
                if os.path.exists('/Applications/Calculator.app'):  # macOS
                    os.system('open -a Calculator')
                else:  # Linux
                    os.system('gnome-calculator')  # ou autre calculatrice Linux
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la calculatrice: {e}")
    
    def open_email(self):
        """Ouvre le client email par défaut"""
        try:
            if os.name == 'nt':  # Windows
                os.system('start mailto:')
            elif os.name == 'posix':  # macOS ou Linux
                os.system('open mailto:')
        except Exception as e:
            print(f"Erreur lors de l'ouverture du client email: {e}")
    
    def close_current_app(self):
        """Ferme l'application au premier plan (sauf cette application)"""
        try:
            if os.name == 'nt':  # Windows
                # Simuler Alt+F4
                pyautogui.hotkey('alt', 'f4')
            elif os.name == 'posix':  # macOS ou Linux
                if os.path.exists('/usr/bin/xdotool'):  # Linux avec xdotool
                    os.system('xdotool getactivewindow windowkill')
                else:  # macOS
                    pyautogui.hotkey('command', 'q')
        except Exception as e:
            print(f"Erreur lors de la fermeture de l'application: {e}")
    
    def run(self):
        """Lance la boucle principale de l'application"""
        self.root.mainloop()

# Point d'entrée du programme
if __name__ == "__main__":
    app = HandControllerApp()
    app.run()