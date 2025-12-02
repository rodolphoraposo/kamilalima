-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: kamilalima_agendamentos
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agendamentos`
--

DROP TABLE IF EXISTS `agendamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agendamentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_nome` varchar(100) NOT NULL,
  `cliente_whatsapp` varchar(20) DEFAULT NULL,
  `servico_nome` varchar(100) NOT NULL,
  `data_agendamento` date NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fim` time NOT NULL,
  `status` enum('PENDENTE','APROVADO','RECUSADO') DEFAULT 'PENDENTE',
  `data_criacao` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendamentos`
--

LOCK TABLES `agendamentos` WRITE;
/*!40000 ALTER TABLE `agendamentos` DISABLE KEYS */;
INSERT INTO `agendamentos` VALUES (1,'Teste Bloqueado','5582991112233','Escova Simples','2025-12-05','14:00:00','14:30:00','PENDENTE','2025-11-18 16:49:19'),(2,'Maria Rita Rapôso','82999887766','Escova Simples','2025-12-05','11:00:00','11:30:00','PENDENTE','2025-11-18 17:01:40'),(3,'Maria Rita Rapôso','82999887766','Corte de Cabelo','2025-12-05','09:00:00','09:45:00','PENDENTE','2025-11-18 17:15:10'),(4,'Maria Rita Rapôso','82999887766','Corte de Cabelo','2025-11-20','10:00:00','10:45:00','PENDENTE','2025-11-18 17:20:09'),(5,'Maria Rita Rapôso','82999887766','Corte de Cabelo','2025-11-20','13:30:00','14:15:00','PENDENTE','2025-11-18 17:21:05'),(6,'Maria Rita Rapôso','82999887766','Corte de Cabelo','2025-11-19','16:00:00','16:45:00','PENDENTE','2025-11-18 17:23:40'),(7,'Kamila','82999012358','Corte de Cabelo','2025-11-20','11:30:00','12:15:00','PENDENTE','2025-11-18 17:25:33'),(8,'Maria Rita Rapôso','82999887766','Corte de Cabelo','2025-11-19','16:00:00','16:45:00','PENDENTE','2025-11-18 17:31:12'),(9,'Maria Rita Rapôso','82999887766','Escova Simples','2025-12-05','13:30:00','14:00:00','APROVADO','2025-11-18 17:32:58'),(10,'Maria José','82999887766','Coloração','2025-11-21','10:00:00','11:30:00','APROVADO','2025-11-18 21:22:20'),(11,'Nome do Rapôso','5582991234567','Corte de Cabelo','2025-11-30','15:30:00','16:15:00','PENDENTE','2025-11-18 21:23:40'),(12,'Maria Rita Rapôso','82999887766','Manicure + Pedicure','2025-11-21','14:00:00','15:00:00','APROVADO','2025-11-18 21:25:17');
/*!40000 ALTER TABLE `agendamentos` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-18 21:32:14
