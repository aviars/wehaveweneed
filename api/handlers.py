import datetime
import time
import urlparse
from django.http import HttpResponse
from django.contrib.sites.models import Site
from haystack.query import SearchQuerySet, RelatedSearchQuerySet
from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, validate
from wehaveweneed.web.forms import PostForm
from wehaveweneed.web.models import Category, Post, User

class CategoryHandler(BaseHandler):
    """
    Provides listing of all categories.
    """
    allowed_methods = ('GET',)
    fields = ('name','slug')
    model = Category

class ContactHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('first_name', 'last_name', 'organization')
    model = User

    @classmethod
    def organization(cls, model):
        return model.get_profile().organization

class AnonymousPostHandler(AnonymousBaseHandler):
    model = Post
    allowed_methods = ('GET',)

class PostHandler(BaseHandler):
    """
    Handler for individual posts and listing of posts.
    """
    anonymous = AnonymousPostHandler
    allowed_methods = ('GET','POST')
    fields = ('id', 'type', 'title', 'location', 'priority',
              'contact', 'category', 'time_start', 'time_end',
              'created_at', 'content', 'link')
    model = Post

    @classmethod
    def link(cls, model):
        base = "http://" + Site.objects.get_current().domain
        return urlparse.urljoin(base, model.get_absolute_url())

    def read(self, request, post_id=None, post_type=None, category=None):
        if post_id:
            return Post.objects.get(pk=post_id)
        else:
            search = SearchQuerySet()
            if post_type:
                search = search.filter(type=post_type)
            if category:
                search = search.filter(category=category)
            q = request.GET.get('q', None)
            if q:
                search = search.filter(content=q)
            return [r.object for r in search.load_all()]

    @validate(PostForm) # validate against post form
    def create(self, request):
        # Doing another validation here to get the benefit of 'cleaned_data'
        form = PostForm(request.POST)
        form.is_valid()
        data = form.cleaned_data
        post = self.model(
            title=data['title'],
            type=data['type'],
            priority=data['priority'],
            location=data['location'],
            time_start=data.get('time_start', datetime.datetime.utcnow()),
            time_end=data.get('time_end', None),
            category=Category.objects.get(slug=data['category']),
            contact=request.user,
            content=data['content'],
        )
        post.save()
        response_msg = "%s" % post.pk
        # Manually create an HTTP response to set both the message body,
        # and the HTTP return code properly.
        return HttpResponse(response_msg, mimetype="text/plain", status=201)
