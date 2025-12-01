class WeightConverter:
    """Клас для конвертації одиниць ваги."""
    
    TON_TO_KG = 1000  # 1 тонна = 1000 кг
    KG_TO_TON = 0.001  # 1 кг = 0.001 тонни
    
    @classmethod
    def to_kilograms(cls, tons):
        """Конвертує тонни в кілограми."""
        if tons is None:
            return None
        return tons * cls.TON_TO_KG
    
    @classmethod
    def to_tons(cls, kilograms):
        """Конвертує кілограми в тонни."""
        if kilograms is None:
            return None
        return kilograms * cls.KG_TO_TON
    
    @classmethod
    def format_weight(cls, tons, unit='tons', decimal_places=3):
        """
        Форматує вагу у вибраних одиницях.
        
        Args:
            tons: значення в тонах
            unit: одиниця виміру ('tons' або 'kg')
            decimal_places: кількість знаків після коми
        """
        if tons is None:
            return ""
        
        if unit == 'kg':
            value = cls.to_kilograms(tons)
            suffix = " кг"
        else:
            value = tons
            suffix = " т"
        
        return f"{value:.{decimal_places}f}{suffix}"