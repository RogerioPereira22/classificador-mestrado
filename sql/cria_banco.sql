-- Moradores

USE bmk6y39nfvstjjc20lge;
CREATE TABLE Morador (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    documento VARCHAR(20) -- CPF, RG, etc
);

-- Localidades (Casas, apartamentos, etc)
CREATE TABLE Localidade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    morador_id INT NOT NULL,
    descricao VARCHAR(100), -- Ex: "Casa Principal", "Apto 101"
    endereco VARCHAR(200),
    FOREIGN KEY (morador_id) REFERENCES Morador(id)
);

-- Cômodos
CREATE TABLE Comodo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    localidade_id INT NOT NULL,
    nome VARCHAR(100), -- Ex: "Sala", "Quarto"
    FOREIGN KEY (localidade_id) REFERENCES Localidade(id)
);

-- Câmeras
CREATE TABLE Camera (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comodo_id INT NOT NULL,
    identificador VARCHAR(100), -- Serial, MAC, ou IP
    status ENUM('ligada', 'desligada') DEFAULT 'ligada',
    FOREIGN KEY (comodo_id) REFERENCES Comodo(id)
);

-- Classe de movimento (padronizada)
CREATE TABLE ClasseMovimento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) -- Ex: "Baixa", "Média", "Alta"
);

-- Consolidado de métricas por frame
CREATE TABLE FrameMetrica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id INT NOT NULL,
    frame_num INT NOT NULL,
    tempo_medio FLOAT,
    media_geral FLOAT,
    tamanho_pacote INT,
    classe_movimento_id INT, -- pode ser NULL se não classificado
    perda_pacote FLOAT,
    foi_reclassificado BOOLEAN DEFAULT 0,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES Camera(id),
    FOREIGN KEY (classe_movimento_id) REFERENCES ClasseMovimento(id)
);

-- Alertas (opcional, para câmeras com problemas)
CREATE TABLE Alerta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id INT,
    tipo VARCHAR(50), -- Ex: 'PERDA_PACOTE', 'NAO_CLASSIFICADA'
    descricao VARCHAR(200),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES Camera(id)
);
