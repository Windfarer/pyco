#coding=utf-8
from __future__ import absolute_import
from flask import request
import math

def before_render(var,template):
    var["saltshaker"] = salt_shaker
    var["stapler"] = stapler
    var["glue"] = glue
    return

#custom functions
def salt_shaker(obj, conditions, intersection = False):
    results = None
    if not isinstance(conditions, list) or len(conditions)>10:
        return "Excessive"
    if isinstance(obj, list):
        results = []
    elif isinstance(obj, dict):
        results = {}
    
    first=True
    for cond in conditions:
        cond = cond.lower()
        if isinstance(obj, list):
            if intersection and not first:
                results = [i for i in results if i.get(cond)]
            else:
                for i in obj:
                    if i.get(cond) and i not in results:
                        results.append(i);

        elif isinstance(obj, dict):
            if intersection and not first:
                results.update({k:v for (k, v) in results.iteritems() if k == cond and v})
            else:
                results.update({k:v for (k, v) in obj.iteritems() if k == cond and v})
                
        if first:
            first = False

    return results


def glue(args = None):
    argments = {k:v for k,v in request.args.items()}
    if isinstance(args, dict):
        argments.update(args)
    url=request.path+"?"+"&".join(['%s=%s' % (key, value) for (key, value) in argments.items()]) 
    return url


def stapler(raw_posts, paged=1, perpage=12, post_type=None):
    macthed_posts = [post for post in raw_posts if not post_type or post.get("type") in post_type]
    max_pages = int(math.ceil(len(macthed_posts)/perpage))
    if paged > max_pages:
        paged = max_pages
    start = (paged-1)*perpage
    end = paged*perpage
    result_posts = macthed_posts[start:end]
    
    return {"posts":result_posts,"max":max_pages,"paged":paged}