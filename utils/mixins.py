# utils/mixins.py
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class PaginationMixin:
    """
    Додає стандартну пагінацію до будь-якого ListView.
    Використовує `paginate_by` у в'юсі або 20 за замовчуванням.
    """

    paginate_by = 20  # стандартна кількість елементів на сторінку
    page_kwarg = "page"  # GET-параметр для номера сторінки

    def get_paginate_by(self, queryset):
        """Повертає кількість елементів на сторінку"""
        return getattr(self, "paginate_by", 20)

    def paginate_queryset(self, queryset, page_size):
        """
        Повертає кортеж: (пагінований queryset, сторінка об'єктів, сторінка номер, is_paginated)
        """
        paginator = Paginator(queryset, page_size)
        page = self.request.GET.get(self.page_kwarg)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get(self.context_object_name, [])
        page_size = self.get_paginate_by(queryset)
        paginator, page_obj, object_list, is_paginated = self.paginate_queryset(queryset, page_size)

        context[self.context_object_name] = object_list
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["is_paginated"] = is_paginated
        return context
