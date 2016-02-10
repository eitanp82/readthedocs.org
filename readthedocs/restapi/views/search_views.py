import logging

from django.http import Http404
from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.search.indexes import PageIndex, ProjectIndex, SectionIndex
from readthedocs.search.lib import search_file, search_project, search_section
from readthedocs.restapi import utils


log = logging.getLogger(__name__)


@decorators.api_view(['POST'])
@decorators.permission_classes((permissions.IsAdminUser,))
@decorators.renderer_classes((JSONRenderer,))
def index_search(request):
    """
    Add things to the search index.
    """
    data = request.DATA['data']
    version_pk = data['version_pk']
    commit = data.get('commit')
    version = Version.objects.get(pk=version_pk)

    project_scale = 1
    page_scale = 1

    utils.index_search_request(
        version=version, page_list=data['page_list'], commit=commit,
        project_scale=project_scale, page_scale=page_scale)

    return Response({'indexed': True})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def search(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', LATEST)
    query = request.GET.get('q', None)
    if project_slug is None or query is None:
        return Response({'error': 'Need project and q'},
                        status=status.HTTP_400_BAD_REQUEST)
    log.debug("(API Search) %s" % query)
    results = search_file(request=request, project=project_slug,
                          version=version_slug, query=query)
    return Response({'results': results})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def project_search(request):
    query = request.GET.get('q', None)
    if query is None:
        return Response({'error': 'Need project and q'}, status=status.HTTP_400_BAD_REQUEST)
    log.debug("(API Project Search) %s" % (query))
    results = search_project(request=request, query=query)
    return Response({'results': results})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def section_search(request):
    """Section search

    Queries with query ``q`` across all documents and projects. Queries can be
    limited to a single project or version by using the ``project`` and
    ``version`` GET arguments in your request.

    When you search, you will have a ``project`` facet, which includes the
    number of matching sections per project. When you search inside a project,
    the ``path`` facet will show the number of matching sections per page.

    Possible GET args
    -----------------

    q **(required)**
        The query string **Required**

    project
        A project slug

    version
        A version slug

    path
        A file path slug


    Example::

        GET /api/v2/search/section/?q=virtualenv&project=django

    """
    query = request.GET.get('q', None)
    if not query:
        return Response(
            {'error': 'Search term required. Use the "q" GET arg to search. '},
            status=status.HTTP_400_BAD_REQUEST)
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', LATEST)
    path = request.GET.get('path', None)
    log.debug("(API Section Search) [%s:%s] %s" %
              (project_slug, version_slug, query))
    results = search_section(
        request=request,
        query=query,
        project_slug=project_slug,
        version_slug=version_slug,
        path=path,
    )
    return Response({'results': results})
