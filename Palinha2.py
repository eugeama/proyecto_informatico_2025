import pygame
import random
import cv2
import numpy as np
import time
import json
import os
from boton import Button

USE_MODEL = True

if USE_MODEL:
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model("keras_model.h5", compile=False)
        fake = np.zeros((1, 224, 224, 3), dtype=np.float32)
        model.predict(fake, verbose=0)
    except Exception as e:
        print("No se pudo cargar TensorFlow/modelo, usando modo fallback. Error:", e)
        USE_MODEL = False
        model = None
else:
    model = None

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Piedra, Papel o Demonio")
clock = pygame.time.Clock()

fontTitulo = pygame.font.Font('GROBOLD.ttf', 50)
fontGeneral = pygame.font.Font('Vaseline Extra.ttf', 40)
fontGeneralChiquita = pygame.font.Font('Vaseline Extra.ttf', 33)

BLUE_BG = (10, 26, 80)
BLACK_PANEL = (0, 0, 0)
WHITE = (255, 255, 255)

start_img = pygame.image.load('start_btn.png').convert_alpha()
exit_img = pygame.image.load('exit_btn.png').convert_alpha()
score_img = pygame.image.load('score.png').convert_alpha()  

start_button = Button(45, 340, start_img, 0.8)
exit_button_menu = Button(545, 340, exit_img, 0.8)
score_button = Button(250+45, 455, score_img, 0.8)
exit_button_game = Button(WIDTH - 130, HEIGHT - 70, exit_img, 0.4)
back_button = Button(325, 500, exit_img, 0.6)

leaderboard_file = "leaderboard.txt"
racha_actual = 0

def cargar_leaderboard():
    if not os.path.exists(leaderboard_file):
        return {}
    try:
        with open(leaderboard_file, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_leaderboard(data):
    with open(leaderboard_file, "w") as f:
        json.dump(data, f, indent=4)

leaderboard = cargar_leaderboard()

gestos = [
    "Tijera", "Piedra", "Papel", "Agua", "Desconocido", "Esponja", "Aire", "Demonio"
]
reglas = {
    "Tijera": ["Papel", "Esponja", "Demonio"],
    "Piedra": ["Tijera", "Demonio", "Esponja"],
    "Papel": ["Piedra", "Aire", "Agua"],
    "Agua": ["Demonio", "Tijera", "Piedra"],
    "Esponja": ["Aire", "Agua", "Papel"],
    "Aire": ["Tijera", "Agua", "Piedra"],
    "Demonio": ["Aire", "Esponja", "Papel"]
}

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def predecir_gesto(n_frames=3):
    if not cap.isOpened():
        return "?"
    if not USE_MODEL or model is None:
        return random.choice(gestos)
    preds = []
    for _ in range(n_frames):
        ret, f = cap.read()
        if not ret:
            continue
        img = cv2.resize(f, (224, 224))
        img = (img / 127.5) - 1.0
        preds.append(img.astype(np.float32))
    if not preds:
        return "?"
    batch = np.stack(preds, axis=0)
    mean_pred = np.mean(model.predict(batch, verbose=0), axis=0)
    idx = int(np.argmax(mean_pred))
    if idx >= len(gestos):
        return "Desconocido"
    return gestos[idx]

def cv2frame_to_pygame(f):
    f_rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    f_rgb = np.rot90(f_rgb)
    return pygame.surfarray.make_surface(f_rgb)

jugador = "?"
maquina = "?"
resultado = ""
countdown_active = False
countdown_ms = 3000
countdown_start_ticks = 0
game_active = False
show_score = False
ldb_input = False
running = True

while running:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLUE_BG)

    if not game_active and not show_score:
        if start_button.draw(screen):
            game_active = True
            countdown_active = False
        if exit_button_menu.draw(screen):
            running = False
        if score_button.draw(screen):
            show_score = True

        title = fontTitulo.render("Piedra Papel o Demonio", True, WHITE)
        screen.blit(title, (110, 130))

    elif show_score:
        title = fontTitulo.render("Leaderboard", True, WHITE)
        screen.blit(title, (230, 100))

        leaderboard = cargar_leaderboard()
        if leaderboard:
            sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (nombre, score) in enumerate(sorted_lb):
                entry = fontGeneral.render(f"{i+1}. {nombre}: {score}", True, (255, 215, 0))
                screen.blit(entry, (230, 200 + i * 50))
        else:
            text = fontGeneral.render("No hay registros aún", True, WHITE)
            screen.blit(text, (200, 250))

        if back_button.draw(screen):
            show_score = False

    elif game_active:
        pygame.draw.rect(screen, BLACK_PANEL, (0, 0, WIDTH, HEIGHT - 185))

        ret, frame = cap.read()
        if ret:
            try:
                camara = cv2frame_to_pygame(frame)
                camara = pygame.transform.scale(camara, (WIDTH-110, HEIGHT-205))
                screen.blit(camara, (WIDTH-750, 20))
            except Exception:
                pass

        pygame.draw.rect(screen, (2, 11, 37), (0, 415, WIDTH, 10))

        if exit_button_game.draw(screen):
            game_active = False
            jugador, maquina, resultado = "?", "?", ""

        if countdown_active:
            elapsed = pygame.time.get_ticks() - countdown_start_ticks
            remaining = max(0, countdown_ms - elapsed)
            sec = (remaining + 999) // 1000
            text = fontGeneral.render(str(sec), True, WHITE)
            screen.blit(text, (WIDTH - 420, HEIGHT - 150))
            if elapsed >= countdown_ms:
                countdown_active = False
                gestos_maquina = [g for g in gestos if g != "Desconocido"]
                maquina = random.choice(gestos_maquina)
                jugador = predecir_gesto(3)

                if jugador == "Desconocido":
                    resultado = "No se reconoció el gesto"
                elif jugador == maquina:
                    resultado = "Empate"
                elif maquina in reglas.get(jugador, []):
                    resultado = "Jugador GANA"
                    racha_actual += 1
                else:
                    resultado = "Máquina GANA"
                    if racha_actual > 0:
                        nombre = ""
                        input_active = True

                        input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 20, 300, 40)
                        font_input = pygame.font.Font(None, 50)

                        while input_active:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    cap.release()
                                    exit()

                                elif event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_RETURN:
                                        if nombre.strip():
                                            leaderboard = cargar_leaderboard()
                                            mejor_racha = leaderboard.get(nombre, 0)
                                            if racha_actual > mejor_racha:
                                                leaderboard[nombre] = racha_actual
                                                guardar_leaderboard(leaderboard)
                                        input_active = False  

                                    elif event.key == pygame.K_BACKSPACE:
                                        nombre = nombre[:-1]

                                    else:
                                        if len(nombre) < 15:  
                                            nombre += event.unicode

                            screen.fill((4, 22, 74))
                            texto = fontGeneral.render("Perdiste :( Ingresá tu nombre:", True, WHITE)
                            screen.blit(texto, (WIDTH // 2 - texto.get_width() // 2, HEIGHT // 2 - 100))

                            pygame.draw.rect(screen, WHITE, input_box, 2)
                            txt_surface = font_input.render(nombre, True, WHITE)
                            screen.blit(txt_surface, (input_box.x + 10, input_box.y + 5))

                            pygame.display.flip()  

                        screen.fill((4, 22, 74))
                        confirm = fontGeneral.render("Racha guardada ", True, WHITE)
                        screen.blit(confirm, (WIDTH // 2 - confirm.get_width() // 2, HEIGHT // 2))
                        pygame.display.flip()
                        pygame.time.wait(1500)

                        racha_actual = 0

        texto_jugador = fontGeneral.render(f"Tú: {jugador}", True, WHITE)
        texto_maquina = fontGeneral.render(f"Máquina: {maquina}", True, WHITE)
        texto_resultado = fontGeneral.render(resultado, True, WHITE)
        instruccion = fontGeneralChiquita.render("Presiona SPACE para jugar", True, WHITE)

        screen.blit(texto_jugador, (50, HEIGHT - 170))
        screen.blit(texto_maquina, (50, HEIGHT - 120))
        screen.blit(texto_resultado, (WIDTH - 280, HEIGHT - 150))
        screen.blit(instruccion, (20, HEIGHT - 60))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not countdown_active:
            countdown_active = True
            countdown_start_ticks = pygame.time.get_ticks()
            resultado = ""
            jugador = "?"
            maquina = "?"

    pygame.display.flip()

cap.release()
pygame.quit()