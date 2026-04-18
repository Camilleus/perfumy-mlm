from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from .models import BlogPost
import anthropic


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    return render(request, 'blog/list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog/detail.html', {'post': post})


@staff_member_required
def blog_generate(request):
    """Panel admina do generowania artykułów przez AI"""
    error = None
    success = None

    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        if not topic:
            error = 'Podaj temat artykułu.'
        else:
            try:
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                message = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=2000,
                    messages=[{
                        'role': 'user',
                        'content': f'''Napisz artykuł blogowy po polsku dla sklepu perfumeryjnego "Przystanek Perfumy".

Temat: {topic}

Wymagania:
- Długość: 400-600 słów
- Styl: ekspercki ale przystępny, ciepły, pasjonacki
- Zacznij od chwytliwego tytułu (pierwsza linia, bez "Tytuł:")
- Następnie zajawka (2-3 zdania, bez "Zajawka:")
- Następnie separator: ---
- Następnie pełna treść artykułu z akapitami
- Używaj naturalnego języka, wspominaj nuty zapachowe, okazje, emocje
- Nie używaj markdown (bez **, ##, itp.)
- Pisz tak jakbyś był pasjonatem perfum, nie marketingowcem

Format odpowiedzi:
[TYTUŁ]
[ZAJAWKA]
---
[TREŚĆ]'''
                    }]
                )

                raw = message.content[0].text.strip()
                lines = raw.split('\n')

                # Parsuj odpowiedź
                title = lines[0].strip()
                separator_idx = next((i for i, l in enumerate(lines) if l.strip() == '---'), 2)
                excerpt = ' '.join(lines[1:separator_idx]).strip()
                content = '\n'.join(lines[separator_idx+1:]).strip()

                post = BlogPost.objects.create(
                    title=title,
                    excerpt=excerpt,
                    content=content,
                )
                success = f'Artykuł "{title}" został wygenerowany!'

            except Exception as e:
                error = f'Błąd generowania: {str(e)}'

    posts = BlogPost.objects.all().order_by('-created_at')[:10]
    return render(request, 'blog/generate.html', {
        'error': error,
        'success': success,
        'posts': posts,
    })