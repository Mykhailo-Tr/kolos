
class WeightUnitMiddleware:
    """Middleware для збереження вибраної одиниці виміру."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ініціалізуємо одиницю виміру у сесії, якщо ще не задана
        if 'weight_unit' not in request.session:
            request.session['weight_unit'] = 'tons'  # дефолтне значення
        
        # Якщо в запиті передано зміну одиниці
        if request.method == 'GET' and 'weight_unit' in request.GET:
            weight_unit = request.GET.get('weight_unit')
            if weight_unit in ['tons', 'kg']:
                request.session['weight_unit'] = weight_unit
        
        response = self.get_response(request)
        return response
    
    def process_template_response(self, request, response):
        """Додає одиницю виміру до контексту всіх шаблонів."""
        if hasattr(response, 'context_data'):
            response.context_data['weight_unit'] = request.session.get('weight_unit', 'tons')
        return response