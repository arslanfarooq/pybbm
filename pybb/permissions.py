# -*- coding: utf-8 -*-
"""
Extensible permission system for pybbm
"""
from django.utils.importlib import import_module
from django.db.models import Q

from pybb import models, defaults
from pybb.templatetags.pybb_tags import pybb_topic_moderated_by, pybb_editable_by
from django.http import Http404

def _resolve_class(name):
    """ resolves a class function given as string, returning the function """
    if not name: return False
    modname, funcname = name.rsplit('.', 1)
    return getattr(import_module(modname), funcname)() 

def filter_hidden(user, qs):
    """
    Return queryset for model, manager or queryset, filtering hidden objects for non staff users.
    """
    if user.is_staff:
        return qs
    return qs.filter(hidden=False)

class DefaultPermissionHandler(object):
    """ Default Permission handler """
    #
    # permission checks on categories
    #
    def filter_categories(self, user, qs):
        """ return a queryset with categories `user` is allowed to see """
        return filter_hidden(user, qs)
    
    # 
    # permission checks on forums
    # 
    def filter_forums(self, user, qs):
        """ return a queryset with forums `user` is allowed to see """
        return filter_hidden(user, qs)
    
    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        return user.has_perm('pybb.add_post')
    
    #
    # permission checks on topics
    # 
    def filter_topics(self, user, qs):
        """ return a queryset with topics `user` is allowed to see """
        return qs 
    
    def may_view_topic(self, user, topic):
        """ return True if `user` may view `topic` """
        # check whether topic is on moderation
        if topic.on_moderation and \
           not pybb_topic_moderated_by(topic, user) and\
           not user == topic.user:
            return False  
        # check whether this topic's forum or category is hidden
        if (topic.forum.hidden or self.topic.forum.category.hidden) and (not user.is_staff):
            raise Http404
        
        return True
    
    def may_close_topic(self, user, topic):
        """ return True if `user` may close `topic` """
        return pybb_topic_moderated_by(topic, user)
    
    def may_open_topic(self, user, topic):
        """ return True if `user` may open `topic` """
        return pybb_topic_moderated_by(topic, user)
    
    def may_stick_topic(self, user, topic):
        """ return True if `user` may stick `topic` """
        return pybb_topic_moderated_by(topic, user)
    
    def may_unstick_topic(self, user, topic):
        """ return True if `user` may unstick `topic` """
        return pybb_topic_moderated_by(topic, user)
    
    def may_create_post(self, user, topic):
        """ return True if `user` is allowed to create a new post in `topic` """
        # if topic is hidden, only staff may post
        if topic.forum.hidden and (not user.is_staff):
            raise Http404
        # if topic is closed, only staff may post
        if topic.closed and (not user.is_staff):
            return False
        # only user which have 'pybb.add_post' permission may post
        return user.has_perm('pybb.add_post')
    
    def may_post_as_admin(self, user, topic):
        """ return True if `user` may post as admin in `topic` """
        return user.is_staff
    
    #
    # permission checks on posts
    #    
    def filter_posts(self, user, qs):
        """ return a queryset with posts `user` is allowed to see """
        if self.request.user.is_authenticated():
            # authenticated users may see their own posts, even if they on moderation
            qs = qs.filter(Q(user=user)|Q(on_moderation=False))
        else:
            # anonymous user may not see posts which are on moderation
            qs = qs.filter(on_moderation=False)
        return qs
            
    def may_edit_post(self, user, post):
        """ return True if `user` may edit `post` """
        return pybb_editable_by(post, user)        
    
    def may_delete_post(self, user, post):
        """ return True if `user` may delete `post` """
        return False
    
    #
    # permission checks on users
    #
    def may_blog_user(self, user, user_to_block):
        """ return True if `user` may block `user_to_block` """
        return user.has_permission('pybb.block_users')
    
perms = _resolve_class(defaults.PYBB_PERMISSION_HANDLER)