import cv2
import os
import numpy as np

USUARIOS_DIR = "usuarios"
TRAINER_FILE = "trainer.yml"
HAAR_CASCADE = "haarcascade_frontalface_default.xml"

face_detector = cv2.CascadeClassifier(HAAR_CASCADE)
if face_detector.empty():
    raise FileNotFoundError(f"Haar cascade file not found: {HAAR_CASCADE}")
recognizer = cv2.face.LBPHFaceRecognizer_create()

id_to_info = {}

def treinar_automaticamente():
    global id_to_info
    faces, ids = [], []
    next_id = 0
    id_to_info.clear()
    print(f"Procurando usuários em {USUARIOS_DIR}")
    for pasta_nome in os.listdir(USUARIOS_DIR):
        pasta_path = os.path.join(USUARIOS_DIR, pasta_nome)
        if not os.path.isdir(pasta_path):
            print(f"Ignorando {pasta_path} (não é uma pasta)")
            continue
        info_file = os.path.join(pasta_path, "info.txt")
        nivel = 1
        if os.path.exists(info_file):
            try:
                nivel = int(open(info_file, "r").read().strip())
                print(f"Usuário {pasta_nome} encontrado com nível {nivel}")
            except:
                print(f"Erro ao ler info.txt para {pasta_nome}, usando nível padrão 1")
                nivel = 1
        else:
            print(f"info.txt não encontrado para {pasta_nome}, usando nível padrão 1")
        next_id += 1
        id_to_info[next_id] = (pasta_nome, nivel)
        image_count = 1
        for arquivo in os.listdir(pasta_path):
            if not (arquivo.lower().endswith(".jpg") or arquivo.lower().endswith(".png")):
                print(f"Ignorando {arquivo} (não é .jpg ou .png)")
                continue
            old_img_path = os.path.join(pasta_path, arquivo)
            if any(ord(c) > 127 for c in arquivo):
                new_img_path = os.path.join(pasta_path, f"image_{image_count}.jpg")
                os.rename(old_img_path, new_img_path)
                img_path = new_img_path
                image_count += 1
            else:
                img_path = old_img_path
            gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                print(f"Falha ao ler {img_path}, pulando...")
                continue
            gray = cv2.equalizeHist(gray)
            gray = cv2.resize(gray, (200, 200))
            faces.append(gray)
            ids.append(next_id)
    if faces:
        recognizer.train(faces, np.array(ids))
        recognizer.save(TRAINER_FILE)
        print(f"Treinamento LBPH concluído com {len(ids)} imagens de {len(id_to_info)} usuários.")
    else:
        print("Nenhuma imagem encontrada para treinamento.")

# Forçar o treinamento ao iniciar
treinar_automaticamente()
if os.path.exists(TRAINER_FILE):
    recognizer.read(TRAINER_FILE)