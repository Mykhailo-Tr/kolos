from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, FormView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.forms import modelformset_factory
from django.db.models import Count, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Balance, BalanceSnapshot, BalanceHistory
from .forms import BalanceForm, BalanceSnapshotForm, BalanceHistoryForm, EmptySnapshotForm
from .services import BalanceService


class BalanceListView(ListView):
    model = Balance
    template_name = 'balances/list.html'
    context_object_name = 'balances'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('place', 'culture')
        order = self.request.GET.get('order')
        allowed = ['place__name', '-place__name', 'culture__name', '-culture__name', 'balance_type', '-quantity', 'quantity']
        if order in allowed:
            return qs.order_by(order)
        return qs.order_by('place__name', 'culture__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page": "balances"
        })
        return context


class BalanceCreateView(CreateView):
    model = Balance
    form_class = BalanceForm
    template_name = 'balances/form.html'
    success_url = reverse_lazy('balance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запис створено')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            "page": "balances"
        })

        return context

class BalanceUpdateView(UpdateView):
    model = Balance
    form_class = BalanceForm
    template_name = 'balances/form.html'
    success_url = reverse_lazy('balance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запис оновлено')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "page": "balances"
        })

        return context


class BalanceDeleteView(DeleteView):
    model = Balance
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('balance_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.success_url

        context.update({
            "page": "balances"
        })

        return context


    def delete(self, request, *args, **kwargs):
        messages.warning(request, 'Запис видалено')
        return super().delete(request, *args, **kwargs)


# Snapshot views

class BalanceSnapshotListView(ListView):
    model = BalanceSnapshot
    template_name = 'balances/snapshot_list.html'
    context_object_name = 'snapshots'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            total_records=Count('history_records'), 
            total_quantity=Sum('history_records__quantity')
        )
        order = self.request.GET.get('order', '-snapshot_date')
        
        # Валідуємо параметр сортування
        allowed_orders = ['snapshot_date', '-snapshot_date', 
                         'total_records', '-total_records', 
                         'total_quantity', '-total_quantity']
        
        if order in allowed_orders:
            return qs.order_by(order)
        return qs.order_by('-snapshot_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Отримуємо поточне сортування або використовуємо за замовчуванням
        context['current_order'] = self.request.GET.get('order', '-snapshot_date')
        context.update({
            "page": "balanceshistory"
        })
        return context


class BalanceSnapshotCreateView(View):
    def post(self, request):
        description = request.POST.get('description', 'Ручне збереження')
        created_by = request.user.get_full_name() or request.user.username
        try:
            snapshot = BalanceService.create_snapshot(description=description, created_by=created_by)
            messages.success(request, f'Зліпок створено ({snapshot.total_records()} записів)')
        except Exception as e:
            messages.error(request, f'Помилка: {e}')
        return redirect('balance_snapshot_list')


class BalanceSnapshotDetailView(ListView):
    model = BalanceHistory
    template_name = 'balances/snapshot_detail.html'
    context_object_name = 'history_records'
    paginate_by = 50

    def get_queryset(self):
        self.snapshot = get_object_or_404(BalanceSnapshot, pk=self.kwargs['pk'])
        queryset = BalanceHistory.objects.filter(snapshot=self.snapshot).select_related('place', 'culture')
        
        # Додаємо сортування
        order = self.request.GET.get('order', 'place__name')
        allowed_orders = ['place__name', '-place__name', 'culture__name', '-culture__name', 
                         'balance_type', '-balance_type', 'quantity', '-quantity']
        
        if order in allowed_orders:
            return queryset.order_by(order)
        return queryset.order_by('place__name', 'culture__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['snapshot'] = self.snapshot
        context['model_name'] = f"Зліпок від {self.snapshot.snapshot_date.strftime('%d.%m.%Y %H:%M')}"
        
        # Додаємо поля для сортування
        context['sortable_fields'] = {
            'place__name': 'Місце',
            'culture__name': 'Культура',
            'balance_type': 'Тип балансу',
            'quantity': 'Кількість (т)'
        }
        
        # Додаємо поточне сортування
        context['current_order'] = self.request.GET.get('order', 'place__name')
        
        # Додаємо total_records та total_quantity
        context['total_records_count'] = self.get_queryset().count()
        
        from django.db.models import Sum
        total_qty = self.get_queryset().aggregate(total=Sum('quantity'))['total'] or 0
        context['total_quantity'] = total_qty

        context.update({
            "page": "balanceshistory"
        })
        
        return context


class BalanceSnapshotUpdateView(View):
    def get(self, request, pk):
        snapshot = get_object_or_404(BalanceSnapshot, pk=pk)
        SnapshotFormSet = modelformset_factory(BalanceHistory, form=BalanceHistoryForm, extra=0, can_delete=True)
        
        # Отримуємо параметр сортування
        order = request.GET.get('order', 'place__name')
        allowed_orders = ['place__name', '-place__name', 'culture__name', '-culture__name', 
                         'balance_type', '-balance_type', 'quantity', '-quantity']
        
        # Застосовуємо сортування до queryset
        queryset = BalanceHistory.objects.filter(snapshot=snapshot).select_related('place', 'culture')
        if order in allowed_orders:
            queryset = queryset.order_by(order)
        else:
            queryset = queryset.order_by('place__name', 'culture__name')
        
        formset = SnapshotFormSet(queryset=queryset)
        form = BalanceSnapshotForm(instance=snapshot)
        
        context = {
            'snapshot': snapshot,
            'formset': formset,
            'snapshot_form': form,
            'model_name': f"Редагування зліпку від {snapshot.snapshot_date.strftime('%d.%m.%Y %H:%M')}",
            'current_order': order,
        }
        
        context.update({
            "page": "balanceshistory"
        })

        return render(request, 'balances/snapshot_edit_full.html', context)

    def post(self, request, pk):
        snapshot = get_object_or_404(BalanceSnapshot, pk=pk)
        SnapshotFormSet = modelformset_factory(BalanceHistory, form=BalanceHistoryForm, extra=0, can_delete=True)
        
        # Отримуємо параметр сортування для контексту
        order = request.GET.get('order', 'place__name')
        
        formset = SnapshotFormSet(request.POST, queryset=BalanceHistory.objects.filter(snapshot=snapshot))
        form = BalanceSnapshotForm(request.POST, instance=snapshot)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            for inst in instances:
                inst.snapshot = snapshot
                inst.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Зліпок оновлено')
            return redirect('balance_snapshot_detail', pk=snapshot.pk)
        
        messages.error(request, 'Помилка при збереженні')
        
        context = {
            'snapshot': snapshot,
            'formset': formset,
            'snapshot_form': form,
            'model_name': f"Редагування зліпку від {snapshot.snapshot_date.strftime('%d.%m.%Y %H:%M')}",
            'current_order': order,
        }
        
        return render(request, 'balances/snapshot_edit_full.html', context)


class BalanceSnapshotDeleteView(DeleteView):
    model = BalanceSnapshot
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('balance_snapshot_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.success_url

        context.update({
            "page": "balanceshistory"
        })

        return context

    def delete(self, request, *args, **kwargs):
        messages.warning(request, 'Зліпок видалено')
        return super().delete(request, *args, **kwargs)


class BalanceHistoryCreateView(CreateView):
    model = BalanceHistory
    form_class = BalanceHistoryForm
    template_name = 'balances/snapshot_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.snapshot = get_object_or_404(BalanceSnapshot, pk=self.kwargs['snapshot_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['snapshot'] = self.snapshot  # Додаємо snapshot до контексту
        context['model_name'] = f"Додати запис до зліпку"
        return context

    def form_valid(self, form):
        form.instance.snapshot = self.snapshot
        messages.success(self.request, 'Запис додано')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('balance_snapshot_detail', kwargs={'pk': self.snapshot.pk})
    

class EmptySnapshotCreateView(LoginRequiredMixin, FormView):
    """Створення порожнього зліпка"""
    template_name = 'balances/empty_snapshot_create.html'
    form_class = EmptySnapshotForm
    success_url = reverse_lazy('balance_snapshot_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Створюємо порожній зліпок
        snapshot = form.save(commit=False)
        
        # Якщо користувач не ввів ім'я, використовуємо його ім'я
        if not snapshot.created_by:
            snapshot.created_by = self.request.user.get_full_name() or self.request.user.username
        
        snapshot.save()
        
        messages.success(
            self.request, 
            f'✅ Порожній зліпок "{snapshot.description or "без опису"}" створено! '
            f'Тепер ви можете додавати записи до нього.'
        )
        
        # Після створення переходимо на редагування цього зліпка
        return redirect('balance_snapshot_update', pk=snapshot.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            "page": "balanceshistory"
        })
        
        return context
    
    
class QuickEmptySnapshotCreateView(LoginRequiredMixin, View):
    """Швидке створення порожнього зліпка за поточною датою"""
    
    def post(self, request):
        description = request.POST.get('description', 'Новий порожній зліпок')
        created_by = request.user.get_full_name() or request.user.username
        
        snapshot = BalanceSnapshot.objects.create(
            snapshot_date=timezone.now(),
            description=description,
            created_by=created_by
        )
        
        messages.success(request, f'✅ Порожній зліпок створено! Додавайте записи.')
        return redirect('balance_snapshot_update', pk=snapshot.pk)