from rest_framework.response import Response
from rest_framework.views import APIView


def success_response(message, data=None, status_code=200):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


class HealthCheckView(APIView):
    def get(self, request):
        return success_response(
            message="NGO backend is running properly",
            data={
                "service": "ngo-backend",
                "status": "healthy",
            },
        )