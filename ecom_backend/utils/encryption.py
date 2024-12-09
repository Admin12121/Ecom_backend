import base64
import json
from functools import wraps
from django.http import JsonResponse
from rest_framework.response import Response

def xor_encrypt_decrypt(data, key):
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(data, key * (len(data) // len(key) + 1)))

def encrypt_response(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        access_token = request.auth.token if hasattr(request.auth, 'token') else None
        if not access_token:
            return JsonResponse({'error': 'Access token not found'}, status=401)
        
        if isinstance(access_token, bytes):
            access_token = access_token.decode()
        
        try:
            key = access_token[:32]
            response = view_func(self, request, *args, **kwargs)
            
            if isinstance(response.data, dict):
                json_data = json.dumps(response.data)
                encrypted_data = xor_encrypt_decrypt(json_data, key)
                encoded_data = base64.b64encode(encrypted_data.encode()).decode()
                return Response({"data": encoded_data})
            
            return JsonResponse({'error': 'Invalid response data type'}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return wrapper