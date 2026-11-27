"""
Cover images for the projects and documents grids (escr_custom.covers).
Run with our settings:

    DJANGO_SETTINGS_MODULE=apps.escr_custom.settings python manage.py test escr_custom
"""
from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse
from easy_thumbnails.files import get_thumbnailer

from core.tests.factory import CoreFactoryTestCase
from escr_custom.covers.views import DOCUMENTS, PAGES, parse_ids


class ParseIdsTestCase(SimpleTestCase):

    def test_parse_ids(self):
        self.assertEqual(parse_ids('1, 2,x,,3'), [1, 2, 3])
        self.assertEqual(parse_ids(None), [])
        self.assertEqual(len(parse_ids(','.join(['1'] * 500))), 100)


class CoversTestCase(CoreFactoryTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.factory.make_user()
        self.project = self.factory.make_project(name='Covers', owner=self.user)
        self.client.force_login(self.user)

    def part(self, document):
        part = self.factory.make_part(document=document)
        get_thumbnailer(part.image).get_thumbnail(
            settings.THUMBNAIL_ALIASES['']['card'], generate=True)
        return part

    def covers(self, **params):
        response = self.client.get(reverse('custom-covers'), params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_document_pages(self):
        document = self.factory.make_document(owner=self.user, project=self.project)
        parts = [self.part(document) for _ in range(PAGES + 1)]
        empty = self.factory.make_document(owner=self.user, project=self.project)

        covers = self.covers(documents=f'{document.pk},{empty.pk}')['documents']
        self.assertEqual(len(covers[str(document.pk)]), PAGES)
        self.assertIn(parts[0].image.name, covers[str(document.pk)][0])
        self.assertEqual(covers[str(empty.pk)], [])

    def test_project_latest_documents(self):
        documents = [self.factory.make_document(owner=self.user, project=self.project)
                     for _ in range(DOCUMENTS + 1)]
        for document in documents:
            self.part(document)
        # the first one becomes the most recently updated
        documents[0].save()

        covers = self.covers(projects=str(self.project.pk))['projects']
        self.assertEqual(len(covers[str(self.project.pk)]), DOCUMENTS)

    def test_only_what_the_user_may_read(self):
        stranger = self.factory.make_user()
        theirs = self.factory.make_project(name='Theirs', owner=stranger)
        document = self.factory.make_document(owner=stranger, project=theirs)
        self.part(document)

        covers = self.covers(documents=str(document.pk), projects=str(theirs.pk))
        self.assertEqual(covers, {'documents': {}, 'projects': {}})

    def test_signed_in_only(self):
        self.client.logout()
        response = self.client.get(reverse('custom-covers'))
        self.assertIn(response.status_code, (401, 403))
