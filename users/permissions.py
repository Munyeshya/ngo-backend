from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsStaffUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "staff"
        )


class IsDonorUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "donor"
        )


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        return obj.id == request.user.id


class IsAdminOrStaffProjectOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True

        if request.user.role == "staff":
            return obj.created_by_id == request.user.id

        return False


class IsAdminOrStaffBeneficiaryProjectOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True

        if request.user.role == "staff":
            return obj.project.created_by_id == request.user.id

        return False

class IsAdminOrStaffBeneficiaryImageProjectOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True

        if request.user.role == "staff":
            return obj.beneficiary.project.created_by_id == request.user.id

        return False
class IsAdminOrStaffProjectUpdateOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True

        if request.user.role == "staff":
            return obj.project.created_by_id == request.user.id

        return False


class IsAdminOrStaffProjectUpdateImageOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True

        if request.user.role == "staff":
            return obj.project_update.project.created_by_id == request.user.id

        return False