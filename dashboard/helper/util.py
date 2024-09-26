import base64
from types import SimpleNamespace
from typing import List
from dashboard.models import CustomUserModel, Helmet


def is_left_role_higher_or_equal(left: CustomUserModel.Roles, right: CustomUserModel.Roles) -> bool:
    """Check if left role is higher than right role"""
    if left == CustomUserModel.Roles.ADMIN:
        return True
    elif left == CustomUserModel.Roles.DIRECTOR:
        if right == CustomUserModel.Roles.ADMIN:
            return False
        else:
            return True
    elif left == CustomUserModel.Roles.PIC:
        if right == CustomUserModel.Roles.ADMIN or right == CustomUserModel.Roles.DIRECTOR:
            return False
        else:
            return True
    elif left == CustomUserModel.Roles.WORKER:
        if right == CustomUserModel.Roles.ADMIN or right == CustomUserModel.Roles.DIRECTOR or right == CustomUserModel.Roles.PIC:
            return False
        else:
            return True
    else:
        return False

def construct_worker_info(workers: List[CustomUserModel]) -> List[SimpleNamespace]:
    """Construct worker info for display in site detail"""
    worker_infos = []
    if workers is None:
        return worker_infos
    helmets = Helmet.objects.all()
    for worker in workers:
        if not worker:
            continue
        workerinfo = SimpleNamespace()
        workerinfo.id = worker.id
        workerinfo.first_name = worker.first_name
        workerinfo.last_name = worker.last_name
        workerinfo.email = worker.email
        workerinfo.helmet = helmets.filter(user=worker).first()
        workerinfo.site = worker.workersite_set.filter(site__actual_end_date__isnull=True).first().site if worker.workersite_set.filter(site__actual_end_date__isnull=True).first() else None
        workerinfo.department = worker.department
        workerinfo.date_joined = worker.date_joined.astimezone()
        workerinfo.phone = worker.phone
        worker_infos.append(workerinfo)
    return worker_infos

def str_b64(string: str) -> str:
    """Convert string to base64"""
    if not string:
        return None
    return base64.b64encode(string.encode("ascii")).decode("ascii")

def b64_str(string: str) -> str:
    """Convert base64 to string"""
    if not string:
        return None
    return base64.b64decode(string.encode("ascii")).decode("ascii")
        