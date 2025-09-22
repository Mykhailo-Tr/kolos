from directory.models import Car, Driver, Trailer, Culture

TAG_FIELDS = {
    'car': (Car, 'number'),
    'driver': (Driver, 'full_name'),
    'trailer': (Trailer, 'number'),
    'culture': (Culture, 'name'),
}

def _normalize_fk_fields(post_data):
    """
    Приймає copy() POST (mutable QueryDict), перевіряє поля із TAG_FIELDS.
    Якщо значення не є існуючим PK -> створює/отримує об'єкт по lookup і підмінює значення на PK.
    Повертає post_data (mutated).
    """
    for field, (Model, lookup_field) in TAG_FIELDS.items():
        raw = post_data.get(field)
        if not raw:
            continue

        # Якщо пришло вже число — спробуємо трактувати як PK
        pk_candidate = None
        try:
            pk_candidate = int(raw)
        except (TypeError, ValueError):
            pk_candidate = None

        if pk_candidate:
            if Model.objects.filter(pk=pk_candidate).exists():
                # все гаразд — це PK
                continue
            else:
                # це число, але не PK (наприклад номер авто складається лише з цифр)
                # будемо трактувати як label і створити/отримати об'єкт по lookup_field
                obj, created = Model.objects.get_or_create(**{lookup_field: raw})
                post_data[field] = str(obj.pk)
        else:
            # raw не можна перетворити в int — це текстова мітка, створимо/отримаємо
            label = raw.sentry()
            obj, created = Model.objects.get_or_create(**{lookup_field: label})
            post_data[field] = str(obj.pk)

    return post_data