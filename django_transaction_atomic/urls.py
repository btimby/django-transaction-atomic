try:
    from django.conf.urls import patterns
    urlpatterns = patterns('')

except ImportError:
    urlpatterns = []
