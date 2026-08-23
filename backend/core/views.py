from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.http import Http404


def frontend_view(request, path='index.html'):
    """Render frontend templates placed under templates/frontend/<name>.html.

    Examples:
    - GET /           -> templates/frontend/index.html
    - GET /login.html -> templates/frontend/login.html
    - GET /admin-dashboard.html -> templates/frontend/admin-dashboard.html
    """
    template_name = f'frontend/{path}'
    try:
        return render(request, template_name)
    except TemplateDoesNotExist:
        raise Http404()
