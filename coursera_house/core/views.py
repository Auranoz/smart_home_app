from django.urls import reverse_lazy
from django.views.generic import FormView

from .models import Setting
from .form import ControllerForm

from .request_mixin import get_request, post_request


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')

    def get_context_data(self, **kwargs):
        api_data = get_request()
        # Это сработает только если в базе УЖЕ есть объекты
        bedroom_t = Setting.objects.get(controller_name='bedroom_target_temperature')
        water_t = Setting.objects.get(controller_name='hot_water_target_temperature')

        self.initial = {
            "bedroom_target_temperature": bedroom_t.value,
            "hot_water_target_temperature": water_t.value,
            "bedroom_light": api_data["bedroom_light"],
            "bathroom_light": api_data["bathroom_light"],
        }
        context = super(ControllerView, self).get_context_data()
        context["data"] = api_data
        return context

    def form_valid(self, form):
        # Аналогично
        bedroom_t = Setting.objects.get(controller_name='bedroom_target_temperature')
        water_t = Setting.objects.get(controller_name='hot_water_target_temperature')

        bedroom_t.value = form.cleaned_data['bedroom_target_temperature']
        bedroom_t.save()
        water_t.value = form.cleaned_data['hot_water_target_temperature']
        water_t.save()

        # Мб нужна проверка на то, изменились ли данные после POST запроса или нет.
        post_data = [
            {'name': 'bedroom_light', 'value': form.cleaned_data['bedroom_light']},
            {'name': 'bathroom_light', 'value': form.cleaned_data['bathroom_light']}
        ]
        post_request(post_data)
        return super(ControllerView, self).form_valid(form)
