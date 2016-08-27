from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
	url(r'^$', hello.views.home, name='home'),
	url(r'^greeting', hello.views.index, name='index'),
	url(r'^db', hello.views.db, name='db'),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^auth/success', hello.views.auth_success, name='auth_success'),
	url(r'^auth', hello.views.auth, name='auth')
]
