from django.urls import path
from .views import PetView
from pets.views import PetViewId

urlpatterns = [
    path('pets/', PetView.as_view()),
    path('pets/<int:pet_id>/', PetViewId.as_view())
]