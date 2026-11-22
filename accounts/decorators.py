
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Administrators belong in the management dashboard.
        if (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == 'admin'
        ):
            return redirect('dashboard:index')

        # Only customer accounts can shop.
        if request.user.role != 'customer':
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return wrapper


def shopping_access_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Allow guests and customers, but block administrators.
        if request.user.is_authenticated:
            if (
                request.user.is_staff
                or request.user.is_superuser
                or request.user.role == 'admin'
            ):
                return redirect('dashboard:index')

        return view_func(request, *args, **kwargs)

    return wrapper
