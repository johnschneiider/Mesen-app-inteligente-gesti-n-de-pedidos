from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.db.models import ProtectedError
from apps.core.mixins import BusinessOwnerRequiredMixin
from .models import DailyMenu, MenuIngredient, MenuPhoto
from .forms import DailyMenuForm, MenuIngredientForm, MenuPhotoForm


class MenuListView(BusinessOwnerRequiredMixin, View):
    template_name = 'menus/list.html'

    def get(self, request):
        menus = DailyMenu.objects.filter(business=request.user.business)
        return render(request, self.template_name, {'menus': menus, 'now': timezone.now()})


class MenuCreateView(BusinessOwnerRequiredMixin, View):
    template_name = 'menus/form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': DailyMenuForm(), 'action': 'Crear'})

    def post(self, request):
        form = DailyMenuForm(request.POST)
        if form.is_valid():
            menu = form.save(commit=False)
            menu.business = request.user.business
            menu.save()
            # handle photo upload
            if request.FILES.get('photo'):
                MenuPhoto.objects.create(menu=menu, image=request.FILES['photo'], order=0)
            # redirect to edit so ingredients/photos can be added immediately
            return redirect('menus:update', pk=menu.pk)
        return render(request, self.template_name, {'form': form, 'action': 'Crear'})


class MenuUpdateView(BusinessOwnerRequiredMixin, View):
    template_name = 'menus/form.html'

    def get(self, request, pk):
        menu = get_object_or_404(DailyMenu, pk=pk, business=request.user.business)
        return render(request, self.template_name, {
            'form': DailyMenuForm(instance=menu),
            'menu': menu,
            'action': 'Editar',
        })

    def post(self, request, pk):
        menu = get_object_or_404(DailyMenu, pk=pk, business=request.user.business)
        form = DailyMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'Menú guardado correctamente.')
            return redirect('menus:update', pk=menu.pk)
        return render(request, self.template_name, {
            'form': form, 'menu': menu, 'action': 'Editar'
        })


class MenuDeleteView(BusinessOwnerRequiredMixin, View):
    def post(self, request, pk):
        return self._delete(request, pk)

    def delete(self, request, pk):
        return self._delete(request, pk)

    def _delete(self, request, pk):
        menu = get_object_or_404(DailyMenu, pk=pk, business=request.user.business)
        try:
            menu.delete()
        except ProtectedError:
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    'No se puede eliminar: este menú tiene pedidos asociados.',
                    status=409,
                    content_type='text/plain',
                )
            from django.contrib import messages
            messages.error(request, 'No se puede eliminar este menú porque tiene pedidos asociados.')
            return redirect('menus:list')
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        return redirect('menus:list')


class AddMenuPhotoView(BusinessOwnerRequiredMixin, View):
    template_name = 'menus/partials/photos.html'

    def post(self, request, pk):
        menu = get_object_or_404(DailyMenu, pk=pk, business=request.user.business)
        if request.FILES.get('image'):
            order = menu.photos.count()
            MenuPhoto.objects.create(menu=menu, image=request.FILES['image'], order=order)
        return render(request, self.template_name, {'menu': menu})


class AddIngredientView(BusinessOwnerRequiredMixin, View):
    template_name = 'menus/partials/ingredients.html'

    def post(self, request, pk):
        menu = get_object_or_404(DailyMenu, pk=pk, business=request.user.business)
        form = MenuIngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.menu = menu
            ingredient.order = menu.ingredients.count()
            ingredient.save()
        return render(request, self.template_name, {'menu': menu})


class RemoveIngredientView(BusinessOwnerRequiredMixin, View):
    def delete(self, request, pk):
        ingredient = get_object_or_404(MenuIngredient, pk=pk, menu__business=request.user.business)
        ingredient.delete()
        return HttpResponse('')
