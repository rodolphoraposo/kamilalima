-- database_setup.sql

-- 1. CRIAÇÃO DA TABELA DE SERVIÇOS (Necessária para a 3ª Forma Normal e para o Frontend)
CREATE TABLE IF NOT EXISTS `servicos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(100) NOT NULL UNIQUE,
  `descricao` TEXT,
  `preco` DECIMAL(6, 2) NOT NULL,
  `duracao_minutos` INT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. CRIAÇÃO DA TABELA DE USUÁRIOS (Necessária para o Login e JWT)
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `senha_hash` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. ADAPTAÇÃO DA TABELA AGENDAMENTOS
-- Remove o campo `servico_nome` (redundante na 3FN)
-- Adiciona a FK `servico_id`
-- Adapta a coluna de data para a que está sendo usada no app.py (data_registro)
-- Renomeia a coluna status para ENUM completo
-- NOTA: O dump fornecido usa 'data_criacao', vamos manter o 'data_registro' usado no código Python para consistência.

-- Se a tabela `agendamentos` já existir (do seu dump):
ALTER TABLE `agendamentos`
  DROP COLUMN `servico_nome`,
  ADD COLUMN `servico_id` INT,
  MODIFY COLUMN `status` ENUM('PENDENTE','APROVADO','CANCELADO') DEFAULT 'PENDENTE',
  CHANGE COLUMN `data_criacao` `data_registro` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  ADD CONSTRAINT `fk_servico`
    FOREIGN KEY (`servico_id`) REFERENCES `servicos` (`id`);


-- 4. DADOS INICIAIS DA TABELA SERVICOS
INSERT INTO `servicos` (`nome`, `descricao`, `preco`, `duracao_minutos`) VALUES 
('Corte de Cabelo', 'Corte e finalização básica.', 50.00, 45),
('Escova Simples', 'Lavagem e escova rápida.', 40.00, 30),
('Manicure + Pedicure', 'Tratamento completo das unhas.', 70.00, 60),
('Coloração', 'Coloração completa dos fios. (Não inclui retoque)', 120.00, 90);

-- O teste de integração Pytest precisa do 'Corte de Teste' para rodar, vamos garantir que ele esteja aqui.
INSERT INTO `servicos` (`nome`, `descricao`, `preco`, `duracao_minutos`) VALUES 
('Corte de Teste', 'Serviço temporário para testes da API', 30.00, 30);