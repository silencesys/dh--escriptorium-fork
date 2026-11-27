"""
Cover images for the cards of the projects and documents grids: a few
pages of each document, and of each project the first page of its most
recently updated documents. Upstream's lists carry no image (api/views.py,
ProjectViewSet and DocumentViewSet), and a card is no reason to fetch every
document's parts.

    GET /api/custom/covers/?documents=1,2&projects=3
    {"documents": {"1": [url, ...], "2": []}, "projects": {"3": [url, ...]}}

Only what the user may read is answered (upstream's own managers decide);
the images are upstream's "card" thumbnails (180 x 180), made on upload.
"""
from django.conf import settings
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from easy_thumbnails.files import get_thumbnailer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Document, DocumentPart, Project

PAGES = 3  # of a document
DOCUMENTS = 4  # of a project
MAX_IDS = 100  # per kind, per request (a page of a list is 50)


def parse_ids(value):
    """'1,2,x' -> [1, 2]: the integers of a comma separated parameter."""
    ids = []
    for item in (value or '').split(','):
        item = item.strip()
        if item.isdigit():
            ids.append(int(item))
    return ids[:MAX_IDS]


def card(image):
    """The URL of an image's card thumbnail, or None if there is none (yet)."""
    try:
        thumbnail = get_thumbnailer(image).get_thumbnail(
            settings.THUMBNAIL_ALIASES['']['card'], generate=False)
        return thumbnail.url if thumbnail else None
    except (AttributeError, OSError, ValueError):
        return None


def first_pages(document_ids, count):
    """{document id: [card url, ...]}: the first `count` pages of each."""
    parts = (
        DocumentPart.objects
        .filter(document_id__in=document_ids)
        .annotate(rank=Window(RowNumber(), partition_by=F('document_id'),
                              order_by=F('order').asc()))
        .filter(rank__lte=count)
        .order_by('document_id', 'order')
        .only('pk', 'document_id', 'image')
    )
    covers = {pk: [] for pk in document_ids}
    for part in parts:
        url = card(part.image)
        if url:
            covers[part.document_id].append(url)
    return covers


def readable_documents(user):
    return Document.objects.for_user(user).values('pk')


def document_covers(user, ids):
    allowed = list(Document.objects.filter(pk__in=readable_documents(user))
                   .filter(pk__in=ids).values_list('pk', flat=True))
    return first_pages(allowed, PAGES)


def project_covers(user, ids):
    projects = list(Project.objects.for_user_read(user).filter(pk__in=ids)
                    .values_list('pk', flat=True).distinct())
    latest = (
        Document.objects
        .filter(pk__in=readable_documents(user), project_id__in=projects)
        .annotate(rank=Window(RowNumber(), partition_by=F('project_id'),
                              order_by=F('updated_at').desc()))
        .filter(rank__lte=DOCUMENTS)
        .order_by('project_id', 'rank')
        .values_list('pk', 'project_id')
    )
    latest = list(latest)
    pages = first_pages([pk for pk, _ in latest], 1)
    covers = {pk: [] for pk in projects}
    for document, project in latest:
        covers[project].extend(pages[document])
    return covers


class CoversView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response({
            'documents': document_covers(user, parse_ids(request.query_params.get('documents'))),
            'projects': project_covers(user, parse_ids(request.query_params.get('projects'))),
        })
