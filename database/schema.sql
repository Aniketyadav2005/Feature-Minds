-- ============================================================
-- Meme Hate Speech Detector — MySQL schema
-- Run this manually, OR let the FastAPI app auto-create tables
-- on startup via SQLAlchemy (app/database.py). This file is the
-- canonical DDL reference and is handy for production migrations.
-- ============================================================

CREATE DATABASE IF NOT EXISTS meme_detector
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE meme_detector;

CREATE TABLE IF NOT EXISTS analysis_results (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    filename            VARCHAR(255) NOT NULL,
    source              ENUM('upload', 'url') NOT NULL DEFAULT 'upload',
    timestamp           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    extracted_text      TEXT,
    caption             TEXT,

    label               ENUM('hate', 'nothate') NOT NULL,
    is_hate             BOOLEAN NOT NULL DEFAULT FALSE,
    hate_score          FLOAT NOT NULL DEFAULT 0,
    safe_score          FLOAT NOT NULL DEFAULT 0,
    category            VARCHAR(50) DEFAULT 'none',
    threshold_used      INT DEFAULT 50,

    image_path          VARCHAR(500),
    blurred_image_path  VARCHAR(500),
    has_image           BOOLEAN NOT NULL DEFAULT TRUE,

    INDEX idx_filename (filename),
    INDEX idx_timestamp (timestamp),
    INDEX idx_is_hate (is_hate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ground_truth (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    analysis_id   INT NOT NULL UNIQUE,
    label         ENUM('hate', 'safe') NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ground_truth_analysis
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
