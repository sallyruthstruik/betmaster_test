"""betmaster_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from betmaster_test import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^api/callbacks/success/(?P<hash>\w+)$', view=views.redirect_success_callback, name="redirect_success_callback"),
    url(r'^api/callbacks/failure/(?P<hash>\w+)$', view=views.redirect_failure_callback, name="redirect_failure_callback"),

    url(r'^api/deposit/(?P<transaction_id>\d+)$', view=views.get_deposit_status, name="get_deposit_status"),
    url(r'^api/deposit/new', view=views.begin_deposit, name="begin_deposit"),
]
