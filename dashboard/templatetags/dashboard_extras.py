import datetime
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from dashboard.helper.safe_json import safe_json_dumps
from dashboard.models import CustomUserModel, Helmet, HelmetNotification, Project, Site, WorkerRecord, WorkerSite
from dashboard.helper.util import (
    is_left_role_higher_or_equal as _is_left_role_higher_or_equal,
    str_b64 as _str_b64,
    b64_str as _b64_str,
)
import json


register = template.Library()

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

@register.filter
def get_url(name):
    """get url from name"""
    return reverse(name)

@register.filter
def to_string(value):
    return str(value)

@register.filter
def string_with_delimiter(array, delim):
    str = ""
    for item in array:
        str += item.__str__().title() + delim + " "
    # remove last delimiter
    return str[:-len(delim)-1]

@register.filter
def var_dump(obj):
    return vars(obj)

@register.filter
def to_int(value):
    try:
        return int(value)
    except:
        return None

@register.filter
def to_title(value):
    try:
        if type(value) is not str:
            return value
        else:
            return ' '.join([word.capitalize() if word.islower() else word for word in value.split(' ')])
    except:
        return None

def get_attr_by_string(obj, attr_str):
    try:
        attr_str_split = attr_str.split(".")
        for i in range(len(attr_str_split)):
            attr_str = attr_str_split[i].strip()
            if attr_str[-2:] == "()":
                attr_str = attr_str[:-2]
                obj = getattr(obj, attr_str)()
            else:
                obj = getattr(obj, attr_str_split[i])
        return obj
    except:
        return None

@register.filter
def select_group_by(array, group_by):
    try:
        unique = set([get_attr_by_string(item, group_by) for item in array])
        num_rows = len(unique)
        grouped_array = [[] for _ in range(num_rows)]
        for item in array:
            attr_value = get_attr_by_string(item, group_by)
            idx = 0
            for value in unique:
                if attr_value == value:
                    grouped_array[idx].append(item)
                    break
                idx += 1
        return grouped_array
    except Exception as e:
        print("ERROR", e)
        return [array]

def to_json(object):
    return safe_json_dumps(object)

@register.filter(is_safe=True)
def jsonify(json_object):
    """
    Output the json encoding of its argument.
    This will escape all the HTML/XML special characters with their unicode
    escapes, so it is safe to be output anywhere except for inside a tag
    attribute.
    If the output needs to be put in an attribute, entitize the output of this
    filter.
    """

    json_str = to_json(json_object)

    # Escape all the XML/HTML special characters.
    escapes = ["<", ">", "&"]
    for c in escapes:
        json_str = json_str.replace(c, r"\u%04x" % ord(c))

    # now it's safe to use mark_safe
    return mark_safe(json_str)

@register.filter
def nullify(value):
    if value:
        return value
    else:
        return "null"

@register.filter
def abs_v(value):
    try:
        return abs(int(value))
    except:
        return value

def construct_notification(notification_instance):
    return {
        'notification_type': notification_instance.type,
        'id': notification_instance.id,
        'message': notification_instance.message,
        'timestamp': notification_instance.timestamp.astimezone().strftime("%d-%m-%Y %H:%M:%S"),
        'helmet_identifier': notification_instance.helmet.identifier,
        'helmet_user_fullname': notification_instance.user.first_name + " " + notification_instance.user.last_name,
        'helmet_site_id': notification_instance.site.id,
        'helmet_site_name': notification_instance.site.name,
        'done': True if notification_instance.resolved_at else False,
    }
@register.simple_tag()
def get_helmet_notifications(is_done, **kwargs):
    ascending = kwargs.get('ascending', False)
    user_id = kwargs.get('user_id', None)
    site_id = kwargs.get('site_id', None)
    user = CustomUserModel.objects.get(id=user_id)
    site = Site.objects.get(id=site_id)
    if is_done is True:
        retval = HelmetNotification.objects.filter(resolved_at__isnull=False)
    elif is_done is False:
        retval = HelmetNotification.objects.filter(resolved_at__isnull=True)
    else:
        retval = HelmetNotification.objects.all()
        
    if user:
        if user.role == CustomUserModel.Roles.ADMIN or user.is_superuser:
            pass
        elif user.role == CustomUserModel.Roles.DIRECTOR:
            projects = Project.objects.filter(director=user)
            sites = Site.objects.filter(project__in=projects)
            retval = retval.filter(site__in=sites)
        elif user.role == CustomUserModel.Roles.PIC:
            sites = Site.objects.filter(pic=user)
            retval = retval.filter(site__in=sites)
        else:
            retval = retval.filter(user=user)
    
    if site is not None:
        retval = retval.filter(site=site)

    if retval.__len__() > 0:
        if ascending:
            retval = retval.order_by('timestamp')
        else:
            retval = retval.order_by('-timestamp')
    
    msg = []
    for notification in retval:
        msg.append(construct_notification(notification))
    return msg

@register.simple_tag()
def get_active_project_by_director(director):
    projects = list(Project.objects.filter(director=director, actual_end_date__isnull=True))
    if projects.__len__() <= 0:
        projects = None
        return projects
    # stringify
    retstr = ""
    for i in range(projects.__len__()):
        nstr = mark_safe(f"<a href='{reverse('projects_view', kwargs={'project_id':projects[i].id})}'>{projects[i]}</a>")
        retstr += nstr
        if i < projects.__len__() - 1:
            if i == projects.__len__() - 2:
                retstr += " and "
            else:
                retstr += ", "
    return retstr

@register.simple_tag()
def get_active_site_by_pic(pic):
    sites = list(Site.objects.filter(pic=pic))
    if sites.__len__() <= 0:
        sites = None
        return sites
    # stringify
    retstr = ""
    for i in range(sites.__len__()):
        retstr += mark_safe(f"<a href='{reverse('sites_view', kwargs={'site_id':sites[i].id})}'>{sites[i]}</a>")
        if i < sites.__len__() - 1:
            if i == sites.__len__() - 2:
                retstr += " and "
            else:
                retstr += ", "
    return retstr


@register.simple_tag()
def get_active_site_by_worker(worker):
    wrksite = WorkerSite.objects.filter_active(worker=worker)
    sites = []
    for ws in wrksite:
        sites.append(ws.site)
    if sites.__len__() <= 0:
        sites = None
        return sites
    # stringify
    retstr = ""
    for i in range(sites.__len__()):
        retstr += mark_safe(f"<a href='{reverse('sites_view', kwargs={'site_id':sites[i].id})}'>{sites[i]}</a>")
        if i < sites.__len__() - 1:
            if i == sites.__len__() - 2:
                retstr += " and "
            else:
                retstr += ", "
    return retstr

@register.simple_tag()
def get_first_active_site_id_by_worker(worker):
    wrksite = WorkerSite.objects.filter_active(worker=worker)
    if wrksite.__len__() <= 0:
        return None
    return wrksite[0].site.id

@register.simple_tag()
def get_last_record_by_worker(worker, **kwargs):
    temperature = kwargs.get('temperature', None)
    position = kwargs.get('position', None)
    if temperature and position:
        return WorkerRecord.objects.filter(user=worker, temperature__isnull=False, latitude__isnull=False, longitude__isnull=False).order_by('-timestamp').first()
    elif temperature:
        return WorkerRecord.objects.filter(user=worker, temperature__isnull=False).order_by('-timestamp').first()
    elif position:
        return WorkerRecord.objects.filter(user=worker, latitude__isnull=False, longitude__isnull=False).order_by('-timestamp').first()
    else:
        return WorkerRecord.objects.filter(user=worker).order_by('-timestamp').first()
    

@register.simple_tag()
def is_left_role_higher_than_or_equal(left, right):
    return _is_left_role_higher_or_equal(left, right)

@register.simple_tag()
def count_days(**kwargs):
    start_date = kwargs.get('start_date', "now")
    end_date = kwargs.get('end_date', "now")
    if end_date == "now":
        end_date = datetime.datetime.now().astimezone().date()
    if start_date == "now":
        start_date = datetime.datetime.now().astimezone().date()
    return (end_date - start_date).days

@register.simple_tag()
def ratio_percent(**kwargs):
    try:
        nominator = int(kwargs.get('nominator', 0))
        denominator = int(kwargs.get('denominator', 0))
        return int(nominator / denominator * 100)
    except:
        return 0

@register.filter
def str_b64(string):
    return _str_b64(string)

@register.filter
def b64_str(string):
    return _b64_str(string)

        