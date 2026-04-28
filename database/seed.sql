-- ============================================
-- CAPTCHA v2 — Données initiales
-- ============================================

USE captcha_db;

-- Insérer les classes
INSERT INTO classes (nom, label_fr) VALUES
    ('car',   'voiture'),
    ('bus',  'bus'),
    ('truck', 'camion'),
    ('motorcycle', 'moto'),
    ('bicycle', 'vélo'),
    ('fire_hydrant', 'hydrant'),
    ('stop_sign', 'panneau de stop'),
    ('traffic_light', 'feu de circulation');
    