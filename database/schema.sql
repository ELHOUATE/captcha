-- ============================================
-- CAPTCHA v2 — Schéma de base de données MySQL
-- ============================================

CREATE DATABASE IF NOT EXISTS captcha_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE captcha_db;

-- Table des classes (voiture, bateau, camion...)
CREATE TABLE IF NOT EXISTS classes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(50) NOT NULL UNIQUE,      -- ex: "car"
    label_fr    VARCHAR(50) NOT NULL,             -- ex: "voiture"
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des images avec labels YOLO
CREATE TABLE IF NOT EXISTS images (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    classe_id       INT NOT NULL,
    chemin          VARCHAR(255) NOT NULL,         -- ex: "car/img001.jpg"
    contient_objet  BOOLEAN NOT NULL,             -- True si YOLO a détecté l'objet
    confiance_yolo  FLOAT DEFAULT 0.0,            -- score de confiance YOLO (0-1)
    nb_objets       INT DEFAULT 0,                -- nombre d'objets détectés
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classe_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- Table des sessions CAPTCHA (tokens temporaires)
CREATE TABLE IF NOT EXISTS sessions (
    token       VARCHAR(36) PRIMARY KEY,           -- UUID
    classe_id   INT NOT NULL,
    image_ids   JSON NOT NULL,                    -- liste des 9 IDs images
    correctes   JSON NOT NULL,                    -- IDs des images correctes
    expires_at  DATETIME NOT NULL,
    utilise     BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classe_id) REFERENCES classes(id)
);

-- Table des tentatives (historique + anti-bot)
CREATE TABLE IF NOT EXISTS tentatives (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    token       VARCHAR(36),
    succes      BOOLEAN NOT NULL,
    score       FLOAT NOT NULL,                   -- ex: 0.75
    ip          VARCHAR(45),                      -- IPv4 ou IPv6
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les performances
CREATE INDEX idx_images_classe ON images(classe_id);
CREATE INDEX idx_images_objet  ON images(contient_objet);
CREATE INDEX idx_sessions_exp  ON sessions(expires_at);
CREATE INDEX idx_tentatives_ip ON tentatives(ip);