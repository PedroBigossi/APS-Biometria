import cv2
import os
import random
from treinamento import face_detector, recognizer, id_to_info

USUARIOS_DIR = "usuarios"
NUM_FOTOS_CADASTRO = 60

def random_color(seed=None):
    random.seed(seed)
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def process_frame(frame, cadastrando, reconhecendo, count, pasta_atual, nome_atual, num_fotos_cadastro, id_colors):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)
    faces = [[x, y, w, h] for (x, y, w, h) in faces] if faces is not None else []

    if faces is not None:
        for face in faces:
            x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            face_img = frame[y:y+h, x:x+w]
            face_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            face_gray = cv2.equalizeHist(face_gray)
            face_gray = cv2.resize(face_gray, (200, 200))

            if cadastrando:
                count += 1
                cv2.imwrite(os.path.join(pasta_atual, f"{nome_atual}_{count}.jpg"), face_img)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"Capturando {count}/{num_fotos_cadastro}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            elif reconhecendo:
                id_predito, conf = recognizer.predict(face_gray)
                if conf < 70:
                    nome, nivel = id_to_info.get(id_predito, ("Desconhecido", 0))
                else:
                    nome, nivel = "Desconhecido", 0

                if id_predito not in id_colors:
                    id_colors[id_predito] = random_color(id_predito)
                color = id_colors[id_predito]
                cv2.putText(frame, f"{nome}", (x, y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                if nivel > 0:
                    cv2.putText(frame, f"Nível: {nivel}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    return frame, count, cadastrando