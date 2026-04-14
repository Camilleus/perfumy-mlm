from django.urls import path
from . import views

urlpatterns = [
    path('regulamin/', views.RegulaminView.as_view(), name='regulamin'),
    path('polityka-prywatnosci/', views.PrivacyPolicyView.as_view(), name='polityka_prywatnosci'),
    path('zwroty-reklamacje/', views.ReturnsPolicyView.as_view(), name='returns_policy'),
    path('odr/', views.OdrView.as_view(), name='odr'),
    path('omnibus/', views.OmnibusView.as_view(), name='omnibus'),
    path('kontakt/', views.ContactView.as_view(), name='contact'),
    path('kontakt/wyslij/', views.contact_submit, name='contact_submit'),
    path('odstapienie-formularz/wyslij/', views.withdrawal_submit, name='withdrawal_submit'),
]