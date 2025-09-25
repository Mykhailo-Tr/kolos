from django.apps import AppConfig


class LogisticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logistics'
    
    
    def ready(self):
        import logistics.signals 
        from .fake_weight_reader import FakeWeightReader
        reader = FakeWeightReader()
        reader.start()
        
        import sys
        sys.weight_reader = reader
