from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def react_app(request, path=''):
    """
    View для отдачи React приложения.
    Ловит все пути и отдает один HTML файл.
    """
    context = {
        'user': request.user,
    }
    return render(request, 'react_app.html', context)