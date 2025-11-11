"""
Отдельный файл для импорта VehicleDataService чтобы избежать циклических импортов
"""

def get_vehicle_data_service(user):
    """
    Функция для получения экземпляра VehicleDataService
    """
    from vehicles.services import VehicleDataService
    return VehicleDataService(user)