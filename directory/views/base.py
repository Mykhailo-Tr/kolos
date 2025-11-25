from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

class BaseListView(ListView):
    template_name = "directory/list.html"
    context_object_name = "items"
    paginate_by = 10  # пагінація — опціонально

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model = self.model
        fields = [f for f in model._meta.fields if f.name != "id"]

        # формуємо список рядків для таблиці
        rows = []
        for obj in context["items"]:
            values = []
            for f in fields:
                # якщо є choices 
                if f.choices:
                    display_method = f"get_{f.name}_display"
                    value = getattr(obj, display_method)()
                else:
                    value = getattr(obj, f.name, "")
                values.append(value)
                
            row = {
                "object": obj,
                "values": values,
                "update_url": reverse_lazy(f"{model._meta.model_name}_update", args=[obj.pk]),
                "delete_url": reverse_lazy(f"{model._meta.model_name}_delete", args=[obj.pk]),
            }
            rows.append(row)
            
        context.update({
            "model_verbose": model._meta.verbose_name_plural,
            "fields": fields,
            "rows": rows,  # ← ось це важливо!
            "create_url": reverse_lazy(f"{model._meta.model_name}_create"),
            "page": model._meta.model_name + "s",
        })
        return context



class BaseFormViewMixin:
    """Міксин для Create/Update — спільна логіка"""
    template_name = "directory/form.html"
    success_message = "Операцію виконано успішно."

    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model = self.model._meta    
        context["model_name"] = model.verbose_name
        context["cancel_url"] = reverse_lazy(f"{model.model_name}_list")
        if isinstance(self, CreateView):
            context["title"] = f"Додати {model.verbose_name}"
        else:
            context["title"] = f"Редагувати {model.verbose_name}"
        
        context["page"] = f"{self.model._meta.model_name}s"
        return context


class BaseCreateView(BaseFormViewMixin, CreateView):
    """Створення запису"""
    pass


class BaseUpdateView(BaseFormViewMixin, UpdateView):
    """Оновлення запису"""
    pass


class BaseDeleteView(DeleteView):
    template_name = "confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model = self.model._meta
        context["model_name"] = model.verbose_name
        context["cancel_url"] = reverse_lazy(f"{model.model_name}_list")
        context["title"] = f"Видалити {model.verbose_name}"
        context["page"] = f"{self.model._meta.model_name}s"
        return context

    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")
    