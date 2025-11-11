# dashboard/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from vehicles.services import AutoGraphService
import logging

logger = logging.getLogger(__name__)


class DashboardDataAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """API для получения данных дашборда"""
        try:
            service = AutoGraphService()
            if service.login("demo", "demo"):
                schemas = service.get_schemas()

                if schemas:
                    first_schema = schemas[0]
                    schema_id = first_schema.get('ID')

                    dashboard_data = service.get_dashboard_summary(schema_id)

                    if dashboard_data:
                        return Response({
                            'success': True,
                            'data': dashboard_data,
                            'schema_name': first_schema.get('Name', 'Demo')
                        })

            return Response({
                'success': False,
                'error': 'Не удалось получить данные дашборда'
            }, status=500)

        except Exception as e:
            logger.error(f"Dashboard API error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class VehicleDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id):
        """API для получения детальной информации по ТС"""
        try:
            service = AutoGraphService()
            if service.login("demo", "demo"):
                schemas = service.get_schemas()

                if schemas:
                    schema_id = schemas[0].get('ID')
                    vehicle_data = service.get_vehicle_monitoring_data(schema_id, vehicle_id)

                    if vehicle_data:
                        return Response({
                            'success': True,
                            'data': vehicle_data
                        })

            return Response({
                'success': False,
                'error': 'Не удалось получить данные ТС'
            }, status=500)

        except Exception as e:
            logger.error(f"Vehicle detail API error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)