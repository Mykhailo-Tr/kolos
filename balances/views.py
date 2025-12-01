from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.forms import formset_factory, modelformset_factory
from .models import Balance, BalanceSnapshot, BalanceHistory
from .forms import BalanceForm, BalanceSnapshotForm, BalanceHistoryForm


class BalanceListView(ListView):
    model = Balance
    template_name = "balances/list.html"
    context_object_name = "balances"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().select_related("place", "culture")
        order = self.request.GET.get("order")
        valid_orders = [
            "id", "-id",
            "place__name", "-place__name",
            "culture__name", "-culture__name",
            "balance_type", "-balance_type",
            "quantity", "-quantity"
        ]
        if order in valid_orders:
            qs = qs.order_by(order)
        else:
            qs = qs.order_by("-id")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = "Журнал залишків"
        context["page"] = "balances"
        return context


class BalanceCreateView(CreateView):
    model = Balance
    form_class = BalanceForm
    template_name = "balances/form.html"
    success_url = reverse_lazy("balance_list")

    def form_valid(self, form):
        messages.success(self.request, "✅ Новий запис залишку успішно створено.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Помилка при створенні запису. Перевірте дані.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.verbose_name
        context["url_name"] = "balance"
        context["page"] = "balances"
        return context


class BalanceUpdateView(UpdateView):
    model = Balance
    form_class = BalanceForm
    template_name = "balances/form.html"
    success_url = reverse_lazy("balance_list")

    def form_valid(self, form):
        messages.success(self.request, "✅ Запис залишку оновлено успішно.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Не вдалося оновити запис.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.verbose_name
        context["url_name"] = "balance"
        context["page"] = "balances"
        return context


class BalanceDeleteView(DeleteView):
    model = Balance
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("balance_list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ Запис залишку успішно видалено.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["model_name"] = self.model._meta.verbose_name
        context["page"] = "balances"
        return context


# ===== ІСТОРІЯ ЗАЛИШКІВ =====

class BalanceSnapshotCreateView(View):
    """Створює новий зліпок залишків."""
    
    def post(self, request):
        description = request.POST.get('description', 'Ручне збереження')
        
        try:
            snapshot = Balance.create_snapshot(description=description)
            messages.success(
                request, 
                f"✅ Зліпок успішно створено! Збережено {snapshot.total_records()} записів."
            )
        except Exception as e:
            messages.error(request, f"❌ Помилка при створенні зліпку: {str(e)}")
        
        return redirect('balance_snapshot_list')


class BalanceSnapshotListView(ListView):
    model = BalanceSnapshot
    template_name = "balances/snapshot_list.html"
    context_object_name = "snapshots"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = "Історія залишків"
        context["page"] = "balanceshistory"
        return context


class BalanceSnapshotDetailView(ListView):
    model = BalanceHistory
    template_name = "balances/snapshot_detail.html"
    context_object_name = "history_records"
    paginate_by = 50

    def get_queryset(self):
        snapshot_id = self.kwargs['pk']
        return BalanceHistory.objects.filter(snapshot_id=snapshot_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot_id = self.kwargs['pk']
        context['snapshot'] = BalanceSnapshot.objects.get(pk=snapshot_id)
        context["model_name"] = "Деталі зліпку"
        context["page"] = "balanceshistory"
        return context


class BalanceSnapshotUpdateView(View):
    """Повне редагування зліпку з усіма записами."""
    
    def get(self, request, pk):
        snapshot = get_object_or_404(BalanceSnapshot, pk=pk)
        snapshot_form = BalanceSnapshotForm(instance=snapshot)
        
        # Створюємо formset для всіх історичних записів
        HistoryFormSet = modelformset_factory(
            BalanceHistory,
            form=BalanceHistoryForm,
            extra=0,
            can_delete=True
        )
        
        formset = HistoryFormSet(
            queryset=BalanceHistory.objects.filter(snapshot=snapshot).order_by('place_name', 'culture_name')
        )
        
        context = {
            'snapshot': snapshot,
            'snapshot_form': snapshot_form,
            'formset': formset,
            'model_name': 'Редагування зліпку',
            'page': 'balanceshistory',
        }
        
        return render(request, 'balances/snapshot_edit_full.html', context)
    
    def post(self, request, pk):
        snapshot = get_object_or_404(BalanceSnapshot, pk=pk)
        snapshot_form = BalanceSnapshotForm(request.POST, instance=snapshot)
        
        HistoryFormSet = modelformset_factory(
            BalanceHistory,
            form=BalanceHistoryForm,
            extra=0,
            can_delete=True
        )
        
        formset = HistoryFormSet(request.POST)
        
        if snapshot_form.is_valid() and formset.is_valid():
            # Зберігаємо зліпок
            snapshot_form.save()
            
            # Зберігаємо всі зміни в історичних записах
            instances = formset.save(commit=False)
            
            for instance in instances:
                instance.snapshot = snapshot
                instance.save()
            
            # Видаляємо позначені записи
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f"✅ Зліпок успішно оновлено! Оновлено {len(instances)} записів.")
            return redirect('balance_snapshot_detail', pk=snapshot.pk)
        else:
            messages.error(request, "❌ Помилка при збереженні. Перевірте введені дані.")
            
            context = {
                'snapshot': snapshot,
                'snapshot_form': snapshot_form,
                'formset': formset,
                'model_name': 'Редагування зліпку',
                'page': 'balanceshistory',
            }
            
            return render(request, 'balances/snapshot_edit_full.html', context)


class BalanceSnapshotDeleteView(DeleteView):
    model = BalanceSnapshot
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("balance_snapshot_list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ Зліпок залишків успішно видалено.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["model_name"] = "Зліпок залишків"
        context["page"] = "balanceshistory"
        return context


# ===== ДОДАВАННЯ НОВОГО ЗАПИСУ ДО ЗЛІПКУ =====

class BalanceHistoryCreateView(CreateView):
    """Додавання нового запису до існуючого зліпку."""
    model = BalanceHistory
    form_class = BalanceHistoryForm
    template_name = "balances/history_form.html"
    
    def get_success_url(self):
        return reverse_lazy('balance_snapshot_detail', kwargs={'pk': self.kwargs['snapshot_pk']})
    
    def form_valid(self, form):
        snapshot = get_object_or_404(BalanceSnapshot, pk=self.kwargs['snapshot_pk'])
        form.instance.snapshot = snapshot
        messages.success(self.request, "✅ Новий запис успішно додано до зліпку.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['snapshot'] = get_object_or_404(BalanceSnapshot, pk=self.kwargs['snapshot_pk'])
        context['model_name'] = 'Додати запис до зліпку'
        context['page'] = 'balanceshistory'
        return context