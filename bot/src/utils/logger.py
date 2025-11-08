import logging
import sys
from datetime import datetime
from typing import Optional


class PerformanceLogger:
    """
    Класс для логирования производительности и отслеживания метрик
    """
    def __init__(self, name: str = "PerformanceLogger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Создаем форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Создаем обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        self.logger.addHandler(console_handler)
    
    def log_request(self, user_id: int, command: str, execution_time: float):
        """
        Логирует информацию о запросе пользователя
        """
        self.logger.info(f"User {user_id} executed command '{command}' in {execution_time:.3f}s")
    
    def log_db_operation(self, operation: str, collection: str, execution_time: float, success: bool = True):
        """
        Логирует операции с базой данных
        """
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DB operation '{operation}' on collection '{collection}' {status} in {execution_time:.3f}s")
    
    def log_error(self, error: Exception, context: str = ""):
        """
        Логирует ошибки с контекстом
        """
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """
        Логирует различные метрики производительности
        """
        unit_str = f" {unit}" if unit else ""
        self.logger.info(f"Performance metric - {metric_name}: {value}{unit_str}")


# Глобальный экземпляр логгера
perf_logger = PerformanceLogger()