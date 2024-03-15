# Обработчик контекста
from .models import SubRubric

def board_context_processor(request):
    context = {}
    context['rubrics'] = SubRubric.objects.all() # Список Подрубрик помещается в переменную rubrics контекста шаблона
    # Реализация корректного возврата
    context['keyword'] = ''
    context['all'] = ''
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            context['keyword'] = '?keyword=' + keyword
            context['all'] = context['keyword']
    if 'page' in request.GET:
        page = request.GET['page']
        if page != '1':
            if context['all']:
                context['all'] += '&page=' + page
            else:
                context['all'] = '?page=' + page
    return context
